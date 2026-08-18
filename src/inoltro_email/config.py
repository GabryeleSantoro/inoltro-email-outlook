"""Caricamento e validazione della configurazione.

La configurazione arriva da due sorgenti distinte:

* ``config.yaml``  -> parametri di funzionamento (non segreti, versionabili);
* variabili d'ambiente / ``.env`` -> la sola chiave API di ocr.space.

Questa separazione evita che la chiave finisca per sbaglio dentro il
repository insieme al file di configurazione.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

API_KEY_ENV = "OCR_SPACE_API_KEY"

DEFAULT_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif"]


class ConfigError(Exception):
    """Configurazione assente, malformata o incoerente."""


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
class RuleSettings:
    keywords: List[str] = field(default_factory=lambda: ["televisita"])
    codes: List[str] = field(default_factory=lambda: ["15A10"])
    mode: str = "all"
    fuzzy_ocr_confusions: bool = True


@dataclass
class ForwardSettings:
    to: List[str] = field(default_factory=list)
    cc: List[str] = field(default_factory=list)
    subject_prefix: str = ""
    body_note: str = ""
    dry_run: bool = True


@dataclass
class OutlookSettings:
    folder: str = "Inbox"
    catch_up_minutes: int = 30
    processed_category: str = "Inoltrata-Televisita"


@dataclass
class AttachmentSettings:
    allowed_extensions: List[str] = field(default_factory=lambda: list(DEFAULT_EXTENSIONS))
    max_bytes: int = 10_485_760


@dataclass
class StorageSettings:
    db_path: Path = Path("state/processed.sqlite3")


@dataclass
class LoggingSettings:
    level: str = "INFO"
    file: Optional[Path] = Path("logs/inoltro.log")


@dataclass
class Settings:
    ocr: OcrSettings = field(default_factory=OcrSettings)
    rules: RuleSettings = field(default_factory=RuleSettings)
    forward: ForwardSettings = field(default_factory=ForwardSettings)
    outlook: OutlookSettings = field(default_factory=OutlookSettings)
    attachments: AttachmentSettings = field(default_factory=AttachmentSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)

    @classmethod
    def load(cls, config_path: Path, *, require_api_key: bool = True) -> "Settings":
        """Legge il YAML, unisce la chiave API dall'ambiente e valida il tutto."""
        load_dotenv()  # popola l'ambiente dal file .env se presente

        config_path = Path(config_path)
        if not config_path.is_file():
            raise ConfigError(
                f"File di configurazione non trovato: {config_path}. "
                "Copiare config.example.yaml in config.yaml e adattarlo."
            )
        try:
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"YAML non valido in {config_path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ConfigError(f"La radice di {config_path} deve essere una mappa YAML.")

        settings = cls._from_dict(raw)
        settings.ocr.api_key = os.environ.get(API_KEY_ENV, "").strip()
        settings.validate(require_api_key=require_api_key)
        return settings

    @classmethod
    def _from_dict(cls, raw: Dict[str, Any]) -> "Settings":
        def section(name: str) -> Dict[str, Any]:
            value = raw.get(name) or {}
            if not isinstance(value, dict):
                raise ConfigError(f"La sezione '{name}' deve essere una mappa YAML.")
            return value

        ocr_raw = section("ocr")
        rules_raw = section("rules")
        fwd_raw = section("forward")
        outlook_raw = section("outlook")
        att_raw = section("attachments")
        storage_raw = section("storage")
        log_raw = section("logging")

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
        rules = RuleSettings(
            keywords=_as_str_list(rules_raw.get("keywords"), ["televisita"]),
            codes=_as_str_list(rules_raw.get("codes"), ["15A10"]),
            mode=str(rules_raw.get("mode", "all")).lower(),
            fuzzy_ocr_confusions=bool(rules_raw.get("fuzzy_ocr_confusions", True)),
        )
        forward = ForwardSettings(
            to=_as_str_list(fwd_raw.get("to"), []),
            cc=_as_str_list(fwd_raw.get("cc"), []),
            subject_prefix=str(fwd_raw.get("subject_prefix", "")),
            body_note=str(fwd_raw.get("body_note", "")),
            dry_run=bool(fwd_raw.get("dry_run", True)),
        )
        outlook = OutlookSettings(
            folder=str(outlook_raw.get("folder", "Inbox")),
            catch_up_minutes=int(outlook_raw.get("catch_up_minutes", 30)),
            processed_category=str(outlook_raw.get("processed_category", "")),
        )
        attachments = AttachmentSettings(
            allowed_extensions=[
                _normalize_extension(ext)
                for ext in _as_str_list(att_raw.get("allowed_extensions"), DEFAULT_EXTENSIONS)
            ],
            max_bytes=int(att_raw.get("max_bytes", AttachmentSettings.max_bytes)),
        )
        storage = StorageSettings(db_path=Path(str(storage_raw.get("db_path", "state/processed.sqlite3"))))
        log_file = log_raw.get("file", "logs/inoltro.log")
        logging_settings = LoggingSettings(
            level=str(log_raw.get("level", "INFO")).upper(),
            file=Path(str(log_file)) if log_file else None,
        )
        return cls(
            ocr=ocr,
            rules=rules,
            forward=forward,
            outlook=outlook,
            attachments=attachments,
            storage=storage,
            logging=logging_settings,
        )

    def validate(self, *, require_api_key: bool = True) -> None:
        if require_api_key and not self.ocr.api_key:
            raise ConfigError(
                f"Variabile d'ambiente {API_KEY_ENV} non impostata. "
                "Copiare .env.example in .env e inserire la chiave di ocr.space."
            )
        if self.ocr.engine not in (1, 2, 3):
            raise ConfigError("ocr.engine deve valere 1, 2 o 3.")
        if self.ocr.max_pdf_pages_per_request < 1:
            raise ConfigError("ocr.max_pdf_pages_per_request deve essere >= 1.")
        if self.ocr.max_file_bytes < 1:
            raise ConfigError("ocr.max_file_bytes deve essere > 0.")
        if self.rules.mode not in ("all", "any"):
            raise ConfigError("rules.mode deve valere 'all' oppure 'any'.")
        if not self.rules.keywords and not self.rules.codes:
            raise ConfigError("Serve almeno una keyword o un codice in 'rules'.")
        if not self.forward.to:
            raise ConfigError("Serve almeno un destinatario in 'forward.to'.")
        for address in self.forward.to + self.forward.cc:
            if "@" not in address:
                raise ConfigError(f"Indirizzo di inoltro non valido: {address!r}")
        if self.attachments.max_bytes < 1:
            raise ConfigError("attachments.max_bytes deve essere > 0.")

    def ensure_directories(self) -> None:
        """Crea le cartelle di stato e di log, cosi' il primo avvio non fallisce."""
        self.storage.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.logging.file:
            self.logging.file.parent.mkdir(parents=True, exist_ok=True)


def _as_str_list(value: Any, default: List[str]) -> List[str]:
    if value is None:
        return list(default)
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    raise ConfigError(f"Atteso un elenco di stringhe, ricevuto {type(value).__name__}.")


def _normalize_extension(ext: str) -> str:
    ext = ext.strip().lower()
    return ext if ext.startswith(".") else f".{ext}"
