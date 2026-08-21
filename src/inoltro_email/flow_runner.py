"""Esecuzione periodica di un flusso Power Automate.

Il flusso viene avviato come scorciatoia (.lnk) sul desktop di Windows.
Il modulo gestisce l'avvio periodico con un timer configurabile.
"""

from __future__ import annotations

import logging
import platform
import subprocess
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FlowRunner:
    """Esegue un flusso Power Automate periodicamente."""

    def __init__(
        self,
        flow_path: Path,
        interval_seconds: int,
    ) -> None:
        self.flow_path = flow_path
        self.interval_seconds = interval_seconds
        self._timer: Optional[threading.Timer] = None
        self._running = False

    def start(self) -> None:
        """Avvia l'esecuzione periodica del flusso."""
        if self._running:
            logger.warning("FlowRunner gia' in esecuzione.")
            return

        if not self.flow_path.exists():
            logger.error("File del flusso non trovato: %s", self.flow_path)
            return

        self._running = True
        logger.info(
            "FlowRunner avviato: eseguo '%s' ogni %d secondi.",
            self.flow_path, self.interval_seconds,
        )
        self._schedule_next()

    def stop(self) -> None:
        """Ferma l'esecuzione periodica."""
        self._running = False
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        logger.info("FlowRunner fermato.")

    def _schedule_next(self) -> None:
        if not self._running:
            return
        self._timer = threading.Timer(self.interval_seconds, self._execute_and_reschedule)
        self._timer.daemon = True
        self._timer.start()

    def _execute_and_reschedule(self) -> None:
        self._execute_flow()
        self._schedule_next()

    def _execute_flow(self) -> None:
        """Esegue il flusso Power Automate aprendo la scorciatoia."""
        try:
            logger.info("Esecuzione flusso: %s", self.flow_path)
            system = platform.system()

            if system == "Windows":
                import os
                os.startfile(str(self.flow_path))
            elif system == "Linux":
                subprocess.Popen(
                    ["cmd.exe", "/c", "start", "", str(self.flow_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                logger.error("Sistema operativo non supportato per l'esecuzione del flusso: %s", system)
                return

            logger.info("Flusso avviato con successo: %s", self.flow_path)
        except Exception:
            logger.exception("Errore durante l'esecuzione del flusso: %s", self.flow_path)
