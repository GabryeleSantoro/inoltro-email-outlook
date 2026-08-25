"""Controlli locali, economici, prima dell'analisi di una email.

Il database resta sul computer che esegue il servizio.  Conserva il payload
originale dei messaggi effettivamente ammessi all'analisi, cosi' lo stesso
messaggio non puo' consumare di nuovo quota OCR dopo un retry del flow.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from .models import InboundEmail


class MessageDateError(ValueError):
    """Il campo ``date``/``receivedDateTime`` non e' utilizzabile."""


class LocalMessageStore:
    """Registro SQLite persistente e sicuro anche con piu' worker."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS checked_messages (
                    fingerprint TEXT PRIMARY KEY,
                    message_key TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    checked_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def is_fresh(self, received_at: str, *, window_seconds: int,
                 now: Optional[datetime] = None) -> tuple[bool, float]:
        """Restituisce se la data e' nella finestra e la sua eta' in secondi."""
        sent_at = parse_message_date(received_at)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        age_seconds = (current.astimezone(timezone.utc) - sent_at).total_seconds()
        return age_seconds <= window_seconds, age_seconds

    def claim(self, email: InboundEmail, payload: Mapping[str, Any]) -> bool:
        """Salva il messaggio e lo riserva all'analisi.

        L'inserimento atomico e' anche il controllo duplicati: solo la prima
        richiesta con la stessa impronta puo' arrivare all'OCR.
        """
        fingerprint = message_fingerprint(email)
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO checked_messages
                    (fingerprint, message_key, received_at, checked_at, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    fingerprint,
                    email.key,
                    email.received_at,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    serialized,
                ),
            )
        return cursor.rowcount == 1

    def release(self, email: InboundEmail) -> None:
        """Rimuove la prenotazione se un errore inatteso blocca l'analisi."""
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM checked_messages WHERE fingerprint = ?",
                (message_fingerprint(email),),
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10)


def parse_message_date(value: str) -> datetime:
    """Legge ISO 8601 e i formati data del flow Power Automate.

    Le date senza fuso sono interpretate nel fuso locale del server. Il flow
    attuale usa mese/giorno/anno (es. ``08/20/2026 10:26``).
    """
    raw = value.strip()
    if not raw:
        raise MessageDateError("Manca la data del messaggio (campo 'date').")

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
        for pattern in (
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
        ):
            try:
                parsed = datetime.strptime(raw, pattern)
                break
            except ValueError:
                continue
        if parsed is None:
            raise MessageDateError(
                "Data del messaggio non valida: usare ISO 8601 oppure MM/GG/AAAA HH:MM."
            ) from None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return parsed.astimezone(timezone.utc)


def message_fingerprint(email: InboundEmail) -> str:
    """Usa l'ID Outlook; senza ID crea una firma stabile del messaggio."""
    identifier = (email.internet_message_id or email.message_id).strip()
    if identifier:
        return "id:" + identifier

    content = {
        "sender": email.sender,
        "received_at": email.received_at,
        "subject": email.subject,
        "body": email.body_text,
        "attachments": [
            {
                "name": item.name,
                "size": item.size_bytes,
                "content": hashlib.sha256(item.content).hexdigest() if item.content else "",
                "path": str(item.source_path or ""),
            }
            for item in email.attachments
        ],
    }
    encoded = json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "hash:" + hashlib.sha256(encoded).hexdigest()
