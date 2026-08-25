"""Test del log di sessione: un file nuovo a ogni avvio, con data e ora."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from inoltro_email.logging_setup import prune_session_logs, session_log_path, setup_logging


@pytest.fixture(autouse=True)
def _ripristina_logger():
    """Gli handler installati dai test non devono restare al logger radice."""
    yield
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()


def test_nome_con_data_e_ora(tmp_path: Path) -> None:
    path = session_log_path(tmp_path / "servizio.log", datetime(2025, 5, 21, 9, 15, 0))
    assert path == tmp_path / "servizio-20250521-091500.log"


def test_nome_progressivo_se_il_file_esiste(tmp_path: Path) -> None:
    """Due sessioni nello stesso secondo non condividono il file."""
    momento = datetime(2025, 5, 21, 9, 15, 0)
    (tmp_path / "servizio-20250521-091500.log").write_text("", encoding="utf-8")

    assert session_log_path(tmp_path / "servizio.log", momento).name == "servizio-20250521-091500-1.log"


def test_ogni_sessione_scrive_sul_proprio_file(tmp_path: Path) -> None:
    base = tmp_path / "logs" / "servizio.log"

    primo = setup_logging("INFO", base, started_at=datetime(2025, 5, 21, 9, 15, 0))
    logging.getLogger("prova").info("prima sessione")
    secondo = setup_logging("INFO", base, started_at=datetime(2025, 5, 21, 10, 30, 0))
    logging.getLogger("prova").info("seconda sessione")

    assert primo == tmp_path / "logs" / "servizio-20250521-091500.log"
    assert secondo == tmp_path / "logs" / "servizio-20250521-103000.log"
    assert "prima sessione" in primo.read_text(encoding="utf-8")
    assert "seconda sessione" not in primo.read_text(encoding="utf-8")
    assert "seconda sessione" in secondo.read_text(encoding="utf-8")
    assert not base.exists()  # il file indicato in configurazione e' solo un modello


def test_per_session_disattivato_usa_un_unico_file(tmp_path: Path) -> None:
    base = tmp_path / "servizio.log"

    assert setup_logging("INFO", base, per_session=False) == base
    logging.getLogger("prova").info("riga")
    assert "riga" in base.read_text(encoding="utf-8")


def test_senza_file_solo_console(tmp_path: Path) -> None:
    assert setup_logging("INFO", None) is None
    assert not any(isinstance(h, logging.FileHandler) for h in logging.getLogger().handlers)


def test_pulizia_conserva_i_piu_recenti(tmp_path: Path) -> None:
    base = tmp_path / "servizio.log"
    for ora in range(5):
        (tmp_path / f"servizio-20250521-0{ora}0000.log").write_text("", encoding="utf-8")

    rimossi = prune_session_logs(base, keep=2)

    assert [p.name for p in rimossi] == [
        "servizio-20250521-000000.log",
        "servizio-20250521-010000.log",
        "servizio-20250521-020000.log",
    ]
    assert sorted(p.name for p in tmp_path.glob("*.log")) == [
        "servizio-20250521-030000.log",
        "servizio-20250521-040000.log",
    ]


def test_pulizia_non_tocca_altri_file(tmp_path: Path) -> None:
    """Solo i file col nostro schema di data/ora vengono cancellati."""
    base = tmp_path / "servizio.log"
    base.write_text("", encoding="utf-8")
    (tmp_path / "servizio-vecchio.log").write_text("", encoding="utf-8")
    (tmp_path / "servizio-20250521-000000.log").write_text("", encoding="utf-8")

    prune_session_logs(base, keep=0)  # 0 = nessuna cancellazione
    assert len(list(tmp_path.glob("*.log"))) == 3

    prune_session_logs(base, keep=1)
    assert sorted(p.name for p in tmp_path.glob("*.log")) == [
        "servizio-20250521-000000.log",
        "servizio-vecchio.log",
        "servizio.log",
    ]


def test_setup_logging_pulisce_i_vecchi(tmp_path: Path) -> None:
    """Il file della sessione in corso rientra sempre fra quelli conservati."""
    base = tmp_path / "servizio.log"
    (tmp_path / "servizio-20250101-000000.log").write_text("", encoding="utf-8")
    (tmp_path / "servizio-20250102-000000.log").write_text("", encoding="utf-8")

    corrente = setup_logging("INFO", base, keep_sessions=2, started_at=datetime(2025, 5, 21, 9, 15))

    assert corrente is not None and corrente.exists()
    assert sorted(p.name for p in tmp_path.glob("*.log")) == [
        "servizio-20250102-000000.log",
        "servizio-20250521-091500.log",
    ]


def test_worker_reload_riusa_il_file_della_sessione(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Il processo figlio di Uvicorn non deve creare un log distinto."""
    from inoltro_email.api import server

    visto = {}
    session_file = tmp_path / "servizio-20250521-091500.log"
    monkeypatch.setenv("INOLTRO_EMAIL_SESSION_LOG_FILE", str(session_file))
    monkeypatch.setenv("INOLTRO_EMAIL_SESSION_LOG_LEVEL", "warning")
    monkeypatch.setattr(
        server,
        "setup_logging",
        lambda level, path, *, per_session: visto.update(
            level=level, path=path, per_session=per_session
        ),
    )

    server._configure_reload_worker_logging()

    assert visto == {"level": "warning", "path": session_file, "per_session": False}


def test_reload_passa_il_log_di_sessione_al_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """La configurazione Uvicorn non deve sostituire l'handler del file."""
    from inoltro_email.api import server
    from inoltro_email.config import Settings

    chiamate = []
    finto_uvicorn = SimpleNamespace(
        run=lambda *args, **kwargs: chiamate.append((args, kwargs))
    )
    monkeypatch.setitem(sys.modules, "uvicorn", finto_uvicorn)
    session_file = tmp_path / "servizio-20250521-091500.log"

    server.run(
        Settings(),
        reload=True,
        session_log_file=session_file,
        log_level="WARNING",
    )

    assert chiamate == [
        (
            ("inoltro_email.api.server:build",),
            {
                "factory": True,
                "host": "0.0.0.0",
                "port": 8000,
                "reload": True,
                "log_config": None,
            },
        )
    ]
    assert os.environ["INOLTRO_EMAIL_SESSION_LOG_FILE"] == str(session_file.resolve())
    assert os.environ["INOLTRO_EMAIL_SESSION_LOG_LEVEL"] == "WARNING"
