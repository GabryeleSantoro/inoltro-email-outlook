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


def test_email_senza_telemedicina_scartata_senza_ocr(settings: Settings) -> None:
    """Se oggetto e corpo non ne parlano, non si spende una chiamata OCR."""
    payload = email_payload(
        subject="Richiesta appuntamento",
        body="Buongiorno, vorrei prenotare una visita in ambulatorio.",
        attachments=[attachment_payload("referto.pdf", make_blank_pdf())],
    )

    analysis, ocr = analizza(settings, payload)

    assert analysis.esito is Esito.SCARTATA
    assert not analysis.conforme
    assert not analysis.screening.passed
    assert ocr.calls == []
    # Il sentiment viene calcolato comunque: serve a chi legge la risposta.
    assert analysis.sentiment.booking.score > 0


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


def test_pdf_con_livello_di_testo_non_passa_dall_ocr(settings: Settings) -> None:
    pdf = make_pdf(["Impegnativa per prestazione di TELEMEDICINA codice 1501A - paziente Rossi"])
    payload = email_payload(attachments=[attachment_payload("impegnativa.pdf", pdf)])

    analysis, ocr = analizza(settings, payload, FakeOcrClient())

    assert analysis.esito is Esito.CONFORME
    assert ocr.calls == []
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


def test_ci_si_ferma_al_primo_documento_conforme(settings: Settings) -> None:
    payload = email_payload(attachments=[
        attachment_payload("primo.pdf", make_blank_pdf()),
        attachment_payload("secondo.pdf", make_blank_pdf()),
    ])

    analysis, ocr = analizza(settings, payload)

    assert len(ocr.calls) == 1
    assert analysis.matched_attachment == "primo.pdf"


def test_analyze_all_legge_tutti_i_documenti(settings: Settings) -> None:
    settings.attachments.analyze_all = True
    payload = email_payload(attachments=[
        attachment_payload("primo.pdf", make_blank_pdf()),
        attachment_payload("secondo.pdf", make_blank_pdf()),
    ])

    analysis, ocr = analizza(settings, payload)

    assert len(ocr.calls) == 2
    assert len(analysis.attachments) == 2


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
