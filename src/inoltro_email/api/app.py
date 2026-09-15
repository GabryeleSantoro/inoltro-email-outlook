"""Applicazione HTTP (FastAPI) interrogata da Power Automate.

``POST /analizza-email`` riceve una singola email in JSON e restituisce il
verdetto, ma salta screening e OCR se il messaggio e' gia' nel registro.
``POST /registra-email`` riceve lo stesso payload, ma registra solo che il
flusso ha gia' gestito il messaggio.

Il motore PaddleOCR viene creato una volta sola all'avvio. L'analisi resta
sincrona e viene eseguita nel pool di thread di Starlette; il client serializza
le inferenze per non saturare la CPU del server.
"""

from __future__ import annotations

import hmac
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List, Mapping, Optional, Tuple

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .. import __version__
from ..analysis import EmailAnalyzer
from ..config import Settings
from ..flow_runner import FlowRunner
from ..inbound import InboundError, parse_email
from ..message_guard import LocalMessageStore
from ..models import InboundEmail
from ..ocr.extractor import TextExtractor
from ..ocr.paddle import PaddleOcrClient
from ..rawjson import RawJsonError, loads_tolerant
from ..session_report import EmailSessionReport
from .responses import analysis_to_dict

logger = logging.getLogger(__name__)

API_KEY_HEADER = "X-API-Key"
# 413: il nome della costante e' cambiato fra le versioni di Starlette.
RICHIESTA_TROPPO_GRANDE = 413

# Codici con cui il servizio risponde a un'analisi riuscita.
#
# 200 = e' una prenotazione di telemedicina, con la sicurezza necessaria per
#       agire senza che una persona guardi il messaggio;
# 202 = messaggio analizzato correttamente, ma non e' una prenotazione (o non
#       lo e' abbastanza da esserne certi).
#
# Sono due codici 2xx apposta. Power Automate considera *fallita* l'azione HTTP
# davanti a un 4xx: il flusso finirebbe in errore e, con i tentativi automatici
# attivi, rianalizzerebbe lo stesso messaggio consumando altra CPU. "Non
# e' una prenotazione" e' un esito legittimo dell'analisi, non un errore della
# richiesta. Entrambe le risposte portano il verdetto completo nel corpo.
ANALISI_CERTA = 200
ANALISI_SENZA_PRENOTAZIONE = 202
MESSAGGIO_IGNORATO = 202
MESSAGGIO_REGISTRATO = 201
MOTIVO_SENZA_ALLEGATI = "senza_allegati"
DESTINATARIO_ESCLUSO_DALL_INOLTRO = "telemedicina.prenota@aslsalerno.it"
MOTIVO_DESTINATARIO_ESCLUSO = "destinatario_telemedicina_prenota"
DEFAULT_MESSAGE_STORE_PATH = Path("data") / "checked_messages.sqlite3"
_CONTENT_BYTES_LOG_PREVIEW_CHARS = 80
_BODY_LOG_PREVIEW_CHARS = 80

# Il flusso in produzione manda gli allegati come percorsi su disco: la forma
# e' diversa da quella del connettore Outlook, il servizio le accetta entrambe.
RICHIESTA_ESEMPIO_PERCORSI = {
    "subject": "R: Agende telemedicina DSB 68 - ORTOPEDIA",
    "body": "<html><body><p>Si invia l'impegnativa per la televisita.</p></body></html>",
    "date": "08/20/2026 10:26",
    "attchment": "C:\\Users\\user\\Documents\\Power Automate\\Allegati\\image.png",
}

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
    """Serializza il payload senza riversare base64 e corpo completi nei log."""
    try:
        return json.dumps(
            _truncate_content_bytes(payload),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    except Exception:  # noqa: BLE001 - non deve mai bloccare la gestione richiesta
        return repr(payload)


def _truncate_content_bytes(value: Any) -> Any:
    """Copia ricorsivamente il payload, abbreviando i campi voluminosi nei log."""
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            if str(key).casefold() in {"contentbytes", "contentbyte"}:
                result[key] = _truncate_base64_for_log(item)
            elif str(key).casefold() == "body":
                result[key] = _truncate_body_for_log(item)
            else:
                result[key] = _truncate_content_bytes(item)
        return result
    if isinstance(value, list):
        return [_truncate_content_bytes(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_truncate_content_bytes(item) for item in value)
    return value


def _truncate_base64_for_log(value: Any) -> Any:
    return _truncate_string_for_log(value, _CONTENT_BYTES_LOG_PREVIEW_CHARS)


def _truncate_body_for_log(value: Any) -> Any:
    return _truncate_string_for_log(value, _BODY_LOG_PREVIEW_CHARS)


def _truncate_string_for_log(value: Any, limit: int) -> Any:
    if not isinstance(value, str) or len(value) <= limit:
        return value
    return f"{value[:limit]}... [troncato, totale={len(value)} caratteri]"


def create_app(
    settings: Optional[Settings] = None,
    *,
    analyzer: Optional[EmailAnalyzer] = None,
    flow_path: Optional[Path] = None,
    flow_timer: int = 60,
    skip_confirmation: bool = False,
    message_store_path: Optional[Path] = None,
    dev_mode: bool = False,
) -> FastAPI:
    """Costruisce l'applicazione.

    ``analyzer`` si passa solo nei test, per evitare il caricamento dei modelli.
    """
    settings = settings or Settings.load()
    if flow_timer <= 0:
        raise ValueError("flow_timer deve essere maggiore di zero.")
    store_path = message_store_path or DEFAULT_MESSAGE_STORE_PATH

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        owned_client: Optional[PaddleOcrClient] = None
        if analyzer is None:
            owned_client = PaddleOcrClient(settings.ocr)
            application.state.analyzer = EmailAnalyzer(
                settings, TextExtractor(settings, owned_client)
            )
        else:
            application.state.analyzer = analyzer
        application.state.message_store = None if dev_mode else LocalMessageStore(store_path)
        application.state.email_session_report = EmailSessionReport()

        flow_runner: Optional[FlowRunner] = None
        if flow_path:
            flow_runner = FlowRunner(
                flow_path=flow_path,
                interval_seconds=flow_timer,
                auto_continue=(
                    settings.flow_popup.auto_continue and not skip_confirmation
                ),
                popup_title=settings.flow_popup.popup_title,
                popup_button=settings.flow_popup.popup_button,
                popup_timeout=settings.flow_popup.popup_timeout,
            )
            flow_runner.start()
            application.state.flow_runner = flow_runner

        logger.info(
            "Servizio pronto: screening su %s, criteri sul contenuto %s.",
            " / ".join(settings.screening.keywords),
            " + ".join(settings.rules.keywords + settings.rules.codes),
        )
        logger.info(
            "Sicurezza: telemedicina dal %.0f%%, prenotazione dal %.0f%%, "
            "OCR solo sopra il %.0f%%.",
            settings.confidence.telemedicine_threshold,
            settings.confidence.booking_threshold,
            settings.confidence.min_percent_for_ocr,
        )
        if dev_mode:
            logger.warning(
                "Modalita' --dev attiva: controllo duplicati e registrazione email disattivati."
            )
        if settings.local_files.enabled and not settings.local_files.allowed_directories:
            logger.warning(
                "Allegati per percorso attivi senza 'local_files.allowed_directories': "
                "qualunque file del disco con estensione ammessa puo' essere letto dal "
                "motore OCR locale. Se il servizio non e' solo in locale, indicare "
                "le cartelle consentite."
            )
        try:
            yield
        finally:
            application.state.email_session_report.log_summary(logger)
            if flow_runner is not None:
                flow_runner.stop()
            if owned_client is not None:
                owned_client.close()

    app = FastAPI(
        title=settings.api.title,
        version=__version__,
        description=(
            "Analizza una singola email inoltrata da Power Automate: verifica "
            "telemedicina/televisita in oggetto e corpo, legge PDF e immagini "
            "cercando i criteri configurati e calcola le percentuali di "
            "sicurezza. Risponde 200 quando e' certamente una prenotazione di "
            "telemedicina, 202 in tutti gli altri casi analizzati."
        ),
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.dev_mode = dev_mode

    # ------------------------------------------------------------ endpoint

    @app.get("/", tags=["servizio"], summary="Informazioni sul servizio")
    def informazioni() -> dict:
        return {
            "servizio": settings.api.title,
            "versione": __version__,
            "analisi": "/analizza-email",
            "registro": "/registra-email",
            "modalita_sviluppo": dev_mode,
            "documentazione": "/docs",
        }

    @app.post("/", tags=["servizio"], summary="Endpoint errato")
    def endpoint_errato_root_post() -> JSONResponse:
        """Aiuta a diagnosticare integrazioni che postano sul percorso sbagliato."""
        logger.warning(
            "Richiesta ricevuta su POST /. Endpoint corretti: "
            "POST /analizza-email oppure POST /registra-email"
        )
        return JSONResponse(
            {
                "errore": "Endpoint errato: usare POST /analizza-email oppure POST /registra-email.",
                "codice": status.HTTP_405_METHOD_NOT_ALLOWED,
                "endpoint_analisi": "/analizza-email",
                "endpoint_registro": "/registra-email",
            },
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @app.get("/salute", tags=["servizio"], summary="Controllo di funzionamento")
    def salute() -> dict:
        """Sonda leggera per bilanciatori e monitoraggi: non chiama l'OCR."""
        return {
            "stato": "ok",
            "versione": __version__,
            "ocr_backend": "paddleocr",
            "ocr_device": settings.ocr.device,
            "ocr_configurato": True,
            "chiave_richiesta": bool(settings.api.api_key),
            "modalita_sviluppo": dev_mode,
        }

    @app.post(
        "/analizza-email",
        tags=["analisi"],
        summary="Analizza una singola email letta da Power Automate",
        responses={
            ANALISI_CERTA: {
                "description": "E' una prenotazione di telemedicina: sicurezza "
                               "oltre la soglia di certezza configurata.",
            },
            ANALISI_SENZA_PRENOTAZIONE: {
                "description": "Messaggio analizzato: non e' una prenotazione di "
                               "telemedicina, o non lo e' con sicurezza sufficiente. "
                               "Include anche una prenotazione certa il cui inoltro "
                               "e' bloccato dal destinatario. "
                               "Il verdetto completo e' nel corpo della risposta.",
            },
        },
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"type": "object"},
                        "example": RICHIESTA_ESEMPIO,
                        "examples": {
                            "allegati_in_base64": {"value": RICHIESTA_ESEMPIO},
                            "allegati_per_percorso": {"value": RICHIESTA_ESEMPIO_PERCORSI},
                        },
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
        email, payload, repairs = await _read_email_request(request, settings)

        if repairs:
            # Il payload e' stato accettato ma era da riparare: chi legge la
            # risposta deve poterlo sapere e correggere il flusso a monte.
            email.warnings.append(
                "JSON non valido riparato in lettura: " + "; ".join(repairs)
            )

        # Senza un allegato non c'e' documentazione da verificare. Il motivo
        # stabile permette al flusso di predisporre in futuro un autoreply che
        # chieda la ricetta, senza inviare alcun messaggio da questo servizio.
        if not email.attachments:
            return _without_attachments_response(request, email)

        # Il flusso registra il messaggio soltanto dopo aver completato le
        # proprie azioni. Ai tentativi successivi il controllo deve stare qui,
        # prima dell'OCR e prima di qualunque risposta 200.
        if not dev_mode and request.app.state.message_store.contains(payload):
            logger.info("Email gia' analizzata: %s. OCR non avviato.", email.key)
            return JSONResponse(
                _ignored_message(email.key, email.subject, "gia_analizzata"),
                status_code=MESSAGGIO_IGNORATO,
            )

        analysis = await run_in_threadpool(request.app.state.analyzer.analyze, email)

        forwarding_block_reason = _forwarding_block_reason(email)
        inoltrabile = forwarding_block_reason is None
        stato = (
            ANALISI_CERTA
            if analysis.prenotazione_certa and inoltrabile
            else ANALISI_SENZA_PRENOTAZIONE
        )
        session_record = request.app.state.email_session_report.analyzed(
            email,
            analysis,
            forwarding_block_reason=forwarding_block_reason or "",
        )
        if analysis.esito.value == "scartata":
            logger.info(
                "EMAIL SCARTATA | motivo=screening | id=%s | ricevuta_il=%s | oggetto='%s'",
                email.key, email.received_at, email.subject or "(senza oggetto)",
            )
        elif session_record.stato == "DA_INOLTRARE":
            logger.info(
                "EMAIL DA INOLTRARE | id=%s | ricevuta_il=%s | oggetto='%s' | motivo=%s",
                email.key, email.received_at, email.subject or "(senza oggetto)",
                session_record.reason,
            )
        else:
            logger.info(
                "EMAIL NON INOLTRATA | id=%s | ricevuta_il=%s | oggetto='%s' | motivo=%s",
                email.key, email.received_at, email.subject or "(senza oggetto)",
                session_record.reason,
            )
        logger.info(
            "EMAIL ANALIZZATA | id=%s | ricevuta_il=%s | esito=%s | http=%d | durata_ms=%d",
            email.key, email.received_at, analysis.esito.value, stato, analysis.duration_ms,
        )
        logger.info(
            "Risposta %d per '%s': telemedicina %s, prenotazione %s (soglia di certezza %.0f%%).",
            stato, email.subject or "(senza oggetto)",
            analysis.telemedicina.summary(), analysis.prenotazione.summary(),
            settings.confidence.certainty_threshold,
        )
        return JSONResponse(
            analysis_to_dict(
                analysis,
                include_text=settings.attachments.return_text,
                max_text_chars=settings.attachments.max_text_chars,
                tos=email.tos,
                ccs=email.ccs,
                inoltrabile=inoltrabile,
                motivo_non_inoltro=forwarding_block_reason,
            ),
            status_code=stato,
        )

    @app.post(
        "/registra-email",
        tags=["registro"],
        summary="Registra un messaggio gia' gestito dal flusso",
        status_code=MESSAGGIO_REGISTRATO,
        responses={
            MESSAGGIO_REGISTRATO: {
                "description": "Messaggio registrato: le chiamate successive con lo "
                               "stesso messaggio saranno riconosciute come duplicate.",
            },
            MESSAGGIO_IGNORATO: {
                "description": "Messaggio gia' registrato, oppure registrazione "
                               "saltata in modalita' --dev.",
            },
        },
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"type": "object"},
                        "example": RICHIESTA_ESEMPIO,
                        "examples": {
                            "allegati_in_base64": {"value": RICHIESTA_ESEMPIO},
                            "allegati_per_percorso": {"value": RICHIESTA_ESEMPIO_PERCORSI},
                        },
                    }
                },
            }
        },
    )
    async def registra_email(
        request: Request,
        x_api_key: Optional[str] = Header(default=None, alias=API_KEY_HEADER),
    ) -> JSONResponse:
        """Marca un payload come gestito senza svolgere analisi o OCR."""
        _check_api_key(settings, x_api_key)
        email, payload, repairs = await _read_email_request(request, settings)

        if not email.attachments:
            return _without_attachments_response(request, email)

        if dev_mode:
            logger.info(
                "MODALITA' DEV | EMAIL NON REGISTRATA | id=%s | ricevuta_il=%s | "
                "oggetto='%s' | allegati=%d",
                email.key, email.received_at or "(data assente)",
                email.subject or "(senza oggetto)", len(email.attachments),
            )
            body = {
                "id_messaggio": email.key,
                "oggetto": email.subject,
                "esito": "non_registrata_dev",
                "registrata": False,
                "motivo": "modalita_sviluppo",
                "modalita_sviluppo": True,
            }
            if repairs:
                body["avvisi"] = [
                    "JSON non valido riparato in lettura: " + "; ".join(repairs)
                ]
            return JSONResponse(body, status_code=MESSAGGIO_IGNORATO)

        if not request.app.state.message_store.register(email, payload):
            logger.info("Messaggio gia' registrato: %s.", email.key)
            return JSONResponse(
                _ignored_message(email.key, email.subject, "gia_registrato"),
                status_code=MESSAGGIO_IGNORATO,
            )

        logger.info(
            "EMAIL REGISTRATA | id=%s | ricevuta_il=%s | oggetto='%s' | allegati=%d",
            email.key, email.received_at or "(data assente)",
            email.subject or "(senza oggetto)", len(email.attachments),
        )
        body = {
            "id_messaggio": email.key,
            "oggetto": email.subject,
            "esito": "registrata",
            "registrata": True,
        }
        if repairs:
            body["avvisi"] = ["JSON non valido riparato in lettura: " + "; ".join(repairs)]
        return JSONResponse(body, status_code=MESSAGGIO_REGISTRATO)

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


def _payload_value(payload: Any, *names: str) -> str:
    """Legge pochi campi del JSON senza costruire l'email o gli allegati."""
    if not isinstance(payload, Mapping):
        return ""
    values = {str(key).lower(): value for key, value in payload.items()}
    for name in names:
        value = values.get(name.lower())
        if value is not None:
            text = str(value).strip()
            if text:
                return text
    return ""


def _ignored_message(message_key: str, subject: str, reason: str) -> dict:
    """Risposta 2xx: il flow puo' ignorarla senza ritentare la HTTP action."""
    return {
        "id_messaggio": message_key or "(senza id)",
        "oggetto": subject,
        "esito": "ignorata",
        "considerata": False,
        "motivo": reason,
    }


def _without_attachments_response(request: Request, email: InboundEmail) -> JSONResponse:
    """Scarta email senza allegati, lasciando un segnale per il flusso."""
    request.app.state.email_session_report.discarded(
        message_key=email.key,
        received_at=email.received_at,
        subject=email.subject,
        reason="senza allegati",
    )
    logger.info(
        "EMAIL SCARTATA | motivo=senza_allegati | id=%s | ricevuta_il=%s | oggetto='%s'",
        email.key, email.received_at or "(data assente)", email.subject or "(senza oggetto)",
    )
    return JSONResponse(
        _ignored_message(email.key, email.subject, MOTIVO_SENZA_ALLEGATI),
        status_code=MESSAGGIO_IGNORATO,
    )


def _forwarding_block_reason(email: InboundEmail) -> Optional[str]:
    """Restituisce il motivo che impedisce l'inoltro, altrimenti ``None``."""
    if DESTINATARIO_ESCLUSO_DALL_INOLTRO in email.recipients:
        return MOTIVO_DESTINATARIO_ESCLUSO
    return None


async def _read_email_request(
    request: Request, settings: Settings,
) -> Tuple[InboundEmail, Mapping[str, Any], List[str]]:
    """Legge e valida il payload condiviso dagli endpoint email."""
    payload, repairs = await _read_json(request, settings.api.max_request_bytes)
    logger.info("PAYLOAD JSON RICEVUTO:\n%s", _payload_to_log(payload))
    try:
        email = parse_email(
            payload,
            include_inline_images=settings.attachments.include_inline_images,
            max_attachment_bytes=settings.attachments.max_bytes,
            local_files=settings.local_files,
        )
    except InboundError as exc:
        logger.error(
            "Payload non interpretabile: %s\nPayload completo:\n%s",
            exc,
            _payload_to_log(payload),
        )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return email, payload, repairs


async def _read_json(request: Request, max_bytes: int) -> Tuple[Any, List[str]]:
    """Legge il corpo della richiesta e lo interpreta.

    Restituisce ``(payload, riparazioni)``: il JSON del flusso arriva quasi
    sempre non valido (vedi ``rawjson``), viene letto lo stesso e le riparazioni
    applicate risalgono fino alla risposta.
    """
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

    raw_text = raw.decode("utf-8", errors="replace")
    try:
        payload, repairs = loads_tolerant(raw_text)
    except RawJsonError as exc:
        logger.error(
            "JSON non interpretabile: %s\nPayload completo (raw):\n%s",
            exc,
            raw_text,
        )
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=f"JSON non valido: {exc}"
        ) from exc

    if repairs:
        # Power Automate costruisce il JSON concatenando stringhe: a capo,
        # virgolette degli attributi HTML e percorsi Windows lo rendono non
        # valido. Si legge lo stesso, ma resta a verbale.
        logger.warning(
            "JSON non valido riparato in lettura (%s). "
            "Conviene correggere il flusso Power Automate a monte.",
            "; ".join(repairs),
        )
        logger.debug("Payload riparato (raw):\n%s", raw_text)
    return payload, repairs
