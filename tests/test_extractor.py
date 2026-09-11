"""Test della scelta della strategia di lettura degli allegati."""

from __future__ import annotations

from pathlib import Path

from conftest import FakeOcrClient, make_blank_pdf, make_pdf

from inoltro_email.config import Settings
from inoltro_email.models import AttachmentFile, TextSource
from inoltro_email.ocr.extractor import TextExtractor
from inoltro_email.ocr.paddle import OcrError


def attachment_from(path: Path) -> AttachmentFile:
    return AttachmentFile(path=path, original_name=path.name, size_bytes=path.stat().st_size)


def test_pdf_con_testo_letto_senza_ocr(settings: Settings, tmp_path: Path) -> None:
    """Prima si prova a leggere il PDF: se il testo c'e', non si chiama l'OCR."""
    path = tmp_path / "referto.pdf"
    path.write_bytes(make_pdf(["Richiesta di TELEVISITA codice 1501A per paziente"]))
    ocr = FakeOcrClient()

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.PDF_TEXT
    assert "TELEVISITA" in result.text
    assert ocr.calls == []


def test_pdf_con_poco_testo_ricade_sull_ocr(settings: Settings, tmp_path: Path) -> None:
    """Poche lettere sono il tipico PDF scansionato con la sola intestazione."""
    path = tmp_path / "scansione.pdf"
    path.write_bytes(make_pdf(["ASL"]))
    ocr = FakeOcrClient(default_text="TELEVISITA 1501A")

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.OCR
    assert ocr.calls == ["scansione.pdf"]


def test_pdf_illeggibile_va_all_ocr(settings: Settings, tmp_path: Path) -> None:
    """PDF malformato: pypdf non ne cava nulla, ci prova l'OCR."""
    path = tmp_path / "rotto.pdf"
    path.write_bytes(b"%PDF-1.4\nnon sono un pdf valido")
    ocr = FakeOcrClient(default_text="TELEVISITA 1501A")

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.OCR
    assert ocr.calls == ["rotto.pdf"]


def test_pdf_con_testo_unito_all_ocr_quando_richiesto(
    settings: Settings, tmp_path: Path
) -> None:
    settings.ocr.always_call = True
    path = tmp_path / "referto.pdf"
    path.write_bytes(make_pdf(["Richiesta di TELEVISITA codice 1501A per paziente"]))
    ocr = FakeOcrClient(default_text="timbro e firma del medico")

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.PDF_TEXT_OCR
    assert "TELEVISITA" in result.text
    assert "timbro e firma del medico" in result.text
    assert ocr.calls == ["referto.pdf"]


def test_pdf_scansionato_passa_dall_ocr(settings: Settings, tmp_path: Path) -> None:
    path = tmp_path / "scansione.pdf"
    path.write_bytes(make_blank_pdf(pages=1))
    ocr = FakeOcrClient(default_text="TELEVISITA 1501A")

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.OCR
    assert result.text == "TELEVISITA 1501A"
    assert len(ocr.calls) == 1


def test_pdf_lungo_viene_spezzato_in_blocchi(settings: Settings, tmp_path: Path) -> None:
    """PDF lungo: batch per RAM, tutte le pagine restano elaborate."""
    settings.ocr.pdf_pages_per_batch = 3
    path = tmp_path / "lungo.pdf"
    path.write_bytes(make_blank_pdf(pages=7))
    ocr = FakeOcrClient(default_text="parte")

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.OCR
    assert len(ocr.calls) == 3  # 7 pagine -> blocchi da 3, 3 e 1
    assert result.text.count("parte") == 3


def test_immagine_inviata_direttamente(settings: Settings, tmp_path: Path) -> None:
    path = tmp_path / "foto.jpg"
    path.write_bytes(b"contenuto-jpeg")
    ocr = FakeOcrClient(default_text="televisita 1501A")

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.OCR
    assert ocr.calls == ["foto.jpg"]


def test_estensione_non_ammessa_saltata(settings: Settings, tmp_path: Path) -> None:
    path = tmp_path / "archivio.zip"
    path.write_bytes(b"PK\x03\x04")
    ocr = FakeOcrClient()

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.SKIPPED
    assert "non ammessa" in (result.error or "")
    assert ocr.calls == []


def test_allegato_troppo_grande_saltato(settings: Settings, tmp_path: Path) -> None:
    settings.attachments.max_bytes = 10
    path = tmp_path / "grande.png"
    path.write_bytes(b"x" * 100)

    result = TextExtractor(settings, FakeOcrClient()).extract(attachment_from(path))

    assert result.source is TextSource.SKIPPED
    assert "troppo grande" in (result.error or "")


def test_errore_ocr_non_solleva_ma_viene_registrato(settings: Settings, tmp_path: Path) -> None:
    class BrokenOcr:
        def parse_file(self, path):
            raise OcrError("motore PaddleOCR non disponibile")

    path = tmp_path / "foto.png"
    path.write_bytes(b"contenuto")

    result = TextExtractor(settings, BrokenOcr()).extract(attachment_from(path))

    assert result.source is TextSource.ERROR
    assert not result.ok
    assert "PaddleOCR" in (result.error or "")


def test_pdf_con_testo_insufficiente_ricade_su_ocr(settings: Settings, tmp_path: Path) -> None:
    """Poche lettere nel livello di testo = PDF scansionato con intestazione."""
    path = tmp_path / "quasi-vuoto.pdf"
    path.write_bytes(make_pdf(["Pag. 1"]))
    ocr = FakeOcrClient(default_text="TELEVISITA 1501A")

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.OCR
    assert len(ocr.calls) == 1
