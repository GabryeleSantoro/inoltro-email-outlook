"""Test del registro SQLite dei messaggi gestiti."""

from __future__ import annotations

import sqlite3

from inoltro_email.message_guard import LocalMessageStore


def test_migra_il_vecchio_registro_a_message_key_primary_key(tmp_path) -> None:
    database = tmp_path / "checked.sqlite3"
    with sqlite3.connect(database) as connection:
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
        connection.executemany(
            "INSERT INTO checked_messages VALUES (?, ?, ?, ?, ?)",
            [
                ("old", "AAMkAD-old", "2026-09-01", "2026-09-01T08:00:00+00:00", "old"),
                ("new", "AAMkAD-old", "2026-09-01", "2026-09-01T09:00:00+00:00", "new"),
                ("other", "AAMkAD-other", "2026-09-01", "2026-09-01T08:00:00+00:00", "other"),
            ],
        )

    LocalMessageStore(database)

    with sqlite3.connect(database) as connection:
        primary_keys = [
            row[1] for row in connection.execute("PRAGMA table_info(checked_messages)")
            if row[5] == 1
        ]
        rows = connection.execute(
            "SELECT message_key, payload_json FROM checked_messages ORDER BY message_key"
        ).fetchall()

    assert primary_keys == ["message_key"]
    assert rows == [("AAMkAD-old", "new"), ("AAMkAD-other", "other")]
