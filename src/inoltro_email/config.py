"""Caricamento e validazione della configurazione.

La configurazione arriva da due sorgenti distinte:

* ``config.yaml``  -> parametri di funzionamento (non segreti, versionabili);
* variabili d'ambiente / ``.env`` -> i soli segreti: la chiave API di ocr.space
  e la chiave che Power Automate deve presentare al servizio.

Questa separazione evita che chiavi e segreti finiscano per sbaglio dentro il
repository insieme al file di configurazione. Il file YAML e' facoltativo: se
manca, il servizio parte con i valori predefiniti (comodo dentro un container,
dove si preferisce configurare tutto da variabili d'ambiente).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

OCR_API_KEY_ENV = "OCR_SPACE_API_KEY"
SERVICE_API_KEY_ENV = "SERVICE_API_KEY"
HOST_ENV = "API_HOST"
PORT_ENV = "PORT"

DEFAULT_CONFIG_PATH = Path("config.yaml")
DEFAULT_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif"]


class ConfigError(Exception):
    """Configurazione assente, malformata o incoerente."""


@dataclass
class ApiSettings:
    """Parametri del servizio HTTP interrogato da Power Automate."""

    host: str = "0.0.0.0"
    port: int = 8000
    # Chiave attesa nell'header X-API-Key. Vuota = nessun controllo (solo per
    # prove locali: in rete il servizio va sempre protetto).
    api_key: str = ""
    # Dimensione massima del corpo della richiesta: un'email con allegati
    # arriva in base64, quindi circa 4/3 della dimensione reale.
    max_request_bytes: int = 33_554_432  # 32 MiB
    # Titolo e versione mostrati nella documentazione OpenAPI.
    title: str = "Servizio telemedicina - analisi email"


@dataclass
class ScreeningSettings:
    """Prima verifica su oggetto e corpo del messaggio."""

    keywords: List[str] = field(default_factory=lambda: ["telemedicina", "televisita"])
    # any = basta uno dei termini (impostazione voluta: telemedicina O televisita)
    # all = servono tutti
    mode: str = "any"
    # Se lo screening non passa non si chiama l'OCR: si risparmia quota.
    stop_on_failure: bool = True


@dataclass
class RuleSettings:
    """Criteri che il testo letto da allegati e foto deve soddisfare."""

    keywords: List[str] = field(default_factory=lambda: ["telemedicina"])
    codes: List[str] = field(default_factory=lambda: ["1501A"])
    mode: str = "all"
    fuzzy_ocr_confusions: bool = True


@dataclass
class OcrSettings:
    api_key: str = ""
    endpoint: str = "https://api.ocr.space/parse/image"
    language: str = "ita"
    engine: int = 2
    timeout_seconds: int = 120
    max_retries: int = 3
    max_file_bytes: int = 1_048_576
    max_pdf_pages_per_request: int = 3


@dataclass
class AttachmentSettings:
    allowed_extensions: List[str] = field(default_factory=lambda: list(DEFAULT_EXTENSIONS))
    max_bytes: int = 10_485_760
    # Analizza anche le foto incorporate nel corpo del messaggio (allegati
    # inline e immagini "data:" dentro l'HTML).
    include_inline_images: bool = True
    # Quanti file al massimo passare all'OCR per ogni email.
    max_files: int = 10
    # false = ci si ferma al primo file conforme (meno chiamate all'OCR);
    # true  = si leggono comunque tutti i file, utile per diagnosticare.
    analyze_all: bool = False


@dataclass
class SentimentSettings:
    """Soglie del punteggio di sentiment e di intento di prenotazione."""

    positive_threshold: float = 0.15
    negative_threshold: float = -0.15
    booking_threshold: float = 0.5
    # Quanto un allegato conforme rafforza l'ipotesi "prenotazione".
    attachment_bonus: float = 0.15


@dataclass
class LoggingSettings:
    level: str = "INFO"
    file: Optional[Path] = Path("logs/servizio.log")


@dataclass
class Settings:
    api: ApiSettings = field(default_factory=ApiSettings)
    screening: ScreeningSettings = field(default_factory=ScreeningSettings)
    rules: RuleSettings = field(default_factory=RuleSettings)
    ocr: OcrSettings = field(default_factory=OcrSettings)
    attachments: AttachmentSettings = field(default_factory=AttachmentSettings)
    sentiment: SentimentSettings = field(default_factory=SentimentSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)

    @classmethod
    def load(
        cls,
        config_path: Optional[Path] = None,
        *,
        require_api_key: bool = True,
    ) -> "Settings":
        """Legge il YAML, unisce i segreti dall'ambiente e valida il tutto.

        ``config_path`` esplicito e mancante e' un errore; se invece non viene
        indicato nulla e ``config.yaml`` non esiste, si usano i valori
        predefiniti e si configura tutto da variabili d'ambiente.
        """
        load_dotenv()  # popola l'ambiente dal file .env se presente

        explicit = config_path is not None
        path = Path(config_path) if explicit else DEFAULT_CONFIG_PATH

        if path.is_file():
            settings = cls._from_dict(_read_yaml(path))
        elif explicit:
            raise ConfigError(
                f"File di configurazione non trovato: {path}. "
                "Copiare config.example.yaml in config.yaml e adattarlo."
            )
        else:
            settings = cls()

        settings.apply_environment()
        settings.validate(require_api_key=require_api_key)
        return settings

    def apply_environment(self) -> None:
        """Sovrascrive con l'ambiente cio' che non deve stare nel YAML."""
        self.ocr.api_key = os.environ.get(OCR_API_KEY_ENV, "").strip()
        self.api.api_key = os.environ.get(SERVICE_API_KEY_ENV, "").strip()
        host = os.environ.get(HOST_ENV, "").strip()
        if host:
            self.api.host = host
        port = os.environ.get(PORT_ENV, "").strip()
        if port:
            try:
                self.api.port = int(port)
            except ValueError as exc:
                raise ConfigError(f"Variabile d'ambiente {PORT_ENV} non numerica: {port!r}") from exc

    @classmethod
    def _from_dict(cls, raw: Dict[str, Any]) -> "Settings":
        def section(name: str) -> Dict[str, Any]:
            value = raw.get(name) or {}
            if not isinstance(value, dict):
                raise ConfigError(f"La sezione '{name}' deve essere una mappa YAML.")
            return value

        api_raw = section("api")
        screening_raw = section("screening")
        rules_raw = section("rules")
        ocr_raw = section("ocr")
        att_raw = section("attachments")
        sentiment_raw = section("sentiment")
        log_raw = section("logging")

        api = ApiSettings(
            host=str(api_raw.get("host", ApiSettings.host)),
            port=int(api_raw.get("port", ApiSettings.port)),
            max_request_bytes=int(api_raw.get("max_request_bytes", ApiSettings.max_request_bytes)),
            title=str(api_raw.get("title", ApiSettings.title)),
        )
        screening = ScreeningSettings(
            keywords=_as_str_list(screening_raw.get("keywords"), ["telemedicina", "televisita"]),
            mode=str(screening_raw.get("mode", ScreeningSettings.mode)).lower(),
            stop_on_failure=bool(screening_raw.get("stop_on_failure", True)),
        )
        rules = RuleSettings(
            keywords=_as_str_list(rules_raw.get("keywords"), ["telemedicina"]),
            codes=_as_str_list(rules_raw.get("codes"), ["1501A"]),
            mode=str(rules_raw.get("mode", RuleSettings.mode)).lower(),
            fuzzy_ocr_confusions=bool(rules_raw.get("fuzzy_ocr_confusions", True)),
        )
        ocr = OcrSettings(
            endpoint=str(ocr_raw.get("endpoint", OcrSettings.endpoint)),
            language=str(ocr_raw.get("language", OcrSettings.language)),
            engine=int(ocr_raw.get("engine", OcrSettings.engine)),
            timeout_seconds=int(ocr_raw.get("timeout_seconds", OcrSettings.timeout_seconds)),
            max_retries=int(ocr_raw.get("max_retries", OcrSettings.max_retries)),
            max_file_bytes=int(ocr_raw.get("max_file_bytes", OcrSettings.max_file_bytes)),
            max_pdf_pages_per_request=int(
                ocr_raw.get("max_pdf_pages_per_request", OcrSettings.max_pdf_pages_per_request)
            ),
        )
        attachments = AttachmentSettings(
            allowed_extensions=[
                _normalize_extension(ext)
                for ext in _as_str_list(att_raw.get("allowed_extensions"), DEFAULT_EXTENSIONS)
            ],
            max_bytes=int(att_raw.get("max_bytes", AttachmentSettings.max_bytes)),
            include_inline_images=bool(att_raw.get("include_inline_images", True)),
            max_files=int(att_raw.get("max_files", AttachmentSettings.max_files)),
            analyze_all=bool(att_raw.get("analyze_all", False)),
        )
        sentiment = SentimentSettings(
            positive_threshold=float(
                sentiment_raw.get("positive_threshold", SentimentSettings.positive_threshold)
            ),
            negative_threshold=float(
                sentiment_raw.get("negative_threshold", SentimentSettings.negative_threshold)
            ),
            booking_threshold=float(
                sentiment_raw.get("booking_threshold", SentimentSettings.booking_threshold)
            ),
            attachment_bonus=float(
                sentiment_raw.get("attachment_bonus", SentimentSettings.attachment_bonus)
            ),
        )
        log_file = log_raw.get("file", "logs/servizio.log")
        logging_settings = LoggingSettings(
            level=str(log_raw.get("level", "INFO")).upper(),
            file=Path(str(log_file)) if log_file else None,
        )
        return cls(
            api=api,
            screening=screening,
            rules=rules,
            ocr=ocr,
            attachments=attachments,
            sentiment=sentiment,
            logging=logging_settings,
        )

    def validate(self, *, require_api_key: bool = True) -> None:
        if require_api_key and not self.ocr.api_key:
            raise ConfigError(
                f"Variabile d'ambiente {OCR_API_KEY_ENV} non impostata. "
                "Copiare .env.example in .env e inserire la chiave di ocr.space."
            )
        if not 1 <= self.api.port <= 65535:
            raise ConfigError("api.port deve essere compreso fra 1 e 65535.")
        if self.api.max_request_bytes < 1:
            raise ConfigError("api.max_request_bytes deve essere > 0.")
        if self.screening.mode not in ("all", "any"):
            raise ConfigError("screening.mode deve valere 'all' oppure 'any'.")
        if not _clean(self.screening.keywords):
            raise ConfigError("Serve almeno una parola in 'screening.keywords'.")
        if self.rules.mode not in ("all", "any"):
            raise ConfigError("rules.mode deve valere 'all' oppure 'any'.")
        if not _clean(self.rules.keywords) and not _clean(self.rules.codes):
            raise ConfigError("Serve almeno una keyword o un codice in 'rules'.")
        if self.ocr.engine not in (1, 2, 3):
            raise ConfigError("ocr.engine deve valere 1, 2 o 3.")
        if self.ocr.max_pdf_pages_per_request < 1:
            raise ConfigError("ocr.max_pdf_pages_per_request deve essere >= 1.")
        if self.ocr.max_file_bytes < 1:
            raise ConfigError("ocr.max_file_bytes deve essere > 0.")
        if self.attachments.max_bytes < 1:
            raise ConfigError("attachments.max_bytes deve essere > 0.")
        if self.attachments.max_files < 1:
            raise ConfigError("attachments.max_files deve essere >= 1.")
        if not 0.0 <= self.sentiment.booking_threshold <= 1.0:
            raise ConfigError("sentiment.booking_threshold deve stare fra 0 e 1.")
        if self.sentiment.negative_threshold > self.sentiment.positive_threshold:
            raise ConfigError(
                "sentiment.negative_threshold deve essere <= sentiment.positive_threshold."
            )

    def ensure_directories(self) -> None:
        """Crea la cartella dei log: il primo avvio non fallisce."""
        if self.logging.file:
            self.logging.file.parent.mkdir(parents=True, exist_ok=True)


def _read_yaml(path: Path) -> Dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML non valido in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"La radice di {path} deve essere una mappa YAML.")
    return raw


def _as_str_list(value: Any, default: List[str]) -> List[str]:
    if value is None:
        return list(default)
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    raise ConfigError(f"Atteso un elenco di stringhe, ricevuto {type(value).__name__}.")


def _clean(values: List[str]) -> List[str]:
    return [value for value in values if value and value.strip()]


def _normalize_extension(ext: str) -> str:
    ext = ext.strip().lower()
    return ext if ext.startswith(".") else f".{ext}"
