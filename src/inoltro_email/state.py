"""Registro dei messaggi gia' elaborati (SQLite).

Serve a non inoltrare due volte la stessa email: l'evento ``NewMailEx`` e la
scansione di recupero all'avvio possono benissimo vedere lo stesso messaggio.
L'inserimento con ``INSERT OR IGNORE`` funziona da lock: se non inserisce
nulla, qualcuno l'ha gia' preso in carico.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import Decision

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS processed (
    message_key   TEXT PRIMARY KEY,
    entry_id      TEXT,
    subject       TEXT,
    decision      TEXT,
    matched_terms TEXT,
    processed_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_processed_at ON processed (processed_at);
"""


class ProcessedStore:
    """Accesso al registro dei messaggi elaborati."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), timeout=10, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "ProcessedStore":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def claim(self, message_key: str, entry_id: str = "", subject: str = "") -> bool:
        """Prenota un messaggio.

        Restituisce True se la prenotazione e' andata a buon fine (messaggio mai
        visto prima), False se era gia' stato elaborato.
        """
        cursor = self._conn.execute(
            "INSERT OR IGNORE INTO processed "
            "(message_key, entry_id, subject, decision, matched_terms, processed_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (message_key, entry_id, subject, "in_corso", "", _now()),
        )
        claimed = cursor.rowcount > 0
        if not claimed:
            logger.debug("Messaggio gia' elaborato in precedenza: %s", message_key)
        return claimed

    def finalize(self, message_key: str, decision: Decision, matched_terms: str = "") -> None:
        """Registra l'esito definitivo di un messaggio prenotato."""
        self._conn.execute(
            "UPDATE processed SET decision = ?, matched_terms = ?, processed_at = ? "
            "WHERE message_key = ?",
            (decision.value, matched_terms, _now(), message_key),
        )

    def release(self, message_key: str) -> None:
        """Annulla una prenotazione, cosi' il messaggio potra' essere ritentato.

        Usato quando l'elaborazione si interrompe per una causa transitoria
        (ocr.space irraggiungibile, Outlook che nega l'accesso all'allegato).
        """
        self._conn.execute("DELETE FROM processed WHERE message_key = ?", (message_key,))

    def get_decision(self, message_key: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT decision FROM processed WHERE message_key = ?", (message_key,)
        ).fetchone()
        return row[0] if row else None

    def count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM processed").fetchone()[0])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
