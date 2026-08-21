"""Avvio del servizio con uvicorn.

Separato da ``app.py`` cosi' l'applicazione resta importabile (e collaudabile)
senza tirarsi dietro il server. In produzione si puo' anche lanciare
direttamente::

    uvicorn inoltro_email.api.app:build --factory --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ..config import Settings
from .app import create_app

logger = logging.getLogger(__name__)

import os

def build() -> "object":
    """Fabbrica per ``uvicorn --factory``: legge la configurazione da sola."""
    flow_path_env = os.environ.get("INOLTRO_EMAIL_FLOW_PATH")
    flow_path = Path(flow_path_env) if flow_path_env else None
    flow_timer = int(os.environ.get("INOLTRO_EMAIL_FLOW_TIMER", "60"))
    return create_app(flow_path=flow_path, flow_timer=flow_timer)


def run(
    settings: Optional[Settings] = None,
    *,
    reload: bool = False,
    flow_path: Optional[Path] = None,
    flow_timer: int = 60,
) -> None:
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
    if flow_path:
        logger.info(
            "Flusso Power Automate: '%s' ogni %d secondi.",
            flow_path, flow_timer,
        )

    app = create_app(settings, flow_path=flow_path, flow_timer=flow_timer)

    if reload:
        if flow_path:
            os.environ["INOLTRO_EMAIL_FLOW_PATH"] = str(flow_path.resolve())
            os.environ["INOLTRO_EMAIL_FLOW_TIMER"] = str(flow_timer)
        uvicorn.run(
            "inoltro_email.api.server:build",
            factory=True,
            host=settings.api.host,
            port=settings.api.port,
            reload=True,
        )
        return

    uvicorn.run(
        app,
        host=settings.api.host,
        port=settings.api.port,
        log_config=None,
    )
