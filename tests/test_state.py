"""Test del registro anti-duplicato."""

from __future__ import annotations

from pathlib import Path

from inoltro_email.models import Decision
from inoltro_email.state import ProcessedStore


def test_la_prima_prenotazione_riesce_la_seconda_no(tmp_path: Path) -> None:
    with ProcessedStore(tmp_path / "state.sqlite3") as store:
        assert store.claim("<msg-1@example.com>", "E1", "Oggetto") is True
        assert store.claim("<msg-1@example.com>", "E1", "Oggetto") is False


def test_esito_registrato_e_rileggibile(tmp_path: Path) -> None:
    with ProcessedStore(tmp_path / "state.sqlite3") as store:
        store.claim("<msg-1@example.com>")
        store.finalize("<msg-1@example.com>", Decision.FORWARDED, "televisita, 1501A")
        assert store.get_decision("<msg-1@example.com>") == "forwarded"


def test_release_consente_un_nuovo_tentativo(tmp_path: Path) -> None:
    """Dopo un errore transitorio il messaggio deve poter essere ritentato."""
    with ProcessedStore(tmp_path / "state.sqlite3") as store:
        store.claim("<msg-1@example.com>")
        store.release("<msg-1@example.com>")
        assert store.claim("<msg-1@example.com>") is True


def test_lo_stato_sopravvive_alla_riapertura(tmp_path: Path) -> None:
    db = tmp_path / "state.sqlite3"
    with ProcessedStore(db) as store:
        store.claim("<msg-1@example.com>")
        store.finalize("<msg-1@example.com>", Decision.NO_MATCH)
    with ProcessedStore(db) as store:
        assert store.claim("<msg-1@example.com>") is False
        assert store.count() == 1


def test_crea_la_cartella_mancante(tmp_path: Path) -> None:
    with ProcessedStore(tmp_path / "nuova" / "sotto" / "state.sqlite3") as store:
        assert store.count() == 0


def test_messaggi_diversi_sono_indipendenti(tmp_path: Path) -> None:
    with ProcessedStore(tmp_path / "state.sqlite3") as store:
        assert store.claim("<a@example.com>") is True
        assert store.claim("<b@example.com>") is True
        assert store.count() == 2
