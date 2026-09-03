"""Test del registro SQLite dei messaggi gestiti."""

from __future__ import annotations

import sqlite3

from inoltro_email.message_guard import LocalMessageStore, message_fingerprint
from inoltro_email.models import InboundEmail


def test_impronta_ignora_gli_id_outlook_instabili() -> None:
    first = {
        "id": "AAMk-prima", "internetMessageId": "<prima@example.com>",
        "changeKey": "versione-prima", "subject": "Televisita",
        "body": "Richiesta appuntamento",
        "attachments": [{
            "id": "att-primo", "name": "ricetta.pdf", "contentBytes": "QUJD",
            "lastModifiedDateTime": "2026-09-03T08:00:00Z", "@odata.type": "#fileAttachment",
        }],
    }
    second = {
        "id": "AAMk-dopo", "internetMessageId": "<dopo@example.com>",
        "changeKey": "versione-dopo", "subject": "Televisita",
        "body": "Corpo riscritto da Outlook dopo la categoria",
        "attachments": [{
            "id": "att-dopo", "name": "ricetta.pdf", "contentBytes": "QUJD",
            "lastModifiedDateTime": "2026-09-03T10:00:00Z", "@odata.type": "#fileAttachment",
        }],
    }

    assert message_fingerprint(first) == message_fingerprint(second)


def test_registro_blocca_contenuto_uguale_con_id_diversi(tmp_path) -> None:
    store = LocalMessageStore(tmp_path / "checked.sqlite3")
    first = {"id": "AAMk-prima", "subject": "Televisita", "body": "Richiesta"}
    second = {"id": "AAMk-dopo", "subject": "Televisita", "body": "Richiesta"}

    assert store.register(InboundEmail(message_id="AAMk-prima"), first) is True
    assert store.contains(second) is True
    assert store.register(InboundEmail(message_id="AAMk-dopo"), second) is False


def test_migra_message_key_primary_key_a_fingerprint_del_contenuto(tmp_path) -> None:
    database = tmp_path / "checked.sqlite3"
    with sqlite3.connect(database) as connection:
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
        connection.executemany(
            "INSERT INTO checked_messages VALUES (?, ?, ?, ?)",
            [
                ("AAMkAD-old", "2026-09-01", "2026-09-01T08:00:00+00:00", '{"id":"old","subject":"stesso"}'),
                ("AAMkAD-other", "2026-09-01", "2026-09-01T09:00:00+00:00", '{"id":"new","subject":"stesso"}'),
            ],
        )

    LocalMessageStore(database)

    with sqlite3.connect(database) as connection:
        primary_keys = [
            row[1] for row in connection.execute("PRAGMA table_info(checked_messages)")
            if row[5] == 1
        ]
        rows = connection.execute(
            "SELECT message_key, payload_json FROM checked_messages"
        ).fetchall()

    assert primary_keys == ["fingerprint"]
    assert rows == [("AAMkAD-other", '{"id":"new","subject":"stesso"}')]
