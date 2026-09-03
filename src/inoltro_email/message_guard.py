"""Registro locale dei messaggi che il flusso ha gia' gestito.

Il controllo duplicati usa solo dati semantici del messaggio. ID Outlook/Graph,
versioni dell'oggetto e metadati degli allegati cambiano durante il flusso.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .inbound import html_to_text
from .models import InboundEmail

FINGERPRINT_VERSION = "2"


class LocalMessageStore:
    """Registro SQLite persistente e sicuro anche con piu' worker."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            _ensure_schema(connection)

    def register(self, email: InboundEmail, payload: Mapping[str, Any]) -> bool:
        """Registra il messaggio; ``False`` se contenuto semantico gia' visto."""
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO checked_messages
                    (fingerprint, message_key, received_at, checked_at, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message_fingerprint(payload),
                    email.key,
                    email.received_at,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    serialized,
                ),
            )
        return cursor.rowcount == 1

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10)


def message_fingerprint(payload: Mapping[str, Any]) -> str:
    """Firma stabile: ignora campi tecnici e conserva il contenuto della mail."""
    identity = _message_identity(payload)
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _message_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Riduce ogni forma del payload Outlook ai soli dati utili ai doppioni."""
    body = _body_text(_value(payload, "body", "bodyHtml", "bodyContent", "bodyPreview"))
    attachments = _attachment_identity(_value(payload, "attachments"))
    identity = {
        "sender": _sender_identity(_value(payload, "from", "sender")),
        "received": _normalize(_value(payload, "receivedDateTime", "received", "date")),
        "subject": _normalize(_value(payload, "subject")),
        "attachments": attachments,
    }
    # Con allegati, corpo HTML e firme possono cambiare pur essendo la stessa
    # mail. L'impronta dei file e' piu' affidabile; senza file resta il corpo.
    if not attachments:
        identity["body"] = body
    return identity


def _value(payload: Mapping[str, Any], *names: str) -> Any:
    wanted = {name.casefold() for name in names}
    for key, value in payload.items():
        if str(key).casefold() in wanted:
            return value
    return ""


def _sender_identity(value: Any) -> str:
    if isinstance(value, Mapping):
        nested = _value(value, "emailAddress", "address")
        if isinstance(nested, Mapping):
            nested = _value(nested, "address")
        return _normalize(nested)
    return _normalize(value)


def _body_text(value: Any) -> str:
    if isinstance(value, Mapping):
        value = _value(value, "content", "value")
    return _normalize(html_to_text(str(value or "")))


def _attachment_identity(raw: Any) -> list[dict[str, str]]:
    if isinstance(raw, Mapping):
        raw = [raw]
    if not isinstance(raw, list):
        return []

    signatures: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        entry = _value(item, "properties")
        if not isinstance(entry, Mapping):
            entry = item
        content = _value(entry, "contentBytes", "content", "contentBase64", "$content")
        if not str(content or "").strip():
            # Senza byte non distingue due file diversi: si ricade sul corpo.
            continue
        signatures.append({
            "name": _normalize(_value(entry, "name", "fileName")),
            "content": _binary_hash(content),
        })
    return sorted(signatures, key=lambda item: (item["name"], item["content"]))


def _binary_hash(value: Any) -> str:
    # Base64 puo' contenere a capo diversi; il file sottostante resta identico.
    text = "".join(str(value or "").split())
    return hashlib.sha256(text.encode("ascii", "replace")).hexdigest()


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _ensure_schema(connection: sqlite3.Connection) -> None:
    """Crea/migra schema e ricalcola impronte quando cambia l'algoritmo."""
    columns = {row[1]: row[5] for row in connection.execute("PRAGMA table_info(checked_messages)")}
    if not columns:
        _create_current_table(connection)
    elif columns.get("fingerprint") != 1:
        _rebuild_table(connection, "checked_messages_v3")

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS message_store_meta (
            name TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    row = connection.execute(
        "SELECT value FROM message_store_meta WHERE name = 'fingerprint_version'"
    ).fetchone()
    if row is None or row[0] != FINGERPRINT_VERSION:
        _rebuild_table(connection, "checked_messages_v4")
        connection.execute(
            "INSERT OR REPLACE INTO message_store_meta (name, value) VALUES ('fingerprint_version', ?)",
            (FINGERPRINT_VERSION,),
        )


def _create_current_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE checked_messages (
            fingerprint TEXT PRIMARY KEY,
            message_key TEXT NOT NULL,
            received_at TEXT NOT NULL,
            checked_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )


def _rebuild_table(connection: sqlite3.Connection, temporary_name: str) -> None:
    """Conserva ultima registrazione per ogni nuova firma di contenuto."""
    connection.execute(
        f"""
        CREATE TABLE {temporary_name} (
            fingerprint TEXT PRIMARY KEY,
            message_key TEXT NOT NULL,
            received_at TEXT NOT NULL,
            checked_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    rows: Iterable[tuple[str, str, str, str]] = connection.execute(
        """
        SELECT message_key, received_at, checked_at, payload_json
        FROM checked_messages
        ORDER BY checked_at DESC, rowid DESC
        """
    )
    for message_key, received_at, checked_at, payload_json in rows:
        connection.execute(
            f"""
            INSERT OR IGNORE INTO {temporary_name}
                (fingerprint, message_key, received_at, checked_at, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (_stored_fingerprint(payload_json), message_key, received_at, checked_at, payload_json),
        )
    connection.execute("DROP TABLE checked_messages")
    connection.execute(f"ALTER TABLE {temporary_name} RENAME TO checked_messages")


def _stored_fingerprint(payload_json: str) -> str:
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, Mapping):
        return message_fingerprint(payload)
    return "legacy:" + hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
