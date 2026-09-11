"""Client sincrono per PaddleOCR eseguito interamente in locale.

La libreria PaddleOCR scarica automaticamente i pesi se non li trova. Questo
servizio non deve farlo durante l'analisi di email: i modelli vengono preparati
esplicitamente con ``inoltro-email prepara-ocr`` e il processo normale rifiuta
una cache incompleta prima di caricare il motore.
"""

from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional

from ..config import OcrSettings
from ..models import OcrResult


class OcrError(Exception):
    """Motore locale non disponibile o file non riconosciuto."""


class PaddleOcrClient:
    """Adapter piccolo sopra PaddleOCR 3.x, condivisibile fra richieste."""

    _ORIENTATION_MODEL = "PP-LCNet_x1_0_doc_ori"

    def __init__(
        self,
        settings: OcrSettings,
        *,
        allow_model_download: bool = False,
        engine_factory: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._settings = settings
        self._lock = threading.Lock()
        self._cache_dir = settings.model_cache_dir.resolve()
        self._configure_cache()

        if not allow_model_download:
            self._ensure_models_present()

        factory = engine_factory or _load_paddleocr()
        try:
            self._engine = factory(**self._engine_kwargs(allow_model_download))
        except Exception as exc:  # Paddle conserva eccezioni dipendenti dal backend
            raise OcrError(f"Impossibile inizializzare PaddleOCR: {exc}") from exc

    @classmethod
    def prepare(cls, settings: OcrSettings) -> None:
        """Scarica i pesi nella cache configurata e prova una inferenza locale."""
        client = cls(settings, allow_model_download=True)
        try:
            with tempfile.TemporaryDirectory(prefix="inoltro-paddle-check-") as tmp_dir:
                image_path = Path(tmp_dir) / "check.png"
                _create_check_image(image_path)
                client.parse_file(image_path)
        except OcrError:
            raise
        except Exception as exc:  # pragma: no cover - protezione per librerie native
            raise OcrError(f"Verifica PaddleOCR non riuscita: {exc}") from exc

    def close(self) -> None:
        """Interfaccia uniforme con il precedente client; Paddle non ha close."""

    def __enter__(self) -> "PaddleOcrClient":
        return self

    def __exit__(self, *_exc_info: Any) -> None:
        self.close()

    def parse_file(self, path: Path) -> OcrResult:
        path = Path(path)
        if not path.is_file():
            raise OcrError(f"{path.name}: file non trovato.")

        try:
            results = self._predict(path)
        except OcrError:
            raise
        except Exception as exc:  # pragma: no cover - dipende dal backend nativo
            raise OcrError(f"{path.name}: PaddleOCR non riuscito ({exc}).") from exc

        texts: list[str] = []
        raw: list[dict[str, Any]] = []
        for result in results:
            data = _result_to_dict(result)
            raw.append(data)
            page = data.get("res", data)
            recognized = page.get("rec_texts", []) if isinstance(page, Mapping) else []
            if isinstance(recognized, str):
                recognized = [recognized]
            if isinstance(recognized, Iterable):
                texts.extend(str(text).strip() for text in recognized if str(text).strip())

        text = "\n".join(texts)
        if not text:
            raise OcrError(f"{path.name}: PaddleOCR non ha riconosciuto testo.")
        return OcrResult(text=text, exit_code=1, raw={"pages": raw})

    def _predict(self, path: Path) -> list[Any]:
        # PaddleOCR non dichiara il client thread-safe. Una sola inferenza per
        # processo evita risultati mescolati e non sovraccarica la CPU del server.
        with self._lock:
            return list(self._engine.predict(str(path)))

    def _configure_cache(self) -> None:
        # Deve essere impostata prima dell'import di paddleocr/paddlex.
        os.environ["PADDLE_PDX_CACHE_HOME"] = str(self._cache_dir)

    def _engine_kwargs(self, allow_model_download: bool) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "device": self._settings.device,
            "text_detection_model_name": self._settings.detection_model,
            "text_recognition_model_name": self._settings.recognition_model,
            "use_doc_orientation_classify": self._settings.use_doc_orientation_classify,
            "use_doc_unwarping": self._settings.use_doc_unwarping,
            "use_textline_orientation": self._settings.use_textline_orientation,
            "enable_mkldnn": self._settings.enable_mkldnn,
        }
        if not allow_model_download:
            models = self._models_dir
            kwargs["text_detection_model_dir"] = str(models / self._settings.detection_model)
            kwargs["text_recognition_model_dir"] = str(models / self._settings.recognition_model)
            if self._settings.use_doc_orientation_classify:
                kwargs["doc_orientation_classify_model_dir"] = str(
                    models / self._ORIENTATION_MODEL
                )
        return kwargs

    @property
    def _models_dir(self) -> Path:
        return self._cache_dir / "official_models"

    def _ensure_models_present(self) -> None:
        required = [self._settings.detection_model, self._settings.recognition_model]
        if self._settings.use_doc_orientation_classify:
            required.append(self._ORIENTATION_MODEL)
        missing = [name for name in required if not (self._models_dir / name).is_dir()]
        if missing:
            joined = ", ".join(missing)
            raise OcrError(
                f"Modelli PaddleOCR mancanti in {self._models_dir}: {joined}. "
                "Eseguire 'inoltro-email prepara-ocr' su una macchina con rete e "
                "copiare la cache nel server."
            )


def _load_paddleocr() -> Callable[..., Any]:
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:  # pragma: no cover - dipendenza dichiarata
        raise OcrError(
            "PaddleOCR non installato: eseguire 'uv sync' oppure "
            "'pip install -r requirements.txt'."
        ) from exc
    return PaddleOCR


def _result_to_dict(result: Any) -> dict[str, Any]:
    if isinstance(result, Mapping):
        return dict(result)
    for attribute in ("json", "to_dict"):
        value = getattr(result, attribute, None)
        if callable(value):
            value = value()
        if isinstance(value, Mapping):
            return dict(value)
    raise OcrError(f"Risposta PaddleOCR non riconosciuta: {type(result).__name__}.")


def _create_check_image(path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont

        image = Image.new("RGB", (800, 160), "white")
        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except OSError:
            font = ImageFont.load_default(size=48)
        ImageDraw.Draw(image).text(
            (20, 50), "TELEMEDICINA 1501A", fill="black", font=font
        )
        image.save(path, format="PNG")
    except Exception as exc:  # pragma: no cover - Pillow e' dipendenza runtime
        raise OcrError(f"Impossibile creare immagine di verifica: {exc}") from exc
