"""Applicazione HTTP (FastAPI) interrogata da Power Automate.

Un solo endpoint fa il lavoro: ``POST /analizza-email`` riceve una singola
email in JSON, la analizza e restituisce il verdetto. Il flusso Power Automate
usa l'azione "HTTP", passa il messaggio appena arrivato e poi decide cosa fare
(inoltrare, aprire un ticket, ignorare) leggendo i campi della risposta.

Il client verso ocr.space viene creato una volta sola all'avvio e chiuso allo
spegnimento: cosi' la connessione TLS si riusa fra una richiesta e l'altra.
L'analisi e' sincrona (l'OCR e' una chiamata di rete bloccante), quindi viene
eseguita nel pool di thread di Starlette e non blocca il ciclo di eventi.
"""

from __future__ import annotations

import hmac
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .. import __version__
from ..analysis import EmailAnalyzer
from ..config import Settings
from ..inbound import InboundError, parse_email
from ..ocr.extractor import TextExtractor
from ..ocr.ocrspace import OcrSpaceClient
from .responses import analysis_to_dict

logger = logging.getLogger(__name__)

API_KEY_HEADER = "X-API-Key"
# 413: il nome della costante e' cambiato fra le versioni di Starlette.
RICHIESTA_TROPPO_GRANDE = 413

RICHIESTA_ESEMPIO = {
    "id": "AAMkAGI2...",
    "internetMessageId": "<0123@example.com>",
    "subject": "Richiesta prenotazione televisita",
    "from": "paziente@example.com",
    "receivedDateTime": "2026-08-19T08:00:00Z",
    "isHtml": True,
    "body": "<p>Buongiorno, vorrei prenotare una televisita. "
            "In allegato l'impegnativa. Grazie.</p>",
    "attachments": [
        {
            "name": "impegnativa.pdf",
            "contentType": "application/pdf",
            "isInline": False,
            "contentBytes": "JVBERi0xLjQK...(base64)",
        }
    ],
}


def _payload_to_log(payload: Any) -> str:
    """Serializza un payload in modo robusto per il logging di debug."""
    try:
        return json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    except Exception:  # noqa: BLE001 - non deve mai bloccare la gestione richiesta
        return repr(payload)


def create_app(
    settings: Optional[Settings] = None,
    *,
    analyzer: Optional[EmailAnalyzer] = None,
) -> FastAPI:
    """Costruisce l'applicazione.

    ``analyzer`` si passa solo nei test, per evitare chiamate reali a ocr.space.
    """
    settings = settings or Settings.load()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        owned_client: Optional[OcrSpaceClient] = None
        if analyzer is None:
            owned_client = OcrSpaceClient(settings.ocr)
            application.state.analyzer = EmailAnalyzer(
                settings, TextExtractor(settings, owned_client)
            )
        else:
            application.state.analyzer = analyzer
        logger.info(
            "Servizio pronto: screening su %s, criteri sul contenuto %s.",
            " / ".join(settings.screening.keywords),
            " + ".join(settings.rules.keywords + settings.rules.codes),
        )
        try:
            yield
        finally:
            if owned_client is not None:
                owned_client.close()

    app = FastAPI(
        title=settings.api.title,
        version=__version__,
        description=(
            "Analizza una singola email inoltrata da Power Automate: verifica "
            "telemedicina/televisita in oggetto e corpo, legge allegati e foto "
            "con l'OCR cercando i criteri configurati e calcola il punteggio di "
            "sentiment e di intento di prenotazione."
        ),
        lifespan=lifespan,
    )
    app.state.settings = settings

    # ------------------------------------------------------------ endpoint

    @app.get("/", tags=["servizio"], summary="Informazioni sul servizio")
    def informazioni() -> dict:
        return {
            "servizio": settings.api.title,
            "versione": __version__,
            "analisi": "/analizza-email",
            "documentazione": "/docs",
        }

    @app.post("/", tags=["servizio"], summary="Endpoint errato")
    def endpoint_errato_root_post() -> JSONResponse:
        """Aiuta a diagnosticare integrazioni che postano sul percorso sbagliato."""
        logger.warning(
            "Richiesta ricevuta su POST /. Endpoint corretto: POST /analizza-email"
        )
        return JSONResponse(
            {
                "errore": "Endpoint errato: usare POST /analizza-email.",
                "codice": status.HTTP_405_METHOD_NOT_ALLOWED,
                "endpoint_corretto": "/analizza-email",
            },
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @app.get("/salute", tags=["servizio"], summary="Controllo di funzionamento")
    def salute() -> dict:
        """Sonda leggera per bilanciatori e monitoraggi: non chiama l'OCR."""
        return {
            "stato": "ok",
            "versione": __version__,
            "ocr_configurato": bool(settings.ocr.api_key),
            "chiave_richiesta": bool(settings.api.api_key),
        }

    @app.post(
        "/analizza-email",
        tags=["analisi"],
        summary="Analizza una singola email letta da Power Automate",
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"type": "object"},
                        "example": RICHIESTA_ESEMPIO,
                    }
                },
            }
        },
    )
    async def analizza_email(
        request: Request,
        x_api_key: Optional[str] = Header(default=None, alias=API_KEY_HEADER),
    ) -> JSONResponse:
        _check_api_key(settings, x_api_key)
        payload = await _read_json(request, settings.api.max_request_bytes)

        try:
            email = parse_email(
                payload,
                include_inline_images=settings.attachments.include_inline_images,
                max_attachment_bytes=settings.attachments.max_bytes,
            )
        except InboundError as exc:
            logger.error(
                "Payload non interpretabile: %s\nPayload completo:\n%s",
                exc,
                _payload_to_log(payload),
            )
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        logger.info(
            "Richiesta di analisi: '%s' da %s, %d file.",
            email.subject or "(senza oggetto)", email.sender or "mittente ignoto",
            len(email.attachments),
        )
        analysis = await run_in_threadpool(request.app.state.analyzer.analyze, email)
        return JSONResponse(analysis_to_dict(analysis))

    @app.exception_handler(HTTPException)
    async def _errore_http(_request: Request, exc: HTTPException) -> JSONResponse:
        """Errori con lo stesso involucro della risposta buona."""
        return JSONResponse(
            {"errore": exc.detail, "codice": exc.status_code},
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
        )

    return app


# --------------------------------------------------------------------- utili


def _check_api_key(settings: Settings, provided: Optional[str]) -> None:
    """Confronto della chiave condivisa con Power Automate."""
    expected = settings.api.api_key
    if not expected:
        return  # nessuna chiave configurata: controllo disattivato
    if not provided or not _constant_time_equals(provided.strip(), expected):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=f"Chiave mancante o errata nell'header {API_KEY_HEADER}.",
        )


def _constant_time_equals(left: str, right: str) -> bool:
    """Confronto a tempo costante: non rivela quanti caratteri combaciano."""
    return hmac.compare_digest(left, right)


async def _read_json(request: Request, max_bytes: int) -> Any:
    """Legge il corpo della richiesta rispettando il limite configurato."""
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > max_bytes:
        raise HTTPException(
            RICHIESTA_TROPPO_GRANDE,
            detail=f"Richiesta troppo grande: massimo {max_bytes} byte.",
        )

    raw = await request.body()
    if len(raw) > max_bytes:
        raise HTTPException(
            RICHIESTA_TROPPO_GRANDE,
            detail=f"Richiesta troppo grande: massimo {max_bytes} byte.",
        )
    if not raw.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Corpo della richiesta vuoto.")

    try:
        return json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raw_text = raw.decode("utf-8", errors="replace")
        logger.error(
            "JSON non valido: %s\nPayload completo (raw):\n%s",
            exc,
            raw_text,
        )
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=f"JSON non valido: {exc}"
        ) from exc
