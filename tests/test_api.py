"""Test dell'endpoint HTTP interrogato da Power Automate."""

from __future__ import annotations

import pytest
from conftest import FakeOcrClient, attachment_payload, email_payload, make_blank_pdf
from fastapi.testclient import TestClient

from inoltro_email.analysis import EmailAnalyzer
from inoltro_email.api.app import create_app
from inoltro_email.config import Settings
from inoltro_email.ocr.extractor import TextExtractor

TESTO_CONFORME = "RICHIESTA DI TELEMEDICINA - prestazione 1501A"


@pytest.fixture
def ocr() -> FakeOcrClient:
    return FakeOcrClient(default_text=TESTO_CONFORME)


@pytest.fixture
def client(settings: Settings, ocr: FakeOcrClient) -> TestClient:
    """Applicazione con OCR fittizio: nessuna chiamata di rete nei test."""
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    with TestClient(create_app(settings, analyzer=analyzer)) as instance:
        yield instance


def test_salute(client: TestClient) -> None:
    risposta = client.get("/salute")

    assert risposta.status_code == 200
    assert risposta.json()["stato"] == "ok"


def test_informazioni(client: TestClient) -> None:
    corpo = client.get("/").json()
    assert corpo["analisi"] == "/analizza-email"


def test_email_conforme(client: TestClient) -> None:
    payload = email_payload(attachments=[attachment_payload("impegnativa.pdf", make_blank_pdf())])

    risposta = client.post("/analizza-email", json=payload)

    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["esito"] == "conforme"
    assert corpo["conforme"] is True
    assert corpo["screening"] == {
        "superato": True, "termini": ["televisita"], "dove": ["oggetto", "corpo"],
    }
    assert corpo["criteri"]["trovati"] == ["telemedicina", "1501A"]
    assert corpo["criteri"]["documento"] == "impegnativa.pdf"
    assert corpo["documenti"][0]["origine"] == "allegato"
    assert corpo["sentiment"]["prenotazione"]["e_prenotazione"] is True
    assert corpo["id_messaggio"] == "<msg-1@example.com>"


def test_email_fuori_tema_scartata(client: TestClient, ocr: FakeOcrClient) -> None:
    payload = email_payload(
        subject="Fattura di luglio",
        body="Trasmettiamo la fattura in allegato.",
        attachments=[attachment_payload("fattura.pdf", make_blank_pdf())],
    )

    corpo = client.post("/analizza-email", json=payload).json()

    assert corpo["esito"] == "scartata"
    assert corpo["conforme"] is False
    assert corpo["screening"]["superato"] is False
    assert ocr.calls == []


def test_email_senza_documento_conforme(client: TestClient, settings: Settings) -> None:
    payload = email_payload(attachments=[attachment_payload("altro.pdf", make_blank_pdf())])
    analyzer = EmailAnalyzer(
        settings, TextExtractor(settings, FakeOcrClient(default_text="Referto di visita"))
    )
    with TestClient(create_app(settings, analyzer=analyzer)) as altro_client:
        corpo = altro_client.post("/analizza-email", json=payload).json()

    assert corpo["esito"] == "non_conforme"
    assert corpo["criteri"]["mancanti"] == ["telemedicina", "1501A"]


def test_json_non_valido(client: TestClient) -> None:
    risposta = client.post(
        "/analizza-email", content=b"{non json", headers={"content-type": "application/json"}
    )

    assert risposta.status_code == 400
    assert "JSON non valido" in risposta.json()["errore"]


def test_corpo_vuoto(client: TestClient) -> None:
    risposta = client.post(
        "/analizza-email", content=b"", headers={"content-type": "application/json"}
    )

    assert risposta.status_code == 400
    assert "vuoto" in risposta.json()["errore"]


def test_payload_senza_oggetto_ne_corpo(client: TestClient) -> None:
    risposta = client.post("/analizza-email", json={"subject": "", "body": ""})

    assert risposta.status_code == 400
    assert "nulla da analizzare" in risposta.json()["errore"]


def test_richiesta_troppo_grande(settings: Settings, ocr: FakeOcrClient) -> None:
    settings.api.max_request_bytes = 50
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    with TestClient(create_app(settings, analyzer=analyzer)) as client:
        risposta = client.post("/analizza-email", json=email_payload())

    assert risposta.status_code == 413
    assert "troppo grande" in risposta.json()["errore"]


# ------------------------------------------------------------------ sicurezza


@pytest.fixture
def client_protetto(settings: Settings, ocr: FakeOcrClient) -> TestClient:
    settings.api.api_key = "chiave-condivisa"
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    with TestClient(create_app(settings, analyzer=analyzer)) as instance:
        yield instance


def test_chiave_corretta_accettata(client_protetto: TestClient) -> None:
    risposta = client_protetto.post(
        "/analizza-email", json=email_payload(), headers={"X-API-Key": "chiave-condivisa"}
    )
    assert risposta.status_code == 200


def test_chiave_mancante_rifiutata(client_protetto: TestClient) -> None:
    risposta = client_protetto.post("/analizza-email", json=email_payload())

    assert risposta.status_code == 401
    assert "X-API-Key" in risposta.json()["errore"]


def test_chiave_errata_rifiutata(client_protetto: TestClient) -> None:
    risposta = client_protetto.post(
        "/analizza-email", json=email_payload(), headers={"X-API-Key": "sbagliata"}
    )
    assert risposta.status_code == 401


def test_salute_resta_pubblica(client_protetto: TestClient) -> None:
    """La sonda di stato non richiede la chiave: la usano i bilanciatori."""
    assert client_protetto.get("/salute").status_code == 200


def test_documentazione_openapi_disponibile(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    assert "/analizza-email" in schema["paths"]
