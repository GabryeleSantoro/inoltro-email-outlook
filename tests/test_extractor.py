"""Test della scelta della strategia di lettura degli allegati."""

from __future__ import annotations

from pathlib import Path

from conftest import FakeOcrClient, make_blank_pdf, make_pdf

from inoltro_email.config import Settings
from inoltro_email.models import AttachmentFile, TextSource
from inoltro_email.ocr.extractor import TextExtractor
from inoltro_email.ocr.ocrspace import OcrSpaceError


def attachment_from(path: Path) -> AttachmentFile:
    return AttachmentFile(path=path, original_name=path.name, size_bytes=path.stat().st_size)


def test_pdf_con_testo_non_chiama_ocr(settings: Settings, tmp_path: Path) -> None:
    """Se il PDF ha gia' il testo, non si consuma quota ocr.space."""
    path = tmp_path / "referto.pdf"
    path.write_bytes(make_pdf(["Richiesta di TELEVISITA codice 1501A per paziente"]))
    ocr = FakeOcrClient()

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.PDF_TEXT
    assert "TELEVISITA" in result.text
    assert ocr.calls == []


def test_pdf_scansionato_passa_dall_ocr(settings: Settings, tmp_path: Path) -> None:
    path = tmp_path / "scansione.pdf"
    path.write_bytes(make_blank_pdf(pages=1))
    ocr = FakeOcrClient(default_text="TELEVISITA 1501A")

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.OCR
    assert result.text == "TELEVISITA 1501A"
    assert len(ocr.calls) == 1


def test_pdf_lungo_viene_spezzato_in_blocchi(settings: Settings, tmp_path: Path) -> None:
    """Oltre il limite di pagine del piano, il PDF va inviato a pezzi."""
    settings.ocr.max_pdf_pages_per_request = 3
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


def test_immagine_oltre_il_limite_dell_api_saltata(settings: Settings, tmp_path: Path) -> None:
    """Il limite di ocr.space e' piu' basso di quello degli allegati."""
    settings.ocr.max_file_bytes = 50
    settings.attachments.max_bytes = 10_000
    path = tmp_path / "grande.png"
    path.write_bytes(b"x" * 100)
    ocr = FakeOcrClient()

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.SKIPPED
    assert ocr.calls == []


def test_errore_ocr_non_solleva_ma_viene_registrato(settings: Settings, tmp_path: Path) -> None:
    class BrokenOcr:
        def parse_file(self, path):
            raise OcrSpaceError("quota giornaliera esaurita")

    path = tmp_path / "foto.png"
    path.write_bytes(b"contenuto")

    result = TextExtractor(settings, BrokenOcr()).extract(attachment_from(path))

    assert result.source is TextSource.ERROR
    assert not result.ok
    assert "quota" in (result.error or "")


def test_pdf_con_testo_insufficiente_ricade_su_ocr(settings: Settings, tmp_path: Path) -> None:
    """Poche lettere nel livello di testo = PDF scansionato con intestazione."""
    path = tmp_path / "quasi-vuoto.pdf"
    path.write_bytes(make_pdf(["Pag. 1"]))
    ocr = FakeOcrClient(default_text="TELEVISITA 1501A")

    result = TextExtractor(settings, ocr).extract(attachment_from(path))

    assert result.source is TextSource.OCR
    assert len(ocr.calls) == 1
