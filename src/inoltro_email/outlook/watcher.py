"""Ascolto degli arrivi in Outlook tramite l'evento ``NewMailEx``.

``NewMailEx`` scatta appena Outlook deposita un messaggio nella Posta in
arrivo e passa gli EntryID separati da virgola. E' l'attivazione "vera" al
momento dell'arrivo, senza polling.

Due accortezze imparate dall'uso di COM:

* un'eccezione sollevata dentro un gestore di evento fa cadere l'intero
  message pump, quindi ogni EntryID viene elaborato in un ``try/except``;
* gli eventi arrivano solo mentre ``PumpMessages()` e' in esecuzione: cio' che
  arriva a programma spento si recupera con la scansione iniziale.
"""

from __future__ import annotations

import logging
from typing import Optional

from ..config import Settings
from ..pipeline import ForwardPipeline
from .client import OutlookError

logger = logging.getLogger(__name__)

# Il gestore di eventi viene istanziato da pywin32, che non ci lascia passare
# argomenti al costruttore: la pipeline si condivide tramite questa variabile.
_ACTIVE_PIPELINE: Optional[ForwardPipeline] = None


class NewMailHandler:
    """Gestore degli eventi di Outlook.Application.

    Usato con ``DispatchWithEvents``: pywin32 costruisce una classe che unisce
    l'oggetto COM a questa, e invoca ``OnNewMailEx`` a ogni consegna.
    """

    def OnNewMailEx(self, entry_id_collection: str) -> None:  # noqa: N802 - nome imposto da COM
        if _ACTIVE_PIPELINE is None:
            logger.error("Evento ricevuto ma nessuna pipeline attiva.")
            return

        for entry_id in str(entry_id_collection or "").split(","):
            entry_id = entry_id.strip()
            if not entry_id:
                continue
            try:
                result = _ACTIVE_PIPELINE.process_entry_id(entry_id)
                if result is not None:
                    logger.info("Esito per '%s': %s", result.subject, result.decision.value)
            except Exception:  # noqa: BLE001 - non deve mai propagare nel pump COM
                logger.exception("Errore elaborando l'EntryID %s", entry_id)


def watch(settings: Settings, pipeline: ForwardPipeline) -> None:
    """Avvia il ciclo di ascolto (bloccante) fino a Ctrl+C."""
    global _ACTIVE_PIPELINE

    try:
        import pythoncom  # noqa: PLC0415
        import win32com.client  # noqa: PLC0415
    except ImportError as exc:
        raise OutlookError(
            "pywin32 non disponibile: la modalita' 'watch' richiede Windows con "
            "Outlook Desktop (pip install pywin32)."
        ) from exc

    _ACTIVE_PIPELINE = pipeline

    # Recupera cio' che e' arrivato mentre il programma non era in ascolto.
    if settings.outlook.catch_up_minutes > 0:
        logger.info("Recupero dei messaggi degli ultimi %d minuti...", settings.outlook.catch_up_minutes)
        pipeline.process_recent(settings.outlook.catch_up_minutes)

    # DispatchWithEvents crea una connessione ad Outlook agganciata al gestore.
    # Il riferimento va tenuto vivo per tutta la durata dell'ascolto: se l'oggetto
    # venisse raccolto dal garbage collector, gli eventi smetterebbero di arrivare
    # senza alcun errore visibile.
    application = win32com.client.DispatchWithEvents("Outlook.Application", NewMailHandler)

    if settings.forward.dry_run:
        logger.warning("Modalita' DRY-RUN attiva: nessun messaggio verra' realmente inoltrato.")
    logger.info("In ascolto di nuovi messaggi. Premere Ctrl+C per terminare.")

    try:
        pythoncom.PumpMessages()
    except KeyboardInterrupt:
        logger.info("Interruzione richiesta, chiusura in corso.")
    finally:
        del application  # rilascia l'aggancio agli eventi
        _ACTIVE_PIPELINE = None
