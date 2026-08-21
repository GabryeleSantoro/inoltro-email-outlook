"""Esecuzione periodica di un flusso Power Automate.

Il flusso viene avviato come scorciatoia (.lnk) sul desktop di Windows.
Il modulo gestisce l'avvio periodico con un timer configurabile.

Se ``auto_continue`` e' attivo, dopo l'avvio il modulo cerca
automaticamente il popup di conferma di PAD e clicca "Continue"
disabilitando temporaneamente l'input utente.
"""

from __future__ import annotations

import logging
import platform
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FlowRunner:
    """Esegue un flusso Power Automate periodicamente."""

    def __init__(
        self,
        flow_path: Path,
        interval_seconds: int,
        *,
        auto_continue: bool = True,
        popup_title: str = "Power Automate",
        popup_button: str = "Continue",
        popup_timeout: float = 10.0,
    ) -> None:
        self.flow_path = flow_path
        self.interval_seconds = interval_seconds
        self.auto_continue = auto_continue
        self.popup_title = popup_title
        self.popup_button = popup_button
        self.popup_timeout = popup_timeout
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
        """Esegue il flusso Power Automate aprendo la scorciatoia.

        Se ``auto_continue`` e' True, dopo l'avvio cerca il popup di
        conferma e clicca "Continue" con focus lock.
        """
        try:
            logger.info("Esecuzione flusso: %s", self.flow_path)
            system = platform.system()

            if system == "Windows":
                import os
                if self.flow_path.suffix.lower() == ".url":
                    import configparser
                    config = configparser.ConfigParser(interpolation=None)
                    config.read(self.flow_path, encoding="utf-8")
                    try:
                        url = config.get("InternetShortcut", "URL")
                        os.startfile(url)
                    except (configparser.NoSectionError, configparser.NoOptionError):
                        os.startfile(str(self.flow_path))
                else:
                    os.startfile(str(self.flow_path))
            elif system == "Linux":
                subprocess.Popen(
                    ["cmd.exe", "/c", "start", "", str(self.flow_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                logger.error(
                    "Sistema operativo non supportato per l'esecuzione del flusso: %s",
                    system,
                )
                return

            logger.info("Flusso avviato con successo: %s", self.flow_path)

            if self.auto_continue and platform.system() == "Windows":
                self._click_continue()

        except Exception:
            logger.exception("Errore durante l'esecuzione del flusso: %s", self.flow_path)

    def _click_continue(self) -> None:
        """Cerca il popup di conferma PAD e clicca 'Continue'.

        Il blocco input e' attivo solo durante il click (pochi ms).
        """
        try:
            from .popup_clicker import click_continue

            # Breve attesa iniziale: il popup appare dopo qualche secondo
            time.sleep(1.0)

            ok = click_continue(
                title=self.popup_title,
                button_text=self.popup_button,
                timeout=self.popup_timeout,
            )
            if ok:
                logger.info("Popup 'Continue' cliccato con successo.")
            else:
                logger.warning(
                    "Popup '%s' non trovato o click fallito "
                    "(timeout=%.0fs).", self.popup_button, self.popup_timeout,
                )
        except ImportError:
            logger.warning(
                "pywinauto non installato: auto_continue disabilitato. "
                "Installare con: pip install pywinauto"
            )
        except Exception:
            logger.exception("Errore durante il click sul popup.")
