"""Test dell'endpoint HTTP interrogato da Power Automate."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3

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
    assert corpo["considerata"] is True
    assert corpo["conforme"] is True
    assert corpo["screening"] == {
        "superato": True, "termini": ["televisita"], "dove": ["oggetto", "corpo"],
    }
    assert corpo["criteri"]["trovati"] == ["telemedicina", "1501A"]
    assert corpo["criteri"]["documento"] == "impegnativa.pdf"
    assert corpo["documenti"][0]["origine"] == "allegato"
    assert corpo["sentiment"]["prenotazione"]["e_prenotazione"] is True
    assert corpo["id_messaggio"].startswith("<msg-")


def test_email_fuori_dalla_finestra_non_viene_analizzata(
    settings: Settings, ocr: FakeOcrClient, tmp_path
) -> None:
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    payload = email_payload(
        receivedDateTime="",
        date=(datetime.now(timezone.utc) - timedelta(seconds=121)).isoformat(),
        attachments=[attachment_payload("impegnativa.pdf", make_blank_pdf())],
    )
    with TestClient(create_app(
        settings, analyzer=analyzer, flow_timer=60,
        message_store_path=tmp_path / "checked.sqlite3",
    )) as instance:
        risposta = instance.post("/analizza-email", json=payload)

    assert risposta.status_code == 202
    assert risposta.json()["considerata"] is False
    assert risposta.json()["motivo"] == "fuori_finestra_temporale"
    assert risposta.json()["finestra_secondi"] == 120
    assert ocr.calls == []


def test_email_gia_vista_non_viene_analizzata_due_volte(
    settings: Settings, ocr: FakeOcrClient, tmp_path
) -> None:
    database = tmp_path / "checked.sqlite3"
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    payload = email_payload(attachments=[attachment_payload("impegnativa.pdf", make_blank_pdf())])
    with TestClient(create_app(
        settings, analyzer=analyzer, message_store_path=database,
    )) as instance:
        prima = instance.post("/analizza-email", json=payload)
        seconda = instance.post("/analizza-email", json=payload)

    assert prima.status_code == 200
    assert seconda.status_code == 202
    assert seconda.json()["considerata"] is False
    assert seconda.json()["motivo"] == "gia_analizzato"
    assert ocr.calls == ["impegnativa.pdf"]
    with sqlite3.connect(database) as connection:
        stored = connection.execute("SELECT payload_json FROM checked_messages").fetchone()
    assert stored is not None and '"subject"' in stored[0]


def test_email_fuori_tema_letta_comunque(client: TestClient, ocr: FakeOcrClient) -> None:
    """L'allegato si legge lo stesso: e' il suo contenuto a decidere."""
    payload = email_payload(
        subject="Fattura di luglio",
        body="Trasmettiamo la fattura in allegato.",
        attachments=[attachment_payload("fattura.pdf", make_blank_pdf())],
    )

    corpo = client.post("/analizza-email", json=payload).json()

    assert corpo["screening"]["superato"] is False
    assert ocr.calls == ["fattura.pdf"]
    # L'OCR di prova restituisce un testo conforme: il documento ribalta
    # l'oggetto, ed e' esattamente il motivo per cui lo si legge.
    assert corpo["esito"] == "conforme"
    assert corpo["telemedicina"]["percentuale"] > 50


def test_screening_puo_ancora_fermare_l_ocr(settings: Settings, ocr: FakeOcrClient) -> None:
    settings.screening.stop_on_failure = True
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    with TestClient(create_app(settings, analyzer=analyzer)) as instance:
        corpo = instance.post("/analizza-email", json=email_payload(
            subject="Fattura di luglio",
            body="Trasmettiamo la fattura in allegato.",
            attachments=[attachment_payload("fattura.pdf", make_blank_pdf())],
        )).json()

    assert corpo["esito"] == "scartata"
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
        f'"date":"{datetime.now().strftime("%m/%d/%Y %H:%M:%S")}"{allegato}}}'
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
    """Soglia configurata: chi vuole risparmiare quota puo' ancora farlo."""
    settings.screening.stop_on_failure = True
    settings.confidence.min_percent_for_ocr = 25.0
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


def test_il_testo_letto_torna_nella_risposta(client: TestClient) -> None:
    payload = email_payload(attachments=[attachment_payload("impegnativa.pdf", make_blank_pdf())])

    documento = client.post("/analizza-email", json=payload).json()["documenti"][0]

    assert documento["testo"] == TESTO_CONFORME
    assert documento["testo_troncato"] is False


def test_il_testo_puo_essere_escluso(settings: Settings, ocr: FakeOcrClient) -> None:
    """E' un dato sanitario: chi non lo vuole in giro lo toglie."""
    settings.attachments.return_text = False
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    with TestClient(create_app(settings, analyzer=analyzer)) as instance:
        documento = instance.post("/analizza-email", json=email_payload(
            attachments=[attachment_payload("impegnativa.pdf", make_blank_pdf())],
        )).json()["documenti"][0]

    assert "testo" not in documento
    assert documento["caratteri"] > 0  # il conteggio resta


def test_il_testo_viene_troncato(settings: Settings, ocr: FakeOcrClient) -> None:
    settings.attachments.max_text_chars = 10
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    with TestClient(create_app(settings, analyzer=analyzer)) as instance:
        documento = instance.post("/analizza-email", json=email_payload(
            attachments=[attachment_payload("impegnativa.pdf", make_blank_pdf())],
        )).json()["documenti"][0]

    assert documento["testo"] == TESTO_CONFORME[:10]
    assert documento["testo_troncato"] is True
    assert documento["caratteri"] == len(TESTO_CONFORME)


def test_tutti_gli_allegati_arrivano_all_ocr(settings: Settings) -> None:
    """Nessuna scorciatoia: si legge tutto, anche dopo un documento conforme."""
    ocr = FakeOcrClient(texts={
        "primo": TESTO_CONFORME,
        "secondo": "Informativa sulla privacy",
        "terzo": "Consenso al trattamento",
    })
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    with TestClient(create_app(settings, analyzer=analyzer)) as instance:
        corpo = instance.post("/analizza-email", json=email_payload(attachments=[
            attachment_payload("primo.pdf", make_blank_pdf()),
            attachment_payload("secondo.pdf", make_blank_pdf()),
            attachment_payload("terzo.pdf", make_blank_pdf()),
        ])).json()

    assert len(ocr.calls) == 3
    assert corpo["documenti_letti"] == 3
    assert corpo["documenti_conformi"] == 1
    assert [d["nome"] for d in corpo["documenti"]] == ["primo.pdf", "secondo.pdf", "terzo.pdf"]


# ------------------------------------------------- codice di stato della risposta


def test_duecento_solo_per_una_prenotazione_certa(client: TestClient) -> None:
    risposta = client.post("/analizza-email", json=email_payload(
        subject="Richiesta prenotazione televisita",
        body="Vorrei prenotare una televisita. Allego l'impegnativa.",
        attachments=[attachment_payload("impegnativa.pdf", make_blank_pdf())],
    ))

    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["prenotazione_certa"] is True
    assert corpo["prenotazione"]["percentuale"] >= 80


def test_duecentodue_quando_non_e_una_prenotazione(client: TestClient) -> None:
    """Non e' un errore: e' un esito legittimo, con il verdetto nel corpo."""
    risposta = client.post("/analizza-email", json=email_payload(
        subject="Accessi Telemedicina Luglio 2026",
        body="In allegato gli accessi in Telemedicina del mese.",
    ))

    assert risposta.status_code == 202
    corpo = risposta.json()
    assert corpo["prenotazione_certa"] is False
    assert corpo["telemedicina"]["percentuale"] > 0  # il verdetto c'e' comunque


def test_duecentodue_quando_la_prenotazione_e_solo_probabile(client: TestClient) -> None:
    """Sopra la soglia di conferma ma sotto quella di certezza: la guarda una persona."""
    risposta = client.post("/analizza-email", json=email_payload(
        subject="Rinnovo piano terapeutico",
        body="Si chiede appuntamento di televisita per il rinnovo del piano terapeutico.",
    ))

    corpo = risposta.json()
    assert corpo["prenotazione"]["confermato"] is True
    assert corpo["prenotazione_certa"] is False
    assert risposta.status_code == 202


def test_la_soglia_di_certezza_e_configurabile(
    settings: Settings, ocr: FakeOcrClient
) -> None:
    settings.confidence.certainty_threshold = 60.0
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    with TestClient(create_app(settings, analyzer=analyzer)) as instance:
        risposta = instance.post("/analizza-email", json=email_payload(
            subject="Rinnovo piano terapeutico",
            body="Si chiede appuntamento di televisita per il rinnovo del piano terapeutico.",
        ))

    assert risposta.status_code == 200
    assert risposta.json()["prenotazione_certa"] is True


def test_gli_errori_restano_errori(client: TestClient) -> None:
    """Il 202 vale per le analisi riuscite, non copre i payload rotti."""
    risposta = client.post(
        "/analizza-email", content=b"{non json", headers={"content-type": "application/json"}
    )

    assert risposta.status_code == 400
