"""Registro locale dei messaggi che il flusso ha gia' gestito.

Il database resta sul computer che esegue il servizio. Conserva il payload
originale ricevuto dall'endpoint di registrazione, senza avviare una nuova
analisi o OCR.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .models import InboundEmail


class LocalMessageStore:
    """Registro SQLite persistente e sicuro anche con piu' worker."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            _ensure_schema(connection)

    def register(self, email: InboundEmail, payload: Mapping[str, Any]) -> bool:
        """Registra il messaggio; ``False`` se il ``message_key`` esiste gia'."""
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO checked_messages
                    (message_key, received_at, checked_at, payload_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    email.key,
                    email.received_at,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    serialized,
                ),
            )
        return cursor.rowcount == 1

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10)


def _ensure_schema(connection: sqlite3.Connection) -> None:
    """Crea o migra il registro: ``message_key`` e' la chiave primaria."""
    columns = {
        row[1]: row[5]
        for row in connection.execute("PRAGMA table_info(checked_messages)")
    }
    if not columns:
        _create_current_table(connection)
    elif columns.get("message_key") != 1:
        _migrate_to_message_key_primary_key(connection)


def _create_current_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE checked_messages (
            message_key TEXT PRIMARY KEY,
            received_at TEXT NOT NULL,
            checked_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )


def _migrate_to_message_key_primary_key(connection: sqlite3.Connection) -> None:
    """Migra il vecchio schema, mantenendo l'ultima registrazione per chiave."""
    connection.execute(
        """
        CREATE TABLE checked_messages_v2 (
            message_key TEXT PRIMARY KEY,
            received_at TEXT NOT NULL,
            checked_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO checked_messages_v2
            (message_key, received_at, checked_at, payload_json)
        SELECT message_key, received_at, checked_at, payload_json
        FROM checked_messages
        ORDER BY checked_at DESC, rowid DESC
        """
    )
    connection.execute("DROP TABLE checked_messages")
    connection.execute("ALTER TABLE checked_messages_v2 RENAME TO checked_messages")
