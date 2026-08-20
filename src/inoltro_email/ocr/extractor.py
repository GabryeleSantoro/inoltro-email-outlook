"""Estrazione del testo da un allegato.

Si legge sempre il modo piu' diretto per primo, e si va all'OCR solo quando
serve davvero:

1. **PDF** -> si prova a leggerlo con ``pypdf``. Se il livello di testo c'e' ed
   e' utilizzabile, quello e' il testo del documento: esatto, immediato e senza
   consumare quota. All'OCR ci si va solo quando la lettura non riesce (PDF
   cifrato, malformato) o non produce testo utile perche' il PDF e' una
   scansione. Il PDF che finisce all'OCR viene spezzato in blocchi di pagine se
   supera i limiti del piano;
2. **immagine** -> a ocr.space; se supera il limite di dimensione viene
   **ridimensionata** invece che saltata (vedi ``images.py``);
3. **tutto il resto** -> non arriva nemmeno qui: fogli di calcolo, documenti
   Word e GIF sono esclusi a monte (vedi ``config.FORMATI_SUPPORTATI``).

Con ``ocr.always_call: true`` anche i PDF gia' leggibili passano dall'OCR e i
due testi vengono uniti: piu' dati - dentro un PDF nativo puo' esserci una
scansione incollata - al prezzo di una chiamata per ogni documento.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import List

from ..config import Settings
from ..models import AttachmentFile, ExtractedText, TextSource
from .images import ImageError, riduci_sotto
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
        ha_testo = len(embedded.strip()) >= MIN_PDF_TEXT_CHARS

        if ha_testo and not self._settings.ocr.always_call:
            logger.info(
                "%s: letto direttamente dal PDF (%d caratteri), nessuna chiamata all'OCR.",
                attachment.original_name, len(embedded),
            )
            return ExtractedText(attachment, embedded, TextSource.PDF_TEXT)

        if not ha_testo:
            logger.info(
                "%s: il PDF non ha un livello di testo utilizzabile, si passa all'OCR.",
                attachment.original_name,
            )

        try:
            letto_dall_ocr = self._ocr_pdf(attachment)
        except OcrSpaceError:
            if not ha_testo:
                raise
            # L'OCR non ha funzionato ma il PDF il suo testo ce l'ha: si usa
            # quello invece di far fallire l'analisi del documento.
            logger.warning(
                "%s: OCR non riuscito, si usa il solo livello di testo del PDF.",
                attachment.original_name,
            )
            return ExtractedText(attachment, embedded, TextSource.PDF_TEXT)

        if not ha_testo:
            return ExtractedText(attachment, letto_dall_ocr, TextSource.OCR)

        logger.info(
            "%s: uniti livello di testo del PDF (%d caratteri) e lettura OCR (%d caratteri).",
            attachment.original_name, len(embedded), len(letto_dall_ocr),
        )
        return ExtractedText(
            attachment, f"{embedded}\n{letto_dall_ocr}", TextSource.PDF_TEXT_OCR
        )

    def _ocr_pdf(self, attachment: AttachmentFile) -> str:
        """Manda il PDF a ocr.space, a blocchi se supera i limiti del piano."""
        limits = self._settings.ocr
        page_count = self._count_pdf_pages(attachment.path)
        too_many_pages = page_count > limits.max_pdf_pages_per_request
        too_big = attachment.size_bytes > limits.max_file_bytes

        if not too_many_pages and not too_big:
            return self._ocr.parse_file(attachment.path).text

        logger.info(
            "%s: %d pagine / %d byte oltre i limiti dell'API, invio a blocchi di %d pagine.",
            attachment.original_name, page_count, attachment.size_bytes,
            limits.max_pdf_pages_per_request,
        )
        return self._ocr_pdf_in_chunks(attachment)

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
        limite = self._settings.ocr.max_file_bytes
        if attachment.size_bytes <= limite or not self._settings.ocr.resize_oversized_images:
            if attachment.size_bytes > limite:
                return self._skip(
                    attachment,
                    f"immagine di {attachment.size_bytes} byte oltre il limite di "
                    f"{limite} byte accettato da ocr.space "
                    "(ridimensionamento disattivato)",
                )
            return ExtractedText(
                attachment, self._ocr.parse_file(attachment.path).text, TextSource.OCR
            )

        # Una foto di impegnativa scattata col telefono supera sempre il MB:
        # si rimpicciolisce quanto basta invece di rinunciare a leggerla.
        with tempfile.TemporaryDirectory(prefix="inoltro-img-") as tmp_dir:
            lavoro = Path(tmp_dir) / attachment.path.stem
            try:
                ridotta, nota = riduci_sotto(attachment.path, limite, lavoro)
            except ImageError as exc:
                return self._skip(attachment, f"immagine troppo grande e non riducibile: {exc}")
            testo = self._ocr.parse_file(ridotta).text

        return ExtractedText(attachment, testo, TextSource.OCR, note=nota)

    # ----------------------------------------------------------------- utili

    @staticmethod
    def _skip(attachment: AttachmentFile, reason: str) -> ExtractedText:
        logger.info("Allegato ignorato %s: %s", attachment.original_name, reason)
        return ExtractedText(attachment, "", TextSource.SKIPPED, reason)
