"""Client HTTP per l'API di ocr.space.

Documentazione: https://ocr.space/ocrapi

L'API accetta un POST multipart verso ``/parse/image`` con la chiave nell'header
``apikey`` e restituisce un JSON con ``ParsedResults[*].ParsedText``. Attenzione:
un errore applicativo (file troppo grande, PDF con troppe pagine, quota esaurita)
arriva con HTTP 200 e ``IsErroredOnProcessing: true``, quindi non basta
controllare lo status code.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from ..config import OcrSettings
from ..models import OcrResult

logger = logging.getLogger(__name__)

# Status HTTP per cui vale la pena riprovare: quota per minuto e guasti server.
RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})
# Su questi il retry e' inutile: la chiave e' sbagliata o mancante.
FATAL_STATUS = frozenset({401, 403})

# Estensioni -> valore del parametro `filetype` atteso da ocr.space.
FILETYPE_BY_EXTENSION = {
    ".pdf": "PDF",
    ".jpg": "JPG",
    ".jpeg": "JPG",
    ".png": "PNG",
    ".tif": "TIF",
    ".tiff": "TIF",
    ".bmp": "BMP",
    ".gif": "GIF",
}


class OcrSpaceError(Exception):
    """Errore restituito da ocr.space o impossibilita' di contattarlo."""


class OcrSpaceClient:
    """Wrapper minimale e sincrono sull'API di ocr.space."""

    def __init__(self, settings: OcrSettings, session: Optional[requests.Session] = None) -> None:
        self._settings = settings
        # Una sola sessione: riusa la connessione TLS fra un allegato e l'altro.
        self._session = session or requests.Session()

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "OcrSpaceClient":
        return self

    def __exit__(self, *_exc_info: Any) -> None:
        self.close()

    def parse_file(self, path: Path) -> OcrResult:
        """Manda un file a ocr.space e restituisce il testo riconosciuto.

        Sollevare ``OcrSpaceError`` se il servizio segnala un errore o se non e'
        raggiungibile dopo tutti i tentativi previsti.
        """
        path = Path(path)
        payload = self._build_payload(path)
        last_error: Optional[str] = None

        for attempt in range(1, self._settings.max_retries + 1):
            try:
                with path.open("rb") as handle:
                    files = {"file": (path.name, handle)}
                    response = self._session.post(
                        self._settings.endpoint,
                        headers={"apikey": self._settings.api_key},
                        data=payload,
                        files=files,
                        timeout=self._settings.timeout_seconds,
                    )
            except requests.RequestException as exc:
                last_error = f"errore di rete: {exc}"
                if not self._sleep_before_retry(attempt, last_error, path.name):
                    raise OcrSpaceError(f"{path.name}: {last_error}") from exc
                continue

            if response.status_code in FATAL_STATUS:
                # Nessun retry: e' un problema di credenziali, non transitorio.
                raise OcrSpaceError(
                    f"{path.name}: ocr.space ha risposto {response.status_code} "
                    "(chiave API mancante, errata o non autorizzata)."
                )
            if response.status_code in RETRYABLE_STATUS:
                last_error = f"HTTP {response.status_code}"
                if not self._sleep_before_retry(attempt, last_error, path.name):
                    raise OcrSpaceError(f"{path.name}: {last_error} dopo {attempt} tentativi.")
                continue
            if response.status_code != 200:
                raise OcrSpaceError(f"{path.name}: HTTP {response.status_code} da ocr.space.")

            try:
                data = response.json()
            except ValueError as exc:
                last_error = "risposta non JSON"
                if not self._sleep_before_retry(attempt, last_error, path.name):
                    raise OcrSpaceError(f"{path.name}: {last_error}.") from exc
                continue

            return self._parse_payload(data, path)

        raise OcrSpaceError(f"{path.name}: OCR non riuscito ({last_error or 'motivo sconosciuto'}).")

    def _build_payload(self, path: Path) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "OCREngine": str(self._settings.engine),
            "isOverlayRequired": "false",
            "detectOrientation": "true",
            "scale": "true",
        }
        # L'engine 2 rileva la lingua da solo e rifiuta il parametro `language`.
        if self._settings.engine != 2:
            payload["language"] = self._settings.language

        filetype = FILETYPE_BY_EXTENSION.get(path.suffix.lower())
        if filetype:
            payload["filetype"] = filetype
        return payload

    def _parse_payload(self, data: Dict[str, Any], path: Path) -> OcrResult:
        if data.get("IsErroredOnProcessing"):
            raise OcrSpaceError(f"{path.name}: {_error_message(data)}")

        results: List[Dict[str, Any]] = data.get("ParsedResults") or []
        if not results:
            raise OcrSpaceError(f"{path.name}: ocr.space non ha restituito risultati.")

        chunks: List[str] = []
        for result in results:
            # FileParseExitCode: 1 = ok, 0/-10/-20/-30/-99 = problemi sulla pagina.
            if result.get("FileParseExitCode") not in (1, None) and result.get("ErrorMessage"):
                logger.warning("Pagina non elaborata in %s: %s", path.name, result.get("ErrorMessage"))
                continue
            text = result.get("ParsedText") or ""
            if text.strip():
                chunks.append(text)

        return OcrResult(
            text="\n".join(chunks),
            exit_code=int(data.get("OCRExitCode", 0) or 0),
            raw=data,
        )

    def _sleep_before_retry(self, attempt: int, reason: str, filename: str) -> bool:
        """Attende con backoff esponenziale. False se i tentativi sono finiti."""
        if attempt >= self._settings.max_retries:
            return False
        delay = 2 ** attempt  # 2s, 4s, 8s, ...
        logger.warning(
            "ocr.space: %s su %s (tentativo %d/%d), nuovo tentativo fra %ds.",
            reason, filename, attempt, self._settings.max_retries, delay,
        )
        time.sleep(delay)
        return True


def _error_message(data: Dict[str, Any]) -> str:
    message = data.get("ErrorMessage") or data.get("ErrorDetails") or "errore non specificato"
    if isinstance(message, list):
        message = "; ".join(str(item) for item in message)
    return str(message)
