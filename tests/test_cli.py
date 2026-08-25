"""Test della riga di comando.

`analizza` e `check-file` sono i due comandi che non richiedono di far partire
il server: il primo ripete esattamente cio' che fa l'endpoint HTTP su un
payload salvato su file, il secondo prova OCR e criteri su un singolo file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import responses
from conftest import attachment_payload, email_payload, make_pdf

from inoltro_email.__main__ import main

ENDPOINT = "https://api.ocr.space/parse/image"

CONFIG = """
api:
  port: 8123
screening:
  keywords: ["telemedicina", "televisita"]
  mode: any
rules:
  keywords: ["telemedicina"]
  codes: ["1501A"]
  mode: all
ocr:
  endpoint: "https://api.ocr.space/parse/image"
  engine: 2
  # Nessuna chiamata di rete nei test della riga di comando: qui si usano PDF
  # che il livello di testo ce l'hanno gia'.
  always_call: false
logging:
  level: "WARNING"
  file: null
"""


@pytest.fixture
def config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave-di-prova")
    path = tmp_path / "config.yaml"
    path.write_text(CONFIG, encoding="utf-8")
    return path


# ------------------------------------------------------------ comando analizza


def test_analizza_payload_conforme(config_file: Path, tmp_path: Path, capsys) -> None:
    """PDF con livello di testo: nessuna chiamata di rete, risposta completa."""
    pdf = make_pdf(["Impegnativa TELEMEDICINA prestazione 1501A paziente Rossi"])
    payload = tmp_path / "email.json"
    payload.write_text(
        json.dumps(email_payload(attachments=[attachment_payload("impegnativa.pdf", pdf)])),
        encoding="utf-8",
    )

    code = main(["--config", str(config_file), "analizza", str(payload)])

    assert code == 0
    risultato = json.loads(capsys.readouterr().out)
    assert risultato["esito"] == "conforme"
    assert risultato["criteri"]["documento"] == "impegnativa.pdf"
    assert risultato["sentiment"]["prenotazione"]["e_prenotazione"] is True


def test_analizza_email_fuori_tema(config_file: Path, tmp_path: Path, capsys) -> None:
    """Senza allegati non c'e' nulla da leggere: l'esito lo dicono le percentuali."""
    payload = tmp_path / "email.json"
    payload.write_text(
        json.dumps(email_payload(subject="Fattura", body="In allegato la fattura di luglio.")),
        encoding="utf-8",
    )

    code = main(["--config", str(config_file), "analizza", str(payload)])

    assert code == 0
    risposta = json.loads(capsys.readouterr().out)
    assert risposta["esito"] == "senza_contenuto"
    assert risposta["prenotazione_telemedicina"] is False
    assert risposta["telemedicina"]["percentuale"] < 25


def test_analizza_da_standard_input(config_file: Path, capsys,
                                    monkeypatch: pytest.MonkeyPatch) -> None:
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(email_payload())))
    code = main(["--config", str(config_file), "analizza"])

    assert code == 0
    assert json.loads(capsys.readouterr().out)["esito"] == "senza_contenuto"


def test_analizza_json_non_valido(config_file: Path, tmp_path: Path, capsys) -> None:
    payload = tmp_path / "rotto.json"
    payload.write_text("{non json", encoding="utf-8")

    code = main(["--config", str(config_file), "analizza", str(payload)])

    assert code == 2
    assert "JSON non valido" in capsys.readouterr().err


def test_analizza_payload_vuoto(config_file: Path, tmp_path: Path, capsys) -> None:
    payload = tmp_path / "vuoto.json"
    payload.write_text(json.dumps({"subject": "", "body": ""}), encoding="utf-8")

    code = main(["--config", str(config_file), "analizza", str(payload)])

    assert code == 2
    assert "non interpretabile" in capsys.readouterr().err


# ---------------------------------------------------------- comando check-file


def test_check_file_su_pdf_conforme(config_file: Path, tmp_path: Path, capsys) -> None:
    pdf = tmp_path / "referto.pdf"
    pdf.write_bytes(make_pdf(["Richiesta TELEMEDICINA prestazione 1501A paziente Rossi"]))

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
        "ParsedResults": [{"ParsedText": "TELEMEDICINA cod. 15 0 1A", "FileParseExitCode": 1}],
        "OCRExitCode": 1, "IsErroredOnProcessing": False,
    })
    image = tmp_path / "foto.png"
    image.write_bytes(b"contenuto-immagine")

    code = main(["--config", str(config_file), "check-file", str(image), "--show-text"])

    out = capsys.readouterr().out
    assert code == 0
    assert "CONFORME" in out and "TELEMEDICINA cod. 15 0 1A" in out


def test_check_file_su_percorso_inesistente(config_file: Path, tmp_path: Path, capsys) -> None:
    code = main(["--config", str(config_file), "check-file", str(tmp_path / "manca.pdf")])

    assert code == 2
    assert "non trovato" in capsys.readouterr().err


# ---------------------------------------------------------------- comando serve


def test_serve_usa_host_e_porta_della_riga_di_comando(config_file: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    visto = {}

    def finto_run(
        settings,
        reload=False,
        flow_path=None,
        flow_timer=60,
        session_log_file=None,
        log_level=None,
    ):
        visto["host"] = settings.api.host
        visto["port"] = settings.api.port
        visto["reload"] = reload

    monkeypatch.setattr("inoltro_email.api.server.run", finto_run)
    code = main(["--config", str(config_file), "serve", "--host", "127.0.0.1", "--port", "9999"])

    assert code == 0
    assert visto == {"host": "127.0.0.1", "port": 9999, "reload": False}


def test_serve_senza_argomenti_usa_la_configurazione(config_file: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    visto = {}
    monkeypatch.setattr("inoltro_email.api.server.run",
                        lambda settings, reload=False, flow_path=None, flow_timer=60,
                        session_log_file=None, log_level=None:
                        visto.update(port=settings.api.port))
    main(["--config", str(config_file), "serve"])

    assert visto["port"] == 8123


def test_configurazione_mancante(tmp_path: Path, capsys) -> None:
    code = main(["--config", str(tmp_path / "assente.yaml"), "check-file", "x.pdf"])

    assert code == 2
    assert "Errore di configurazione" in capsys.readouterr().err


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
            "file: null", f'file: "{(logs / "servizio.log").as_posix()}"'
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

    prodotti = sorted(logs.glob("servizio-*.log"))
    assert len(prodotti) == 2, prodotti
    assert not (logs / "servizio.log").exists()
    contenuto = prodotti[0].read_text(encoding="utf-8")
    assert "Sessione 'check-file' avviata il" in contenuto
    assert "Sessione 'check-file' terminata il" in contenuto
    assert "codice=2" in contenuto
