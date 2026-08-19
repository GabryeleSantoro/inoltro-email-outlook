"""Orchestrazione: dall'email ricevuta al verdetto restituito.

Il flusso, per ogni messaggio che arriva da Power Automate:

    screening su oggetto e corpo (telemedicina / televisita)
        -> OCR degli allegati e delle foto incorporate nel corpo
        -> verifica dei criteri sul testo letto (telemedicina + 1501A)
        -> punteggio di sentiment e di intento di prenotazione

Lo screening viene prima apposta: se l'email non parla di telemedicina non si
spende nemmeno una chiamata all'OCR. Il modulo non conosce HTTP: riceve un
``InboundEmail`` e restituisce un ``EmailAnalysis``, quindi e' interamente
collaudabile senza far partire il server.
"""

from __future__ import annotations

import logging
import re
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

from .config import Settings
from .matching import evaluate, screen
from .models import (
    AttachmentAnalysis, AttachmentFile, EmailAnalysis, Esito, InboundAttachment,
    InboundEmail, MatchReport, Origine, ScreeningReport, SentimentScore, TextSource,
)
from .ocr.extractor import TextExtractor
from .sentiment import analyze_sentiment

logger = logging.getLogger(__name__)

_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class EmailAnalyzer:
    """Applica screening, OCR, criteri e sentiment a una singola email."""

    def __init__(self, settings: Settings, extractor: TextExtractor) -> None:
        self._settings = settings
        self._extractor = extractor

    def analyze(self, email: InboundEmail) -> EmailAnalysis:
        """Analizza il messaggio e restituisce il verdetto completo.

        Non solleva mai: un messaggio problematico diventa un esito ``errore``
        con il motivo, cosi' il flusso Power Automate riceve sempre una
        risposta interpretabile.
        """
        started = time.monotonic()
        subject = email.subject or "(senza oggetto)"

        screening = screen(email.subject, email.body_text, self._settings.screening)
        logger.info(
            "Screening di '%s': %s (termini: %s)",
            subject,
            "superato" if screening.passed else "non superato",
            ", ".join(screening.terms) or "-",
        )

        if not screening.passed and self._settings.screening.stop_on_failure:
            return self._result(
                email, Esito.SCARTATA, screening,
                self._sentiment(email, attachment_matched=False),
                started=started,
            )

        try:
            analyses, match, matched_name = self._read_documents(email)
        except Exception as exc:  # noqa: BLE001 - il servizio deve rispondere comunque
            logger.exception("Analisi non riuscita per '%s'", subject)
            return self._result(
                email, Esito.ERRORE, screening,
                self._sentiment(email, attachment_matched=False),
                started=started, error=str(exc),
            )

        esito = _decide(analyses, match)
        sentiment = self._sentiment(email, attachment_matched=esito is Esito.CONFORME)
        logger.info(
            "Esito di '%s': %s (%s), sentiment %s, prenotazione %.2f",
            subject, esito.value, match.summary() if match else "nessun documento letto",
            sentiment.label, sentiment.booking.score,
        )
        return self._result(
            email, esito, screening, sentiment,
            started=started, attachments=analyses, match=match, matched_attachment=matched_name,
        )

    # ------------------------------------------------------ allegati e foto

    def _read_documents(
        self, email: InboundEmail
    ) -> Tuple[List[AttachmentAnalysis], Optional[MatchReport], Optional[str]]:
        """Legge allegati e foto del corpo finche' non trova un documento conforme."""
        candidates = self._select(email.attachments)
        if not candidates:
            logger.info("Nessun allegato o foto analizzabile in '%s'.", email.subject)
            return [], None, None

        analyses: List[AttachmentAnalysis] = []
        best: Optional[MatchReport] = None
        matched_name: Optional[str] = None

        # La cartella temporanea (e i file scritti) sparisce all'uscita dal with.
        with tempfile.TemporaryDirectory(prefix="telemedicina-") as tmp_dir:
            for index, item in enumerate(candidates, start=1):
                stored = _write_to_disk(item, Path(tmp_dir), index)
                extracted = self._extractor.extract(stored)

                report: Optional[MatchReport] = None
                if extracted.ok:
                    report = evaluate(extracted.text, self._settings.rules)
                    logger.info(
                        "%s '%s' (%s): %s -> %s",
                        item.origine.value, item.name, extracted.source.value,
                        report.summary(), "conforme" if report.matched else "non conforme",
                    )
                    if best is None or report.matched:
                        best = report

                analyses.append(
                    AttachmentAnalysis(
                        name=item.name,
                        origine=item.origine,
                        source=extracted.source,
                        chars=len(extracted.text),
                        match=report,
                        error=extracted.error,
                    )
                )

                if report is not None and report.matched:
                    matched_name = item.name
                    if not self._settings.attachments.analyze_all:
                        # Trovato: inutile spendere altre chiamate OCR.
                        break

        return analyses, best, matched_name

    def _select(self, attachments: List[InboundAttachment]) -> List[InboundAttachment]:
        """Scarta cio' che non si sa leggere e limita il numero di chiamate OCR."""
        limits = self._settings.attachments
        selected: List[InboundAttachment] = []

        for item in attachments:
            if item.origine is Origine.CORPO and not limits.include_inline_images:
                continue
            if item.extension not in limits.allowed_extensions:
                logger.debug("'%s' ignorato: estensione non ammessa.", item.name)
                continue
            if item.size_bytes > limits.max_bytes:
                logger.info("'%s' ignorato: %d byte oltre il limite.", item.name, item.size_bytes)
                continue
            if not item.content:
                continue
            selected.append(item)

        if len(selected) > limits.max_files:
            logger.warning(
                "%d file allegati, se ne analizzano i primi %d.", len(selected), limits.max_files
            )
            selected = selected[: limits.max_files]
        return selected

    # ------------------------------------------------------------- sentiment

    def _sentiment(self, email: InboundEmail, *, attachment_matched: bool) -> SentimentScore:
        return analyze_sentiment(
            email.screening_text,
            self._settings.sentiment,
            attachment_matched=attachment_matched,
        )

    # ----------------------------------------------------------------- utili

    @staticmethod
    def _result(
        email: InboundEmail,
        esito: Esito,
        screening: ScreeningReport,
        sentiment: SentimentScore,
        *,
        started: float,
        attachments: Optional[List[AttachmentAnalysis]] = None,
        match: Optional[MatchReport] = None,
        matched_attachment: Optional[str] = None,
        error: Optional[str] = None,
    ) -> EmailAnalysis:
        return EmailAnalysis(
            message_key=email.key,
            subject=email.subject,
            esito=esito,
            screening=screening,
            sentiment=sentiment,
            attachments=attachments or [],
            matched_attachment=matched_attachment,
            match=match,
            error=error,
            duration_ms=int((time.monotonic() - started) * 1000),
        )


def _decide(analyses: List[AttachmentAnalysis], match: Optional[MatchReport]) -> Esito:
    """Traduce l'esito della lettura dei documenti in un esito complessivo."""
    if not analyses:
        return Esito.SENZA_CONTENUTO
    if match is not None and match.matched:
        return Esito.CONFORME
    if all(item.source in (TextSource.SKIPPED, TextSource.ERROR) for item in analyses):
        # Nessun testo letto: non e' un "non conforme", e' un'analisi mancata.
        return Esito.SENZA_CONTENUTO
    return Esito.NON_CONFORME


def _write_to_disk(item: InboundAttachment, directory: Path, index: int) -> AttachmentFile:
    """Scrive l'allegato in una cartella temporanea, con un nome sicuro."""
    target = _unique_path(directory, _sanitize_filename(item.name, index))
    target.write_bytes(item.content)
    return AttachmentFile(
        path=target,
        original_name=item.name,
        size_bytes=item.size_bytes,
        origine=item.origine,
    )


def _sanitize_filename(name: str, index: int) -> str:
    """Ripulisce il nome fornito dal mittente prima di scriverlo su disco."""
    name = Path(name).name  # neutralizza eventuali percorsi ("../../x.pdf")
    name = _UNSAFE_FILENAME_CHARS.sub("_", name).strip(" .")
    if not name:
        name = f"allegato_{index}"
    return name[:120]


def _unique_path(directory: Path, filename: str) -> Path:
    """Evita che due allegati omonimi si sovrascrivano."""
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem, suffix = candidate.stem, candidate.suffix
    counter = 2
    while True:
        candidate = directory / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
