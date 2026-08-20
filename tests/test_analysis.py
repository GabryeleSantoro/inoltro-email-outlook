"""Test del flusso completo: email -> screening -> OCR -> criteri -> sentiment."""

from __future__ import annotations

from conftest import FakeOcrClient, attachment_payload, email_payload, make_blank_pdf, make_pdf

from inoltro_email.analysis import EmailAnalyzer
from inoltro_email.config import Settings
from inoltro_email.inbound import parse_email
from inoltro_email.models import Esito, Origine, TextSource
from inoltro_email.ocr.extractor import TextExtractor
from inoltro_email.ocr.ocrspace import OcrSpaceError

TESTO_CONFORME = "RICHIESTA DI TELEMEDICINA - prestazione 1501A"


def analizza(settings: Settings, payload: dict, ocr: FakeOcrClient | None = None):
    ocr = ocr if ocr is not None else FakeOcrClient(default_text=TESTO_CONFORME)
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr))
    email = parse_email(
        payload,
        include_inline_images=settings.attachments.include_inline_images,
        max_attachment_bytes=settings.attachments.max_bytes,
    )
    return analyzer.analyze(email), ocr


# ------------------------------------------------------------------ screening


def test_gli_allegati_si_leggono_anche_senza_riscontro_nel_testo(
    settings: Settings,
) -> None:
    """Il contenuto di un allegato puo' ribaltare un oggetto che non dice nulla."""
    payload = email_payload(
        subject="Richiesta appuntamento",
        body="Buongiorno, vorrei prenotare una visita in ambulatorio.",
        attachments=[attachment_payload("referto.pdf", make_blank_pdf())],
    )

    analysis, ocr = analizza(settings, payload)

    assert not analysis.screening.passed
    assert ocr.calls == ["referto.pdf"]  # letto lo stesso
    assert analysis.esito is Esito.CONFORME  # il documento contiene i criteri
    # Il sentiment viene calcolato comunque: serve a chi legge la risposta.
    assert analysis.sentiment.booking.score > 0


def test_stop_on_failure_risparmia_le_chiamate(settings: Settings) -> None:
    """Chi vuole risparmiare quota puo' ancora fermarsi allo screening."""
    settings.screening.stop_on_failure = True
    payload = email_payload(
        subject="Richiesta appuntamento",
        body="Buongiorno, vorrei prenotare una visita in ambulatorio.",
        attachments=[attachment_payload("referto.pdf", make_blank_pdf())],
    )

    analysis, ocr = analizza(settings, payload)

    assert analysis.esito is Esito.SCARTATA
    assert not analysis.conforme
    assert ocr.calls == []


def test_screening_puo_proseguire_anche_senza_riscontro(settings: Settings) -> None:
    settings.screening.stop_on_failure = False
    payload = email_payload(
        subject="Documenti",
        body="In allegato quanto richiesto.",
        attachments=[attachment_payload("referto.pdf", make_blank_pdf())],
    )

    analysis, ocr = analizza(settings, payload)

    assert not analysis.screening.passed
    assert analysis.esito is Esito.CONFORME  # il documento contiene i criteri
    assert len(ocr.calls) == 1


# -------------------------------------------------------- criteri sul testo


def test_allegato_conforme_promuove_l_email(settings: Settings) -> None:
    payload = email_payload(attachments=[attachment_payload("impegnativa.pdf", make_blank_pdf())])

    analysis, _ = analizza(settings, payload)

    assert analysis.esito is Esito.CONFORME
    assert analysis.conforme
    assert analysis.matched_attachment == "impegnativa.pdf"
    assert analysis.match is not None and analysis.match.found == ["telemedicina", "1501A"]
    assert analysis.screening.terms == ["televisita"]


def test_pdf_con_livello_di_testo_passa_comunque_dall_ocr(settings: Settings) -> None:
    """I due testi si uniscono: il livello di testo e' esatto, l'OCR aggiunge
    cio' che nel PDF e' solo immagine."""
    pdf = make_pdf(["Impegnativa per prestazione di TELEMEDICINA codice 1501A - paziente Rossi"])
    payload = email_payload(attachments=[attachment_payload("impegnativa.pdf", pdf)])

    analysis, ocr = analizza(settings, payload, FakeOcrClient(default_text="timbro del medico"))

    assert analysis.esito is Esito.CONFORME
    assert ocr.calls == ["impegnativa.pdf"]
    assert analysis.attachments[0].source is TextSource.PDF_TEXT_OCR
    assert "TELEMEDICINA" in analysis.attachments[0].text
    assert "timbro del medico" in analysis.attachments[0].text


def test_pdf_con_livello_di_testo_senza_ocr_se_richiesto(settings: Settings) -> None:
    settings.ocr.always_call = False
    pdf = make_pdf(["Impegnativa per prestazione di TELEMEDICINA codice 1501A - paziente Rossi"])
    payload = email_payload(attachments=[attachment_payload("impegnativa.pdf", pdf)])

    analysis, ocr = analizza(settings, payload, FakeOcrClient())

    assert analysis.esito is Esito.CONFORME
    assert ocr.calls == []
    assert analysis.attachments[0].source is TextSource.PDF_TEXT


def test_ocr_fallito_ripiega_sul_livello_di_testo(settings: Settings) -> None:
    """Se il PDF il testo ce l'ha, un OCR non riuscito non fa perdere il documento."""
    class OcrRotto:
        calls: list = []

        def parse_file(self, path):
            raise OcrSpaceError("quota giornaliera esaurita")

    pdf = make_pdf(["Impegnativa per prestazione di TELEMEDICINA codice 1501A - paziente Rossi"])
    payload = email_payload(attachments=[attachment_payload("impegnativa.pdf", pdf)])

    analysis, _ = analizza(settings, payload, OcrRotto())

    assert analysis.esito is Esito.CONFORME
    assert analysis.attachments[0].source is TextSource.PDF_TEXT


def test_manca_il_codice_nel_documento(settings: Settings) -> None:
    payload = email_payload(attachments=[attachment_payload("impegnativa.pdf", make_blank_pdf())])

    analysis, _ = analizza(
        settings, payload, FakeOcrClient(default_text="Richiesta di telemedicina, nessun codice")
    )

    assert analysis.esito is Esito.NON_CONFORME
    assert analysis.match is not None and analysis.match.missing == ["1501A"]
    assert analysis.matched_attachment is None


def test_email_senza_allegati(settings: Settings) -> None:
    analysis, ocr = analizza(settings, email_payload())

    assert analysis.esito is Esito.SENZA_CONTENUTO
    assert analysis.attachments == []
    assert ocr.calls == []


def test_foto_nel_corpo_analizzata(settings: Settings) -> None:
    """L'impegnativa fotografata e incollata nel messaggio va letta comunque."""
    payload = email_payload(attachments=[
        attachment_payload("foto.jpg", b"jpeg", content_type="image/jpeg", inline=True),
    ])

    analysis, ocr = analizza(settings, payload)

    assert analysis.esito is Esito.CONFORME
    assert ocr.calls == ["foto.jpg"]
    assert analysis.attachments[0].origine is Origine.CORPO


def test_tutti_i_documenti_vengono_letti(settings: Settings) -> None:
    """Anche dopo un documento conforme si legge il resto: tutto fa computo."""
    payload = email_payload(attachments=[
        attachment_payload("primo.pdf", make_blank_pdf()),
        attachment_payload("secondo.pdf", make_blank_pdf()),
    ])

    analysis, ocr = analizza(settings, payload)

    assert len(ocr.calls) == 2
    assert len(analysis.attachments) == 2
    assert analysis.matched_attachment == "primo.pdf"


def test_ci_si_puo_fermare_al_primo_conforme(settings: Settings) -> None:
    settings.attachments.analyze_all = False
    payload = email_payload(attachments=[
        attachment_payload("primo.pdf", make_blank_pdf()),
        attachment_payload("secondo.pdf", make_blank_pdf()),
    ])

    analysis, ocr = analizza(settings, payload)

    assert len(ocr.calls) == 1
    assert analysis.matched_attachment == "primo.pdf"


def test_criteri_riassunti_su_tutti_i_documenti(settings: Settings) -> None:
    """I trovati sono l'unione, i mancanti solo cio' che non c'e' da nessuna parte."""
    payload = email_payload(attachments=[
        attachment_payload("parziale.pdf", make_blank_pdf()),
        attachment_payload("altro.pdf", make_blank_pdf()),
    ])
    ocr = FakeOcrClient(texts={
        "parziale": "Richiesta di telemedicina senza codice",
        "altro": "Prestazione 1501A",
    })

    analysis, _ = analizza(settings, payload, ocr)

    # Nessun documento ha entrambi i criteri: non e' conforme...
    assert analysis.esito is Esito.NON_CONFORME
    # ...ma la risposta dice cosa e' stato trovato nell'insieme del messaggio.
    assert analysis.match is not None
    assert sorted(analysis.match.found) == ["1501A", "telemedicina"]
    assert analysis.match.missing == []


def test_piu_documenti_conformi_alzano_la_sicurezza(settings: Settings) -> None:
    uno = email_payload(attachments=[attachment_payload("primo.pdf", make_blank_pdf())])
    due = email_payload(attachments=[
        attachment_payload("primo.pdf", make_blank_pdf()),
        attachment_payload("secondo.pdf", make_blank_pdf()),
    ])

    con_uno, _ = analizza(settings, uno)
    con_due, _ = analizza(settings, due)

    assert con_due.telemedicina.percent >= con_uno.telemedicina.percent
    assert sum(1 for item in con_due.attachments if item.matched) == 2


def test_secondo_allegato_recupera_la_conformita(settings: Settings) -> None:
    payload = email_payload(attachments=[
        attachment_payload("informativa.pdf", make_blank_pdf()),
        attachment_payload("impegnativa.pdf", make_blank_pdf()),
    ])
    ocr = FakeOcrClient(texts={
        "informativa": "Informativa sulla privacy",
        "impegnativa": TESTO_CONFORME,
    })

    analysis, _ = analizza(settings, payload, ocr)

    assert analysis.esito is Esito.CONFORME
    assert analysis.matched_attachment == "impegnativa.pdf"
    assert len(analysis.attachments) == 2


def test_numero_massimo_di_file_rispettato(settings: Settings) -> None:
    settings.attachments.max_files = 2
    settings.attachments.analyze_all = True
    payload = email_payload(attachments=[
        attachment_payload(f"file{index}.pdf", make_blank_pdf()) for index in range(5)
    ])

    _, ocr = analizza(settings, payload, FakeOcrClient(default_text="niente di rilevante"))

    assert len(ocr.calls) == 2


def test_allegato_illeggibile_non_blocca_la_risposta(settings: Settings) -> None:
    class OcrRotto:
        def parse_file(self, path):
            raise OcrSpaceError("quota giornaliera esaurita")

    payload = email_payload(attachments=[attachment_payload("scansione.pdf", make_blank_pdf())])
    analyzer = EmailAnalyzer(settings, TextExtractor(settings, OcrRotto()))
    analysis = analyzer.analyze(parse_email(payload))

    assert analysis.esito is Esito.SENZA_CONTENUTO
    assert analysis.attachments[0].source is TextSource.ERROR
    assert "quota" in (analysis.attachments[0].error or "")


def test_allegato_di_tipo_non_previsto_ignorato(settings: Settings) -> None:
    payload = email_payload(attachments=[
        attachment_payload("archivio.zip", b"PK\x03\x04", content_type="application/zip"),
    ])

    analysis, ocr = analizza(settings, payload)

    assert analysis.esito is Esito.SENZA_CONTENUTO
    assert ocr.calls == []


# ------------------------------------------------------------------ sentiment


def test_sentiment_incluso_nel_risultato(settings: Settings) -> None:
    payload = email_payload(
        subject="Prenotazione televisita",
        body="Buongiorno, vorrei prenotare una televisita. Grazie mille.",
        attachments=[attachment_payload("impegnativa.pdf", make_blank_pdf())],
    )

    analysis, _ = analizza(settings, payload)

    assert analysis.sentiment.label == "positivo"
    assert analysis.sentiment.booking.is_booking
    # L'allegato conforme entra fra gli indizi di prenotazione.
    assert "allegato conforme" in analysis.sentiment.booking.signals


def test_durata_registrata(settings: Settings) -> None:
    analysis, _ = analizza(settings, email_payload())
    assert analysis.duration_ms >= 0
