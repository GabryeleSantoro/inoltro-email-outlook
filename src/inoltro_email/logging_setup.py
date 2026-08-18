"""Configurazione del logging: console + file rotante."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)-28s %(message)s"
MAX_BYTES = 2_000_000
BACKUP_COUNT = 5


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """Installa gli handler sul logger radice (idempotente)."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(LOG_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    # urllib3 logga ogni connessione a livello DEBUG: troppo rumoroso.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
