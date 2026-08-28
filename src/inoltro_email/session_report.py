"""Registro in memoria delle email gestite nella singola sessione HTTP."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from threading import Lock

from .models import EmailAnalysis, Esito, InboundEmail


@dataclass(frozen=True)
class SessionEmailRecord:
    """Una riga del riepilogo di una sessione del servizio."""

    stato: str
    message_key: str
    received_at: str
    subject: str
    reason: str = ""


class EmailSessionReport:
    """Raccoglie esiti HTTP e li stampa ordinati allo spegnimento dell'app."""

    def __init__(self) -> None:
        self._records: list[SessionEmailRecord] = []
        self._lock = Lock()

    def discarded(
        self,
        *,
        message_key: str,
        received_at: str,
        subject: str,
        reason: str,
    ) -> None:
        self._add("SCARTATA", message_key, received_at, subject, reason)

    def analyzed(self, email: InboundEmail, analysis: EmailAnalysis) -> SessionEmailRecord:
        """Registra una decisione completata e restituisce la riga creata."""
        if analysis.prenotazione_certa:
            state, reason = "DA_INOLTRARE", "prenotazione certa"
        elif analysis.esito is Esito.SCARTATA:
            terms = ", ".join(analysis.screening.terms) or "nessun termine"
            state, reason = "SCARTATA", f"screening non superato ({terms})"
        elif analysis.esito is Esito.SENZA_CONTENUTO:
            state, reason = "NON_INOLTRATA", "nessun documento leggibile"
        elif analysis.esito is Esito.ERRORE:
            state, reason = "NON_INOLTRATA", analysis.error or "errore di analisi"
        elif analysis.match and analysis.match.missing:
            missing = ", ".join(analysis.match.missing)
            state, reason = "NON_INOLTRATA", f"criteri mancanti: {missing}"
        else:
            state = "NON_INOLTRATA"
            reason = (
                "prenotazione non certa "
                f"(telemedicina {analysis.telemedicina.percent:.1f}%, "
                f"prenotazione {analysis.prenotazione.percent:.1f}%)"
            )
        return self._add(state, email.key, email.received_at, email.subject, reason)

    def log_summary(self, logger: logging.Logger) -> None:
        """Scrive un riepilogo leggibile anche quando il log contiene OCR verboso."""
        with self._lock:
            records = list(self._records)

        logger.info("===== RIEPILOGO EMAIL SESSIONE =====")
        if not records:
            logger.info("Nessuna email ricevuta dal flusso.")
            return

        labels = (
            ("DA_INOLTRARE", "EMAIL DA INOLTRARE"),
            ("NON_INOLTRATA", "EMAIL ANALIZZATE, NON INOLTRATE"),
            ("SCARTATA", "EMAIL SCARTATE"),
        )
        for state, label in labels:
            selected = [item for item in records if item.stato == state]
            logger.info("%s: %d", label, len(selected))
            for item in selected:
                detail = f" | motivo={item.reason}" if item.reason else ""
                logger.info(
                    "  - id=%s | ricevuta_il=%s | oggetto='%s'%s",
                    item.message_key or "(senza id)",
                    item.received_at or "(data assente)",
                    item.subject or "(senza oggetto)",
                    detail,
                )

        discarded = [item for item in records if item.stato == "SCARTATA"]
        if discarded:
            logger.info("MOTIVI DI SCARTO:")
            for reason, count in Counter(item.reason for item in discarded).most_common():
                logger.info("  - %s: %d", reason, count)
        logger.info(
            "TOTALI | ricevute=%d | da_inoltrare=%d | non_inoltrate=%d | scartate=%d",
            len(records),
            sum(item.stato == "DA_INOLTRARE" for item in records),
            sum(item.stato == "NON_INOLTRATA" for item in records),
            len(discarded),
        )

    def _add(
        self, state: str, message_key: str, received_at: str, subject: str, reason: str
    ) -> SessionEmailRecord:
        record = SessionEmailRecord(state, message_key, received_at, subject, reason)
        with self._lock:
            self._records.append(record)
        return record
