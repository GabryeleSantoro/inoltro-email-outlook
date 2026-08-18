"""Orchestrazione: da un messaggio in arrivo alla decisione di inoltro.

Il flusso, per ogni messaggio:

    prenota (anti-duplicato) -> salva allegati -> estrai testo -> confronta
    con le regole -> inoltra (o simula) -> registra l'esito

Questo modulo non conosce Microsoft Graph: dipende solo dai Protocol di
``outlook.protocol``, quindi e' interamente collaudabile con un client fittizio
e senza rete.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import List, Optional

from .config import Settings
from .matching import evaluate
from .models import Decision, ExtractedText, MatchReport, ProcessResult
from .ocr.extractor import TextExtractor
from .outlook.protocol import MailClient, MailMessage
from .state import ProcessedStore

logger = logging.getLogger(__name__)


class ForwardPipeline:
    """Applica le regole di inoltro a un messaggio per volta."""

    def __init__(
        self,
        settings: Settings,
        mail_client: MailClient,
        extractor: TextExtractor,
        store: ProcessedStore,
    ) -> None:
        self._settings = settings
        self._mail = mail_client
        self._extractor = extractor
        self._store = store

    # ------------------------------------------------------------- ingressi

    def process_entry_id(self, entry_id: str) -> Optional[ProcessResult]:
        """Elabora un singolo messaggio indicato dal suo identificativo."""
        message = self._mail.get_message(entry_id)
        if message is None:
            return None
        return self.process_message(message)

    def process_recent(self, minutes: int, unread_only: bool = True) -> List[ProcessResult]:
        """Elabora i messaggi recenti (un giro di controllo o l'esecuzione singola)."""
        results: List[ProcessResult] = []
        for message in self._mail.recent_messages(minutes, unread_only=unread_only):
            result = self.process_message(message)
            if result is not None:
                results.append(result)
        return results

    # -------------------------------------------------------------- il cuore

    def process_message(self, message: MailMessage) -> ProcessResult:
        """Elabora un messaggio e restituisce l'esito.

        Non solleva mai eccezioni: un singolo messaggio problematico non deve
        fermare il servizio che resta in ascolto.
        """
        key = message_key(message)
        subject = message.subject or "(senza oggetto)"

        if not self._store.claim(key, message.entry_id, subject):
            logger.info("Gia' elaborato, salto: '%s'", subject)
            return ProcessResult(key, subject, Decision.SKIPPED_DUPLICATE)

        try:
            result = self._evaluate_and_forward(message, key, subject)
        except Exception as exc:  # noqa: BLE001 - il servizio deve restare in piedi
            logger.exception("Errore elaborando '%s'", subject)
            # La prenotazione viene sciolta: alla prossima occasione si riprova.
            self._store.release(key)
            return ProcessResult(key, subject, Decision.ERROR, error=str(exc))

        matched_terms = ""
        if result.match:
            matched_terms = ", ".join(result.match.found_keywords + result.match.found_codes)
        self._store.finalize(key, result.decision, matched_terms)
        return result

    def _evaluate_and_forward(self, message: MailMessage, key: str, subject: str) -> ProcessResult:
        if not message.has_attachments:
            logger.info("Nessun allegato, salto: '%s'", subject)
            return ProcessResult(key, subject, Decision.SKIPPED_NO_ATTACHMENT)

        extractions: List[ExtractedText] = []
        match: Optional[MatchReport] = None
        matched_attachment: Optional[str] = None

        # La cartella temporanea (e gli allegati salvati) sparisce all'uscita.
        with tempfile.TemporaryDirectory(prefix="inoltro-allegati-") as tmp_dir:
            attachments = self._mail.save_attachments(message, Path(tmp_dir))
            if not attachments:
                logger.info("Nessun allegato analizzabile, salto: '%s'", subject)
                return ProcessResult(key, subject, Decision.SKIPPED_NO_ATTACHMENT)

            for attachment in attachments:
                extracted = self._extractor.extract(attachment)
                extractions.append(extracted)
                if not extracted.ok:
                    continue

                report = evaluate(extracted.text, self._settings.rules)
                logger.info(
                    "Allegato '%s' (%s): %s -> %s",
                    attachment.original_name, extracted.source.value,
                    report.summary(), "CONFORME" if report.matched else "non conforme",
                )
                if match is None or report.matched:
                    match = report
                if report.matched:
                    # Trovato: inutile spendere altre chiamate OCR sugli altri file.
                    matched_attachment = attachment.original_name
                    break

        if match is None or not match.matched:
            logger.info("Criteri non soddisfatti, nessun inoltro: '%s'", subject)
            return ProcessResult(key, subject, Decision.NO_MATCH, match, extractions=extractions)

        decision = self._do_forward(message, subject, match, matched_attachment)
        return ProcessResult(key, subject, decision, match, matched_attachment, extractions=extractions)

    def _do_forward(
        self,
        message: MailMessage,
        subject: str,
        match: MatchReport,
        matched_attachment: Optional[str],
    ) -> Decision:
        forward_settings = self._settings.forward
        recipients = ", ".join(forward_settings.to)

        if forward_settings.dry_run:
            logger.warning(
                "[DRY-RUN] '%s' sarebbe stato inoltrato a %s (allegato '%s', %s). "
                "Impostare forward.dry_run: false per inviare davvero.",
                subject, recipients, matched_attachment, match.summary(),
            )
            return Decision.FORWARDED_DRY_RUN

        note = _build_note(forward_settings.body_note, match, matched_attachment)
        self._mail.forward(
            message,
            forward_settings.to,
            forward_settings.cc,
            forward_settings.subject_prefix,
            note,
        )
        self._mail.mark_processed(message, self._settings.outlook.processed_category)
        logger.info("Inoltrato '%s' a %s (allegato '%s').", subject, recipients, matched_attachment)
        return Decision.FORWARDED


def message_key(message: MailMessage) -> str:
    """Chiave anti-duplicato del messaggio.

    Si preferisce l'Internet Message-ID perche' resta valido anche se il
    messaggio viene spostato di cartella o se il programma viene riavviato;
    l'identificativo Graph e' il ripiego quando non e' disponibile.
    """
    return (message.message_id or "").strip() or f"entryid:{message.entry_id}"


def _build_note(base_note: str, match: MatchReport, matched_attachment: Optional[str]) -> str:
    """Compone la nota premessa al corpo dell'inoltro."""
    lines = [base_note] if base_note else []
    terms = ", ".join(match.found_keywords + match.found_codes)
    if terms:
        lines.append(f"Criteri riconosciuti: {terms}")
    if matched_attachment:
        lines.append(f"Allegato analizzato: {matched_attachment}")
    return "\r\n".join(lines)
