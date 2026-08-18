"""Test della riga di comando, in particolare del comando `check-file`.

`check-file` e' l'unico comando che gira anche fuori da Windows: e' il modo
previsto per verificare chiave API e criteri senza toccare Outlook.
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
    path.write_text(CONFIG.format(db=(tmp_path / "state.sqlite3").as_posix()), encoding="utf-8")
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
        "ParsedResults": [{"ParsedText": "TELEVISITA cod. 15 A 10", "FileParseExitCode": 1}],
        "OCRExitCode": 1, "IsErroredOnProcessing": False,
    })
    image = tmp_path / "foto.png"
    image.write_bytes(b"contenuto-immagine")

    code = main(["--config", str(config_file), "check-file", str(image), "--show-text"])

    out = capsys.readouterr().out
    assert code == 0
    assert "CONFORME" in out and "TELEVISITA cod. 15 A 10" in out


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

    def finto_run_once(settings, minutes):
        visto["dry_run"] = settings.forward.dry_run
        return 0

    monkeypatch.setattr("inoltro_email.__main__._cmd_run_once", finto_run_once)
    main(["--config", str(config_file), "--no-dry-run", "run-once"])
    assert visto["dry_run"] is False

    monkeypatch.setattr("inoltro_email.__main__._cmd_run_once", finto_run_once)
    main(["--config", str(config_file), "run-once"])
    assert visto["dry_run"] is True  # resta quello del file


def test_outlook_non_disponibile_senza_traceback(config_file: Path, capsys,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    """Fuori da Windows 'watch' deve spiegarsi, non stampare un traceback."""
    from inoltro_email.outlook.client import OutlookError

    def connessione_fallita(self):
        raise OutlookError("pywin32 non disponibile")

    monkeypatch.setattr("inoltro_email.outlook.client.OutlookClient.connect", connessione_fallita)
    code = main(["--config", str(config_file), "watch"])

    assert code == 3
    assert "Errore Outlook" in capsys.readouterr().err
