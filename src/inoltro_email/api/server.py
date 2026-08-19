"""Avvio del servizio con uvicorn.

Separato da ``app.py`` cosi' l'applicazione resta importabile (e collaudabile)
senza tirarsi dietro il server. In produzione si puo' anche lanciare
direttamente::

    uvicorn inoltro_email.api.app:build --factory --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
from typing import Optional

from ..config import Settings
from .app import create_app

logger = logging.getLogger(__name__)


def build() -> "object":
    """Fabbrica per ``uvicorn --factory``: legge la configurazione da sola."""
    return create_app()


def run(settings: Optional[Settings] = None, *, reload: bool = False) -> None:
    """Avvia il server HTTP (bloccante) fino a Ctrl+C."""
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - dipendenza dichiarata
        raise SystemExit(
            "uvicorn non installato: eseguire 'pip install -r requirements.txt'."
        ) from exc

    settings = settings or Settings.load()
    logger.info(
        "Servizio in ascolto su http://%s:%d (documentazione su /docs).",
        settings.api.host, settings.api.port,
    )
    if reload:
        # Con il ricaricamento automatico uvicorn deve poter reimportare
        # l'applicazione: si passa il percorso della fabbrica, non l'oggetto.
        uvicorn.run(
            "inoltro_email.api.server:build",
            factory=True,
            host=settings.api.host,
            port=settings.api.port,
            reload=True,
        )
        return

    uvicorn.run(
        create_app(settings),
        host=settings.api.host,
        port=settings.api.port,
        log_config=None,  # il logging e' gia' configurato da logging_setup
    )
