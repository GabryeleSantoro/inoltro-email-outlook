"""Controllo periodico della casella.

Senza Outlook Desktop non esiste l'evento ``NewMailEx``: i nuovi messaggi si
scoprono interrogando Microsoft Graph a intervalli regolari. Ogni giro chiede
soltanto i messaggi *non letti* ricevuti negli ultimi ``lookback_minutes``
minuti, quindi il traffico e' minimo anche su caselle affollate.

Due accortezze:

* il ciclo non deve mai morire: un errore di rete o un token temporaneamente
  rifiutato vengono registrati nel log e si riprova al giro successivo;
* se un giro dura piu' dell'intervallo (molti allegati da passare all'OCR), la
  finestra del giro seguente viene allargata al tempo realmente trascorso, cosi'
  nessun messaggio cade nel buco fra due controlli.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Callable, List, Optional

from ..config import Settings
from ..models import ProcessResult
from ..pipeline import ForwardPipeline

logger = logging.getLogger(__name__)

SECONDS_PER_MINUTE = 60


class MailPoller:
    """Interroga la casella a intervalli regolari e passa tutto alla pipeline."""

    def __init__(
        self,
        settings: Settings,
        pipeline: ForwardPipeline,
        *,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._settings = settings
        self._pipeline = pipeline
        self._sleep = sleeper
        self._clock = clock
        self._interval = max(1, settings.outlook.poll_interval_minutes) * SECONDS_PER_MINUTE
        self._last_cycle_started: Optional[float] = None

    # ------------------------------------------------------------------ ciclo

    def run(self, max_cycles: Optional[int] = None) -> None:
        """Esegue i controlli finche' non arriva Ctrl+C (o per ``max_cycles`` giri)."""
        outlook = self._settings.outlook
        if self._settings.forward.dry_run:
            logger.warning("Modalita' DRY-RUN attiva: nessun messaggio verra' realmente inoltrato.")
        logger.info(
            "Controllo della posta ogni %d minuti (finestra %d minuti, %s). Ctrl+C per terminare.",
            outlook.poll_interval_minutes,
            outlook.lookback_minutes,
            "solo messaggi non letti" if outlook.unread_only else "letti e non letti",
        )

        # Primo giro: recupera anche cio' che e' arrivato a programma spento.
        window = max(outlook.catch_up_minutes, outlook.lookback_minutes)
        cycles = 0
        while max_cycles is None or cycles < max_cycles:
            started = self._clock()
            self.poll_once(window)
            cycles += 1
            self._last_cycle_started = started

            if max_cycles is not None and cycles >= max_cycles:
                break
            self._sleep(self._time_to_next_cycle(started))
            window = self._window_minutes()

    def poll_once(self, minutes: Optional[int] = None) -> List[ProcessResult]:
        """Un singolo controllo: non solleva mai, cosi' il ciclo prosegue."""
        window = minutes if minutes is not None else self._window_minutes()
        try:
            results = self._pipeline.process_recent(
                window, unread_only=self._settings.outlook.unread_only
            )
        except Exception as exc:  # noqa: BLE001 - il servizio deve restare in piedi
            logger.exception("Controllo della posta non riuscito, si riprova fra poco: %s", exc)
            return []

        forwarded = sum(1 for result in results if result.forwarded)
        if results:
            logger.info("Controllo concluso: %d messaggi esaminati, %d inoltrati.",
                        len(results), forwarded)
        else:
            logger.debug("Controllo concluso: nessun messaggio nuovo.")
        return results

    # ------------------------------------------------------------- tempistica

    def _time_to_next_cycle(self, cycle_started: float) -> float:
        """Attesa residua perche' i giri partano ogni ``interval`` secondi esatti."""
        elapsed = self._clock() - cycle_started
        if elapsed >= self._interval:
            logger.warning(
                "Il controllo ha richiesto %.0f secondi, piu' dell'intervallo di %d: "
                "il prossimo giro parte subito.", elapsed, self._interval,
            )
            return 0.0
        return self._interval - elapsed

    def _window_minutes(self) -> int:
        """Minuti da esaminare: almeno la finestra configurata.

        Se il giro precedente e' durato piu' del previsto la finestra si allarga
        al tempo davvero trascorso: meglio riesaminare qualche messaggio gia'
        visto (il registro anti-duplicato li scarta) che perderne uno.
        """
        window = self._settings.outlook.lookback_minutes
        if self._last_cycle_started is None:
            return window
        elapsed_minutes = (self._clock() - self._last_cycle_started) / SECONDS_PER_MINUTE
        return max(window, int(math.ceil(elapsed_minutes)))


def watch(settings: Settings, pipeline: ForwardPipeline) -> None:
    """Avvia il controllo periodico (bloccante) fino a Ctrl+C."""
    poller = MailPoller(settings, pipeline)
    try:
        poller.run()
    except KeyboardInterrupt:
        logger.info("Interruzione richiesta, chiusura in corso.")
