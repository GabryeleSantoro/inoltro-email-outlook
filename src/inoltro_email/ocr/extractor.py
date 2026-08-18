"""Estrazione del testo da un allegato.

Decide *come* leggere il file prima ancora di chiamare l'OCR:

1. PDF gia' provvisto di livello di testo -> lo legge con ``pypdf``, senza
   consumare quota ne' tempo di rete;
2. PDF scansionato -> lo manda a ocr.space, spezzandolo in blocchi di pagine
   quando supera i limiti del piano (dimensione o numero di pagine);
3. immagine -> la manda direttamente a ocr.space;
4. tutto il resto -> saltato, con il motivo tracciato nel risultato.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import List

from ..config import Settings
from ..models import AttachmentFile, ExtractedText, TextSource
from .ocrspace import OcrSpaceClient, OcrSpaceError

logger = logging.getLogger(__name__)

# Sotto questa soglia il livello di testo del PDF e' considerato inaffidabile
# (tipico dei PDF scansionati con solo l'intestazione vettoriale): si passa
# comunque all'OCR.
MIN_PDF_TEXT_CHARS = 40


class TextExtractor:
    """Ricava il testo di un allegato usando la strategia piu' economica."""

    def __init__(self, settings: Settings, ocr_client: OcrSpaceClient) -> None:
        self._settings = settings
        self._ocr = ocr_client

    def extract(self, attachment: AttachmentFile) -> ExtractedText:
        extension = attachment.extension

        if extension not in self._settings.attachments.allowed_extensions:
            return self._skip(attachment, f"estensione '{extension or 'assente'}' non ammessa")
        if attachment.size_bytes > self._settings.attachments.max_bytes:
            return self._skip(
                attachment,
                f"allegato troppo grande ({attachment.size_bytes} byte > "
                f"{self._settings.attachments.max_bytes} byte)",
            )

        try:
            if extension == ".pdf":
                return self._extract_pdf(attachment)
            return self._extract_image(attachment)
        except OcrSpaceError as exc:
            logger.error("OCR fallito su %s: %s", attachment.original_name, exc)
            return ExtractedText(attachment, "", TextSource.ERROR, str(exc))
        except Exception as exc:  # noqa: BLE001 - un allegato rotto non deve fermare il flusso
            logger.exception("Errore inatteso leggendo %s", attachment.original_name)
            return ExtractedText(attachment, "", TextSource.ERROR, str(exc))

    # ------------------------------------------------------------------ PDF

    def _extract_pdf(self, attachment: AttachmentFile) -> ExtractedText:
        embedded = self._read_pdf_text_layer(attachment.path)
        if len(embedded.strip()) >= MIN_PDF_TEXT_CHARS:
            logger.info(
                "%s: testo letto dal livello di testo del PDF (%d caratteri), OCR non necessario.",
                attachment.original_name, len(embedded),
            )
            return ExtractedText(attachment, embedded, TextSource.PDF_TEXT)

        logger.info("%s: PDF senza testo utile, invio a ocr.space.", attachment.original_name)
        limits = self._settings.ocr
        page_count = self._count_pdf_pages(attachment.path)
        too_many_pages = page_count > limits.max_pdf_pages_per_request
        too_big = attachment.size_bytes > limits.max_file_bytes

        if not too_many_pages and not too_big:
            return ExtractedText(attachment, self._ocr.parse_file(attachment.path).text, TextSource.OCR)

        logger.info(
            "%s: %d pagine / %d byte oltre i limiti dell'API, invio a blocchi di %d pagine.",
            attachment.original_name, page_count, attachment.size_bytes,
            limits.max_pdf_pages_per_request,
        )
        return ExtractedText(attachment, self._ocr_pdf_in_chunks(attachment), TextSource.OCR)

    def _ocr_pdf_in_chunks(self, attachment: AttachmentFile) -> str:
        """Spezza il PDF in blocchi di pagine e concatena i testi riconosciuti."""
        from pypdf import PdfReader, PdfWriter

        pages_per_chunk = self._settings.ocr.max_pdf_pages_per_request
        texts: List[str] = []

        # La cartella temporanea viene rimossa in ogni caso all'uscita dal with.
        with tempfile.TemporaryDirectory(prefix="inoltro-pdf-") as tmp_dir:
            reader = PdfReader(str(attachment.path))
            total = len(reader.pages)
            for start in range(0, total, pages_per_chunk):
                writer = PdfWriter()
                for index in range(start, min(start + pages_per_chunk, total)):
                    writer.add_page(reader.pages[index])

                chunk_path = Path(tmp_dir) / f"{attachment.path.stem}_p{start + 1}.pdf"
                with chunk_path.open("wb") as handle:
                    writer.write(handle)

                chunk_size = chunk_path.stat().st_size
                if chunk_size > self._settings.ocr.max_file_bytes:
                    logger.warning(
                        "%s: blocco pagine %d-%d ancora troppo grande (%d byte), saltato.",
                        attachment.original_name, start + 1,
                        min(start + pages_per_chunk, total), chunk_size,
                    )
                    continue

                try:
                    texts.append(self._ocr.parse_file(chunk_path).text)
                except OcrSpaceError as exc:
                    # Un blocco illeggibile non deve invalidare gli altri.
                    logger.warning("%s: blocco da pagina %d non elaborato: %s",
                                   attachment.original_name, start + 1, exc)

        if not texts:
            raise OcrSpaceError(f"{attachment.original_name}: nessun blocco del PDF e' stato elaborato.")
        return "\n".join(texts)

    @staticmethod
    def _read_pdf_text_layer(path: Path) -> str:
        from pypdf import PdfReader

        try:
            reader = PdfReader(str(path))
            if reader.is_encrypted:
                # I PDF protetti spesso si aprono con password vuota.
                try:
                    reader.decrypt("")
                except Exception:  # noqa: BLE001
                    logger.warning("%s: PDF cifrato, lettura del testo non possibile.", path.name)
                    return ""
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as exc:  # noqa: BLE001 - PDF malformato: si prova comunque con l'OCR
            logger.warning("%s: impossibile leggere il livello di testo (%s).", path.name, exc)
            return ""

    @staticmethod
    def _count_pdf_pages(path: Path) -> int:
        from pypdf import PdfReader

        try:
            return len(PdfReader(str(path)).pages)
        except Exception:  # noqa: BLE001
            return 1

    # --------------------------------------------------------------- immagini

    def _extract_image(self, attachment: AttachmentFile) -> ExtractedText:
        if attachment.size_bytes > self._settings.ocr.max_file_bytes:
            return self._skip(
                attachment,
                f"immagine di {attachment.size_bytes} byte oltre il limite di "
                f"{self._settings.ocr.max_file_bytes} byte accettato da ocr.space",
            )
        return ExtractedText(attachment, self._ocr.parse_file(attachment.path).text, TextSource.OCR)

    # ----------------------------------------------------------------- utili

    @staticmethod
    def _skip(attachment: AttachmentFile, reason: str) -> ExtractedText:
        logger.info("Allegato ignorato %s: %s", attachment.original_name, reason)
        return ExtractedText(attachment, "", TextSource.SKIPPED, reason)
