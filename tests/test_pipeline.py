"""Test del flusso completo: messaggio -> allegati -> OCR -> criteri -> inoltro."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import FakeMailClient, FakeMessage, FakeOcrClient, make_blank_pdf, make_pdf

from inoltro_email.config import Settings
from inoltro_email.models import Decision
from inoltro_email.ocr.extractor import TextExtractor
from inoltro_email.ocr.ocrspace import OcrSpaceError
from inoltro_email.pipeline import ForwardPipeline
from inoltro_email.state import ProcessedStore


@pytest.fixture
def store(tmp_path: Path) -> ProcessedStore:
    with ProcessedStore(tmp_path / "state.sqlite3") as instance:
        yield instance


def build_pipeline(settings: Settings, mail: FakeMailClient, ocr: FakeOcrClient,
                   store: ProcessedStore) -> ForwardPipeline:
    return ForwardPipeline(settings, mail, TextExtractor(settings, ocr), store)


def test_inoltra_quando_l_allegato_soddisfa_i_criteri(settings, store) -> None:
    message = FakeMessage(subject="Impegnativa", attachments={"referto.pdf": make_blank_pdf()})
    mail = FakeMailClient([message])
    ocr = FakeOcrClient(default_text="RICHIESTA TELEVISITA - prestazione 1501A")

    result = build_pipeline(settings, mail, ocr, store).process_message(message)

    assert result.decision is Decision.FORWARDED
    assert len(mail.forwarded) == 1
    assert mail.forwarded[0]["to"] == ["destinatario@example.com"]
    assert mail.forwarded[0]["prefix"] == "[TELEVISITA] "
    assert "referto.pdf" in mail.forwarded[0]["note"]
    assert mail.categories == ["Inoltrata"]


def test_non_inoltra_se_manca_il_codice(settings, store) -> None:
    message = FakeMessage(attachments={"referto.pdf": make_blank_pdf()})
    mail = FakeMailClient([message])
    ocr = FakeOcrClient(default_text="Richiesta di televisita, nessun codice indicato")

    result = build_pipeline(settings, mail, ocr, store).process_message(message)

    assert result.decision is Decision.NO_MATCH
    assert mail.forwarded == []
    assert result.match is not None and result.match.missing_codes == ["1501A"]


def test_non_inoltra_se_manca_la_parola(settings, store) -> None:
    message = FakeMessage(attachments={"referto.pdf": make_blank_pdf()})
    mail = FakeMailClient([message])
    ocr = FakeOcrClient(default_text="Prestazione 1501A erogata in presenza")

    result = build_pipeline(settings, mail, ocr, store).process_message(message)

    assert result.decision is Decision.NO_MATCH
    assert mail.forwarded == []


def test_dry_run_non_invia_nulla(settings, store) -> None:
    settings.forward.dry_run = True
    message = FakeMessage(attachments={"referto.pdf": make_blank_pdf()})
    mail = FakeMailClient([message])
    ocr = FakeOcrClient(default_text="TELEVISITA 1501A")

    result = build_pipeline(settings, mail, ocr, store).process_message(message)

    assert result.decision is Decision.FORWARDED_DRY_RUN
    assert mail.forwarded == []
    assert mail.categories == []


def test_messaggio_senza_allegati_saltato(settings, store) -> None:
    message = FakeMessage(attachments={})
    mail = FakeMailClient([message])
    ocr = FakeOcrClient()

    result = build_pipeline(settings, mail, ocr, store).process_message(message)

    assert result.decision is Decision.SKIPPED_NO_ATTACHMENT
    assert ocr.calls == []
    assert mail.forwarded == []


def test_nessun_doppio_inoltro_dello_stesso_messaggio(settings, store) -> None:
    """Le finestre di due controlli consecutivi si sovrappongono di proposito."""
    message = FakeMessage(attachments={"referto.pdf": make_blank_pdf()})
    mail = FakeMailClient([message])
    ocr = FakeOcrClient(default_text="TELEVISITA 1501A")
    pipeline = build_pipeline(settings, mail, ocr, store)

    first = pipeline.process_message(message)
    second = pipeline.process_message(message)

    assert first.decision is Decision.FORWARDED
    assert second.decision is Decision.SKIPPED_DUPLICATE
    assert len(mail.forwarded) == 1


def test_si_ferma_al_primo_allegato_conforme(settings, store) -> None:
    """Trovato il match, gli altri allegati non consumano quota OCR."""
    message = FakeMessage(attachments={
        "a_primo.pdf": make_blank_pdf(),
        "b_secondo.pdf": make_blank_pdf(),
        "c_terzo.pdf": make_blank_pdf(),
    })
    mail = FakeMailClient([message])
    ocr = FakeOcrClient(texts={"a_primo": "TELEVISITA 1501A"}, default_text="niente")

    result = build_pipeline(settings, mail, ocr, store).process_message(message)

    assert result.decision is Decision.FORWARDED
    assert result.matched_attachment == "a_primo.pdf"
    assert len(ocr.calls) == 1


def test_esamina_tutti_gli_allegati_finche_serve(settings, store) -> None:
    message = FakeMessage(attachments={
        "a_primo.pdf": make_blank_pdf(),
        "b_secondo.pdf": make_blank_pdf(),
    })
    mail = FakeMailClient([message])
    ocr = FakeOcrClient(texts={"b_secondo": "TELEVISITA 1501A"}, default_text="niente di rilevante")

    result = build_pipeline(settings, mail, ocr, store).process_message(message)

    assert result.decision is Decision.FORWARDED
    assert result.matched_attachment == "b_secondo.pdf"
    assert len(ocr.calls) == 2


def test_pdf_con_testo_riconosciuto_senza_ocr(settings, store) -> None:
    message = FakeMessage(attachments={
        "referto.pdf": make_pdf(["Richiesta TELEVISITA prestazione 1501A paziente Rossi"])
    })
    mail = FakeMailClient([message])
    ocr = FakeOcrClient()

    result = build_pipeline(settings, mail, ocr, store).process_message(message)

    assert result.decision is Decision.FORWARDED
    assert ocr.calls == []


def test_errore_ocr_non_blocca_il_servizio(settings, store) -> None:
    class BrokenOcr:
        def parse_file(self, path):
            raise OcrSpaceError("servizio non raggiungibile")

    message = FakeMessage(attachments={"referto.png": b"contenuto"})
    mail = FakeMailClient([message])
    pipeline = ForwardPipeline(settings, mail, TextExtractor(settings, BrokenOcr()), store)

    result = pipeline.process_message(message)

    assert result.decision is Decision.NO_MATCH
    assert mail.forwarded == []


def test_errore_su_outlook_libera_la_prenotazione(settings, store) -> None:
    """Dopo un guasto transitorio il messaggio dev'essere ritentabile."""
    class BrokenMail(FakeMailClient):
        def forward(self, *args, **kwargs):
            raise RuntimeError("Outlook non risponde")

    message = FakeMessage(attachments={"referto.pdf": make_blank_pdf()})
    mail = BrokenMail([message])
    ocr = FakeOcrClient(default_text="TELEVISITA 1501A")
    pipeline = build_pipeline(settings, mail, ocr, store)

    result = pipeline.process_message(message)

    assert result.decision is Decision.ERROR
    # La prenotazione e' stata sciolta: un nuovo tentativo non e' un duplicato.
    assert store.claim(result.message_key) is True


def test_process_entry_id_usa_il_client(settings, store) -> None:
    message = FakeMessage(entry_id="ENTRY-42", attachments={"r.pdf": make_blank_pdf()})
    mail = FakeMailClient([message])
    ocr = FakeOcrClient(default_text="TELEVISITA 1501A")
    pipeline = build_pipeline(settings, mail, ocr, store)

    assert pipeline.process_entry_id("ENTRY-42").decision is Decision.FORWARDED
    assert pipeline.process_entry_id("INESISTENTE") is None


def test_process_recent_elabora_tutti_i_messaggi(settings, store) -> None:
    messages = [
        FakeMessage(subject="Conforme", message_id="<a@x>", entry_id="E1",
                    attachments={"ok.pdf": make_blank_pdf()}),
        FakeMessage(subject="Non conforme", message_id="<b@x>", entry_id="E2",
                    attachments={"no.pdf": make_blank_pdf()}),
        FakeMessage(subject="Senza allegati", message_id="<c@x>", entry_id="E3"),
    ]
    mail = FakeMailClient(messages)
    ocr = FakeOcrClient(texts={"ok": "TELEVISITA 1501A"}, default_text="altro")

    results = build_pipeline(settings, mail, ocr, store).process_recent(30)

    assert [r.decision for r in results] == [
        Decision.FORWARDED, Decision.NO_MATCH, Decision.SKIPPED_NO_ATTACHMENT
    ]
    assert len(mail.forwarded) == 1


def test_process_recent_chiede_solo_i_non_letti(settings, store) -> None:
    """Il filtro sui messaggi da leggere viene girato al client di posta."""
    letto = FakeMessage(subject="Gia' letto", message_id="<a@x>", entry_id="E1",
                        attachments={"ok.pdf": make_blank_pdf()}, is_read=True)
    non_letto = FakeMessage(subject="Nuovo", message_id="<b@x>", entry_id="E2",
                            attachments={"ok.pdf": make_blank_pdf()})
    mail = FakeMailClient([letto, non_letto])
    ocr = FakeOcrClient(default_text="TELEVISITA 1501A")

    results = build_pipeline(settings, mail, ocr, store).process_recent(5)

    assert mail.queries == [{"minutes": 5, "unread_only": True}]
    assert [r.subject for r in results] == ["Nuovo"]
