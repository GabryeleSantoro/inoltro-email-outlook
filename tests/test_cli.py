"""Test della riga di comando, in particolare del comando `check-file`.

`check-file` e' l'unico comando che non tocca la casella: e' il modo previsto
per verificare chiave API e criteri senza collegarsi a Microsoft 365.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import responses
from conftest import make_pdf

from inoltro_email.__main__ import main

ENDPOINT = "https://api.ocr.space/parse/image"

CONFIG = """
ocr:
  endpoint: "https://api.ocr.space/parse/image"
  engine: 2
rules:
  keywords: ["televisita"]
  codes: ["1501A"]
  mode: all
forward:
  to: ["destinatario@example.com"]
  dry_run: true
outlook:
  token_path: "{token}"
storage:
  db_path: "{db}"
logging:
  level: "WARNING"
  file: null
"""


@pytest.fixture
def config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave-di-prova")
    path = tmp_path / "config.yaml"
    path.write_text(
        CONFIG.format(
            db=(tmp_path / "state.sqlite3").as_posix(),
            token=(tmp_path / "o365_token.txt").as_posix(),
        ),
        encoding="utf-8",
    )
    return path


def test_check_file_su_pdf_conforme(config_file: Path, tmp_path: Path, capsys) -> None:
    """PDF con livello di testo: nessuna chiamata di rete, esito 0."""
    pdf = tmp_path / "referto.pdf"
    pdf.write_bytes(make_pdf(["Richiesta TELEVISITA prestazione 1501A paziente Rossi"]))

    code = main(["--config", str(config_file), "check-file", str(pdf)])

    assert code == 0
    assert "CONFORME" in capsys.readouterr().out


def test_check_file_su_pdf_non_conforme(config_file: Path, tmp_path: Path, capsys) -> None:
    pdf = tmp_path / "altro.pdf"
    pdf.write_bytes(make_pdf(["Referto di visita ambulatoriale ordinaria, nessun codice"]))

    code = main(["--config", str(config_file), "check-file", str(pdf)])

    assert code == 1
    assert "non conforme" in capsys.readouterr().out


@responses.activate
def test_check_file_su_immagine_usa_ocr(config_file: Path, tmp_path: Path, capsys) -> None:
    responses.add(responses.POST, ENDPOINT, status=200, json={
        "ParsedResults": [{"ParsedText": "TELEVISITA cod. 15 0 1A", "FileParseExitCode": 1}],
        "OCRExitCode": 1, "IsErroredOnProcessing": False,
    })
    image = tmp_path / "foto.png"
    image.write_bytes(b"contenuto-immagine")

    code = main(["--config", str(config_file), "check-file", str(image), "--show-text"])

    out = capsys.readouterr().out
    assert code == 0
    assert "CONFORME" in out and "TELEVISITA cod. 15 0 1A" in out


def test_check_file_su_percorso_inesistente(config_file: Path, tmp_path: Path, capsys) -> None:
    code = main(["--config", str(config_file), "check-file", str(tmp_path / "manca.pdf")])
    assert code == 2
    assert "non trovato" in capsys.readouterr().err


def test_configurazione_mancante(tmp_path: Path, capsys) -> None:
    code = main(["--config", str(tmp_path / "assente.yaml"), "check-file", "x.pdf"])
    assert code == 2
    assert "Errore di configurazione" in capsys.readouterr().err


def test_no_dry_run_sovrascrive_la_configurazione(config_file: Path, tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """Il flag della CLI deve avere la precedenza sul file YAML."""
    visto = {}

    def finto_run_once(settings, minutes, unread_only=True):
        visto["dry_run"] = settings.forward.dry_run
        visto["unread_only"] = unread_only
        return 0

    monkeypatch.setattr("inoltro_email.__main__._cmd_run_once", finto_run_once)
    main(["--config", str(config_file), "--no-dry-run", "run-once"])
    assert visto["dry_run"] is False

    monkeypatch.setattr("inoltro_email.__main__._cmd_run_once", finto_run_once)
    main(["--config", str(config_file), "run-once"])
    assert visto["dry_run"] is True  # resta quello del file


def test_include_read_disattiva_il_filtro_sui_non_letti(config_file: Path,
                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    visto = {}

    def finto_run_once(settings, minutes, unread_only=True):
        visto["unread_only"] = unread_only
        return 0

    monkeypatch.setattr("inoltro_email.__main__._cmd_run_once", finto_run_once)
    main(["--config", str(config_file), "run-once"])
    assert visto["unread_only"] is True

    main(["--config", str(config_file), "run-once", "--include-read"])
    assert visto["unread_only"] is False


def test_casella_non_raggiungibile_senza_traceback(config_file: Path, capsys,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    """Senza token valido 'watch' deve spiegarsi, non stampare un traceback."""
    from inoltro_email.outlook.client import OutlookError

    def connessione_fallita(self):
        raise OutlookError("Nessun token valido")

    monkeypatch.setattr("inoltro_email.outlook.client.OutlookClient.connect", connessione_fallita)
    code = main(["--config", str(config_file), "watch"])

    assert code == 3
    assert "Errore Outlook" in capsys.readouterr().err


def test_authenticate_riporta_il_token_salvato(config_file: Path, capsys,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("inoltro_email.outlook.client.OutlookClient.authenticate",
                        lambda self: True)
    code = main(["--config", str(config_file), "authenticate"])

    assert code == 0
    assert "Autenticazione riuscita" in capsys.readouterr().out


def test_authenticate_fallita_restituisce_errore(config_file: Path, capsys,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("inoltro_email.outlook.client.OutlookClient.authenticate",
                        lambda self: False)
    code = main(["--config", str(config_file), "authenticate"])

    assert code == 3
    assert "non riuscita" in capsys.readouterr().err


def test_log_di_sessione_con_data_e_ora(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ogni avvio crea il proprio file di log, con data e ora nel nome."""
    import logging

    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave-di-prova")
    logs = tmp_path / "logs"
    config = tmp_path / "config.yaml"
    config.write_text(
        CONFIG.format(
            db=(tmp_path / "state.sqlite3").as_posix(),
            token=(tmp_path / "o365_token.txt").as_posix(),
        ).replace('level: "WARNING"', 'level: "INFO"').replace(
            "file: null", f'file: "{(logs / "inoltro.log").as_posix()}"'
        ),
        encoding="utf-8",
    )

    try:
        # File inesistente: basta ad arrivare oltre l'impostazione del logging.
        assert main(["--config", str(config), "check-file", str(tmp_path / "manca.pdf")]) == 2
        assert main(["--config", str(config), "check-file", str(tmp_path / "manca.pdf")]) == 2
    finally:
        for handler in list(logging.getLogger().handlers):
            logging.getLogger().removeHandler(handler)
            handler.close()

    prodotti = sorted(logs.glob("inoltro-*.log"))
    assert len(prodotti) == 2, prodotti
    assert not (logs / "inoltro.log").exists()
    assert "Sessione 'check-file' avviata il" in prodotti[0].read_text(encoding="utf-8")
