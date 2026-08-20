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


# ----------------------------------------- payload reali del flusso in uso


def _payload_del_flusso(oggetto: str, corpo_html: str, percorso: str = "") -> bytes:
    """Ricostruisce il JSON come lo scrive davvero Power Automate.

    A capo veri nel corpo, virgolette degli attributi HTML non protette e
    percorso Windows con barre rovesciate: e' il payload che nei log finiva
    sistematicamente in 400.
    """
    allegato = f',"attchment":"{percorso}"' if percorso else ',"attchment":""'
    return (
        f'{{"subject":"{oggetto}","body":"{corpo_html}",'
        f'"date":"08/20/2026 10:26"{allegato}}}'
    ).encode("utf-8")


CORPO_DEL_LOG = (
    "<html>\n<head>\n"
    '<style type="text/css" style="display:none;"> P {margin-top:0;} </style>\n'
    "</head>\n"
    '<body dir="ltr">\n'
    '<div class="elementToProof" style="font-size: 12pt;">\n'
    "Buongiorno, vorrei prenotare una televisita. In allegato l'impegnativa.</div>\n"
    "</body>\n</html>\n"
)


def test_payload_non_valido_del_flusso_viene_riparato(client: TestClient) -> None:
    risposta = client.post(
        "/analizza-email",
        content=_payload_del_flusso("Richiesta prenotazione televisita", CORPO_DEL_LOG),
        headers={"content-type": "application/json"},
    )

    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["oggetto"] == "Richiesta prenotazione televisita"
    assert corpo["screening"]["superato"] is True
    assert any("riparato" in avviso for avviso in corpo["avvisi"])


def test_allegato_indicato_per_percorso_arriva_all_ocr(
    settings: Settings, ocr: FakeOcrClient, tmp_path
) -> None:
    """Il percorso del payload e' la base per l'invio a ocr.space."""
    impegnativa = tmp_path / "image (2).png"
    impegnativa.write_bytes(b"finta immagine")
    settings.local_files.search_directories = [tmp_path]

    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    with TestClient(create_app(settings, analyzer=analyzer)) as instance:
        risposta = instance.post(
            "/analizza-email",
            content=_payload_del_flusso(
                "Richiesta prenotazione televisita",
                CORPO_DEL_LOG,
                r"C:\\Users\\user\\Documents\\Power Automate\\Allegati\\image (2).png",
            ),
            headers={"content-type": "application/json"},
        )

    assert risposta.status_code == 200
    corpo = risposta.json()
    assert ocr.calls == ["image (2).png"]
    assert corpo["esito"] == "conforme"
    assert corpo["documenti"][0]["nome"] == "image (2).png"


def test_percentuali_nella_risposta(client: TestClient) -> None:
    payload = email_payload(attachments=[attachment_payload("impegnativa.pdf", make_blank_pdf())])

    corpo = client.post("/analizza-email", json=payload).json()

    assert corpo["telemedicina"]["percentuale"] > 90
    assert corpo["telemedicina"]["livello"] == "molto alta"
    assert corpo["telemedicina"]["confermato"] is True
    assert corpo["prenotazione"]["percentuale"] > 90
    assert corpo["prenotazione_telemedicina"] is True
    assert corpo["telemedicina"]["indizi_a_favore"], "gli indizi spiegano la percentuale"


def test_email_di_telemedicina_che_non_e_prenotazione(
    settings: Settings, ocr: FakeOcrClient
) -> None:
    """Foglio degli accessi mensili: telemedicina si', prenotazione no."""
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    with TestClient(create_app(settings, analyzer=analyzer)) as instance:
        corpo = instance.post(
            "/analizza-email",
            json=email_payload(
                subject="Accessi Telemedicina Luglio 2026 Dott.ssa Caccavo",
                body="In allegato gli accessi in Telemedicina del mese di Luglio 2026.",
            ),
        ).json()

    assert corpo["telemedicina"]["confermato"] is True
    assert corpo["prenotazione"]["confermato"] is False
    assert corpo["prenotazione_telemedicina"] is False


def test_sotto_la_soglia_minima_non_si_chiama_l_ocr(
    settings: Settings, ocr: FakeOcrClient
) -> None:
    """Il termine solo nell'indirizzo non giustifica una chiamata all'OCR."""
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    with TestClient(create_app(settings, analyzer=analyzer)) as instance:
        corpo = instance.post(
            "/analizza-email",
            json=email_payload(
                subject="Richiesta accesso piattaforma COT",
                body="Si richiede l'accesso alla piattaforma COT.\n"
                     "Da: Telemedicina <telemedicina@aslsalerno.it>",
                attachments=[attachment_payload("modulo.pdf", make_blank_pdf())],
            ),
        ).json()

    assert corpo["esito"] == "scartata"
    assert corpo["telemedicina"]["percentuale"] < 25
    assert ocr.calls == []
