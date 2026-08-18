"""Caricamento e validazione della configurazione.

La configurazione arriva da due sorgenti distinte:

* ``config.yaml``  -> parametri di funzionamento (non segreti, versionabili);
* variabili d'ambiente / ``.env`` -> i soli segreti: la chiave API di ocr.space
  e le credenziali dell'applicazione registrata su Microsoft Entra ID.

Questa separazione evita che chiavi e segreti finiscano per sbaglio dentro il
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
CLIENT_ID_ENV = "MS_CLIENT_ID"
CLIENT_SECRET_ENV = "MS_CLIENT_SECRET"
TENANT_ID_ENV = "MS_TENANT_ID"

# Flussi di autenticazione supportati dalla libreria O365 e usati qui:
#   authorization -> applicazione web/desktop con segreto, consenso una tantum
#   public        -> applicazione senza segreto (client pubblico)
#   credentials   -> solo applicazione (client credentials), senza utente
AUTH_FLOWS = ("authorization", "public", "credentials")

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
    codes: List[str] = field(default_factory=lambda: ["1501A"])
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
    """Accesso alla casella tramite Microsoft Graph (libreria O365).

    ``client_id``/``client_secret``/``tenant_id`` non si leggono dal YAML: sono
    segreti e arrivano dall'ambiente (file ``.env``).
    """

    folder: str = "Inbox"
    # Ogni quanto interrogare la casella e quanto indietro guardare a ogni giro.
    poll_interval_minutes: int = 5
    lookback_minutes: int = 5
    # Considera solo i messaggi ancora da leggere.
    unread_only: bool = True
    # All'avvio recupera i messaggi degli ultimi N minuti (0 per disattivare).
    catch_up_minutes: int = 30
    max_messages_per_poll: int = 50
    processed_category: str = "Inoltrata-Televisita"
    auth_flow: str = "authorization"
    # Casella da leggere: obbligatoria con auth_flow "credentials" (solo
    # applicazione), facoltativa negli altri casi (si usa quella dell'utente).
    mailbox: str = ""
    token_path: Path = Path("state/o365_token.txt")
    request_timeout_seconds: int = 60
    client_id: str = ""
    client_secret: str = ""
    tenant_id: str = "common"


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
        settings.outlook.client_id = os.environ.get(CLIENT_ID_ENV, "").strip()
        settings.outlook.client_secret = os.environ.get(CLIENT_SECRET_ENV, "").strip()
        settings.outlook.tenant_id = os.environ.get(TENANT_ID_ENV, "").strip() or "common"
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
            codes=_as_str_list(rules_raw.get("codes"), ["1501A"]),
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
            poll_interval_minutes=int(
                outlook_raw.get("poll_interval_minutes", OutlookSettings.poll_interval_minutes)
            ),
            lookback_minutes=int(outlook_raw.get("lookback_minutes", OutlookSettings.lookback_minutes)),
            unread_only=bool(outlook_raw.get("unread_only", OutlookSettings.unread_only)),
            catch_up_minutes=int(outlook_raw.get("catch_up_minutes", 30)),
            max_messages_per_poll=int(
                outlook_raw.get("max_messages_per_poll", OutlookSettings.max_messages_per_poll)
            ),
            processed_category=str(outlook_raw.get("processed_category", "")),
            auth_flow=str(outlook_raw.get("auth_flow", OutlookSettings.auth_flow)).lower(),
            mailbox=str(outlook_raw.get("mailbox", "")).strip(),
            token_path=Path(str(outlook_raw.get("token_path", OutlookSettings.token_path))),
            request_timeout_seconds=int(
                outlook_raw.get("request_timeout_seconds", OutlookSettings.request_timeout_seconds)
            ),
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
        if self.outlook.auth_flow not in AUTH_FLOWS:
            raise ConfigError(
                "outlook.auth_flow deve valere " + " oppure ".join(repr(f) for f in AUTH_FLOWS) + "."
            )
        if self.outlook.auth_flow == "credentials" and not self.outlook.mailbox:
            raise ConfigError(
                "Con outlook.auth_flow: credentials serve outlook.mailbox, "
                "l'indirizzo della casella da leggere (non c'e' un utente connesso)."
            )
        if self.outlook.poll_interval_minutes < 1:
            raise ConfigError("outlook.poll_interval_minutes deve essere >= 1.")
        if self.outlook.lookback_minutes < 1:
            raise ConfigError("outlook.lookback_minutes deve essere >= 1.")
        if self.outlook.max_messages_per_poll < 1:
            raise ConfigError("outlook.max_messages_per_poll deve essere >= 1.")

    def ensure_directories(self) -> None:
        """Crea le cartelle di stato, del token e di log: il primo avvio non fallisce."""
        self.storage.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.outlook.token_path.parent.mkdir(parents=True, exist_ok=True)
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
