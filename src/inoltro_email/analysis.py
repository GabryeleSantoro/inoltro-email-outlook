"""Orchestrazione: dall'email ricevuta al verdetto restituito.

Il flusso, per ogni messaggio che arriva da Power Automate:

    screening su oggetto e corpo (telemedicina / televisita)
        -> percentuale di sicurezza "e' telemedicina?" prima dell'OCR
        -> OCR degli allegati e delle foto incorporate nel corpo
        -> verifica dei criteri sul testo letto (telemedicina + 1501A)
        -> percentuali definitive: telemedicina e prenotazione di telemedicina
        -> punteggio di sentiment

La sicurezza si calcola due volte apposta. La prima, su oggetto, corpo e nomi
dei file, decide se vale la pena spendere una chiamata all'OCR: una newsletter
o un foglio di accessi mensili che nomina la telemedicina di sfuggita si ferma
qui. La seconda tiene conto anche di cio' che l'OCR ha letto negli allegati,
che e' l'indizio piu' concreto di tutti.

Il modulo non conosce HTTP: riceve un ``InboundEmail`` e restituisce un
``EmailAnalysis``, quindi e' interamente collaudabile senza far partire il
server.
"""

from __future__ import annotations

import logging
import re
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

from .config import Settings
from .confidence import score_booking, score_telemedicine
from .matching import evaluate, screen
from .models import (
    AttachmentAnalysis, AttachmentFile, ConfidenceScore, EmailAnalysis, Esito,
    InboundAttachment, InboundEmail, MatchReport, Origine, ScreeningReport,
    SentimentScore, TextSource,
)
from .ocr.extractor import TextExtractor
from .sentiment import analyze_sentiment

logger = logging.getLogger(__name__)

_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_BODY_PREVIEW_CHARS = 4000


def _clip(text: str, limit: int) -> str:
    """Restituisce un'anteprima dei log senza allagare console/file."""
    clean = text.strip()
    if len(clean) <= limit:
        return clean
    return f"{clean[:limit]}... [troncato, totale={len(clean)} caratteri]"


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
        self._log_inbound_email(email)

        screening = screen(email.subject, email.body_text, self._settings.screening)
        logger.info(
            "Screening di '%s': %s (termini: %s)",
            subject,
            "superato" if screening.passed else "non superato",
            ", ".join(screening.terms) or "-",
        )

        # Prima stima, senza OCR: serve a decidere se spendere una chiamata.
        preliminary = self._telemedicine_confidence(email)
        logger.info(
            "Sicurezza telemedicina di '%s' prima dell'OCR: %s [%s]",
            subject, preliminary.summary(), _describe(preliminary),
        )

        discard_reason = self._reason_to_discard(screening, preliminary)
        if discard_reason:
            logger.info("'%s' non passa alla lettura degli allegati: %s", subject, discard_reason)
            return self._result(
                email, Esito.SCARTATA, screening,
                self._sentiment(email, attachment_matched=False),
                telemedicina=preliminary,
                prenotazione=self._booking_confidence(email, preliminary),
                started=started,
            )

        try:
            analyses, match, matched_name, text_read = self._read_documents(email)
        except Exception as exc:  # noqa: BLE001 - il servizio deve rispondere comunque
            logger.exception("Analisi non riuscita per '%s'", subject)
            return self._result(
                email, Esito.ERRORE, screening,
                self._sentiment(email, attachment_matched=False),
                telemedicina=preliminary,
                prenotazione=self._booking_confidence(email, preliminary),
                started=started, error=str(exc),
            )

        esito = _decide(analyses, match)
        conforme = esito is Esito.CONFORME
        sentiment = self._sentiment(email, attachment_matched=conforme)

        # Punteggi definitivi: ora si sa anche cosa c'era negli allegati.
        telemedicina = self._telemedicine_confidence(
            email, document_text=text_read, document_matched=conforme
        )
        prenotazione = self._booking_confidence(
            email, telemedicina, document_text=text_read, document_matched=conforme
        )

        logger.info(
            "Esito di '%s': %s (%s), telemedicina %s, prenotazione %s, sentiment %s",
            subject, esito.value, match.summary() if match else "nessun documento letto",
            telemedicina.summary(), prenotazione.summary(), sentiment.label,
        )
        logger.info(
            "Indizi di prenotazione per '%s': %s", subject, _describe(prenotazione)
        )
        return self._result(
            email, esito, screening, sentiment,
            telemedicina=telemedicina, prenotazione=prenotazione,
            started=started, attachments=analyses, match=match, matched_attachment=matched_name,
        )

    def _reason_to_discard(
        self, screening: ScreeningReport, preliminary: ConfidenceScore
    ) -> Optional[str]:
        """Motivo per non leggere gli allegati, oppure None per proseguire."""
        if not self._settings.screening.stop_on_failure:
            return None
        if not screening.passed:
            return "oggetto e corpo non parlano di telemedicina"
        minimum = self._settings.confidence.min_percent_for_ocr
        if preliminary.percent < minimum:
            return (
                f"sicurezza telemedicina {preliminary.percent:.1f}% sotto il minimo "
                f"del {minimum:.0f}% richiesto per chiamare l'OCR"
            )
        return None

    def _log_inbound_email(self, email: InboundEmail) -> None:
        """Logga il contenuto in ingresso per facilitare il debug del flusso."""
        logger.info(
            "Email ricevuta: id=%s da=%s ricevuta_il=%s oggetto='%s'",
            email.key,
            email.sender or "mittente ignoto",
            email.received_at or "sconosciuta",
            email.subject or "(senza oggetto)",
        )

        if email.body_text.strip():
            logger.info(
                "Corpo testo (%d caratteri): %s",
                len(email.body_text),
                _clip(email.body_text, _BODY_PREVIEW_CHARS),
            )
            logger.debug("Corpo testo completo:\n%s", email.body_text)
        else:
            logger.info("Corpo testo vuoto.")

        if email.body_html.strip():
            logger.debug(
                "Corpo HTML (%d caratteri):\n%s",
                len(email.body_html),
                email.body_html,
            )

        if not email.attachments:
            logger.info("Nessun allegato nel payload.")
            return

        logger.info("Allegati ricevuti: %d", len(email.attachments))
        for index, item in enumerate(email.attachments, start=1):
            logger.info(
                "Allegato %d: nome='%s' origine=%s tipo=%s dimensione=%d byte provenienza=%s",
                index,
                item.name,
                item.origine.value,
                item.content_type or "sconosciuto",
                item.size_bytes,
                item.source_path if item.source_path is not None else "payload (base64)",
            )

    # ------------------------------------------------------ allegati e foto

    def _read_documents(
        self, email: InboundEmail
    ) -> Tuple[List[AttachmentAnalysis], Optional[MatchReport], Optional[str], str]:
        """Legge allegati e foto del corpo finche' non trova un documento conforme.

        Restituisce anche il testo complessivamente letto: entra nel calcolo
        della sicurezza, non solo nella verifica dei criteri.
        """
        candidates = self._select(email.attachments)
        if not candidates:
            logger.info("Nessun allegato o foto analizzabile in '%s'.", email.subject)
            return [], None, None, ""

        analyses: List[AttachmentAnalysis] = []
        best: Optional[MatchReport] = None
        matched_name: Optional[str] = None
        texts: List[str] = []

        # La cartella temporanea (e i file scritti) sparisce all'uscita dal with.
        with tempfile.TemporaryDirectory(prefix="telemedicina-") as tmp_dir:
            for index, item in enumerate(candidates, start=1):
                stored = _write_to_disk(item, Path(tmp_dir), index)
                extracted = self._extractor.extract(stored)

                report: Optional[MatchReport] = None
                if extracted.ok:
                    texts.append(extracted.text)
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

        return analyses, best, matched_name, "\n".join(texts)

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
            if not item.has_content:
                logger.info("'%s' ignorato: nessun contenuto leggibile.", item.name)
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

    # ------------------------------------------------- percentuali di sicurezza

    def _telemedicine_confidence(
        self,
        email: InboundEmail,
        *,
        document_text: str = "",
        document_matched: bool = False,
    ) -> ConfidenceScore:
        return score_telemedicine(
            email.subject,
            email.body_text,
            self._settings.confidence,
            attachment_names=[item.name for item in email.attachments],
            document_text=document_text,
            document_matched=document_matched,
        )

    def _booking_confidence(
        self,
        email: InboundEmail,
        telemedicina: ConfidenceScore,
        *,
        document_text: str = "",
        document_matched: bool = False,
    ) -> ConfidenceScore:
        return score_booking(
            email.subject,
            email.body_text,
            self._settings.confidence,
            telemedicine=telemedicina,
            document_text=document_text,
            document_matched=document_matched,
        )

    # ----------------------------------------------------------------- utili

    @staticmethod
    def _result(
        email: InboundEmail,
        esito: Esito,
        screening: ScreeningReport,
        sentiment: SentimentScore,
        *,
        telemedicina: ConfidenceScore,
        prenotazione: ConfidenceScore,
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
            telemedicina=telemedicina,
            prenotazione=prenotazione,
            attachments=attachments or [],
            matched_attachment=matched_attachment,
            match=match,
            error=error,
            warnings=list(email.warnings),
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


def _describe(score: ConfidenceScore) -> str:
    """Indizi del punteggio in una riga, per il log."""
    parts = [f"{item.label} ({item.where}) {item.weight:+.2f}" for item in score.evidence]
    return "; ".join(parts) or "nessun indizio"


def _write_to_disk(item: InboundAttachment, directory: Path, index: int) -> AttachmentFile:
    """Rende l'allegato un file su disco, pronto per l'OCR.

    Se il payload ne ha indicato il percorso il file c'e' gia': si usa dov'e'
    (e non lo si tocca), invece di ricopiarlo nella cartella temporanea.
    """
    if item.source_path is not None and item.source_path.is_file():
        return AttachmentFile(
            path=item.source_path,
            original_name=item.name,
            size_bytes=item.size_bytes,
            origine=item.origine,
        )

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
