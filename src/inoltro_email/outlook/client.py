"""Accesso alla casella Outlook tramite Microsoft Graph (libreria O365).

Non serve Outlook Desktop ne' Windows: si dialoga con Microsoft 365 via HTTPS,
quindi il programma gira anche su Linux, su macOS o dentro un container.

La libreria ``O365`` viene importata dentro ``connect()`` e non a livello di
modulo, cosi' il file resta importabile anche dove non e' installata (utile per
i test e per il comando ``check-file``).

Autenticazione (applicazione registrata su Microsoft Entra ID):

* ``authorization``/``public`` - a nome dell'utente; il consenso si da' una
  volta sola con ``python -m inoltro_email authenticate`` e il token, con il
  suo refresh token, resta in ``outlook.token_path``;
* ``credentials``             - solo applicazione, senza utente: serve
  ``outlook.mailbox`` per indicare quale casella leggere.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional

from ..config import CLIENT_ID_ENV, CLIENT_SECRET_ENV, OutlookSettings
from ..models import AttachmentFile

logger = logging.getLogger(__name__)

# Permessi richiesti in fase di consenso: lettura della casella, scrittura
# (categoria sui messaggi elaborati) e invio dell'inoltro.
DELEGATED_SCOPES = ["basic", "message_all"]

_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff"}
_INBOX_NAMES = {"inbox", "posta in arrivo"}


class OutlookError(Exception):
    """Errore di configurazione, di autenticazione o di dialogo con Graph."""


class OutlookMessage:
    """Adattatore attorno a un ``O365.Message`` che implementa ``MailMessage``."""

    def __init__(self, api_message: Any) -> None:
        self.api_message = api_message

    @property
    def entry_id(self) -> str:
        return str(getattr(self.api_message, "object_id", "") or "")

    @property
    def message_id(self) -> str:
        """Internet Message-ID; stringa vuota se non disponibile."""
        return str(getattr(self.api_message, "internet_message_id", "") or "").strip()

    @property
    def subject(self) -> str:
        return str(getattr(self.api_message, "subject", "") or "")

    @property
    def sender(self) -> str:
        sender = getattr(self.api_message, "sender", None)
        if sender is None:
            return ""
        return str(getattr(sender, "address", "") or getattr(sender, "name", "") or "")

    @property
    def has_attachments(self) -> bool:
        return bool(getattr(self.api_message, "has_attachments", False))

    @property
    def received_time(self) -> Optional[datetime]:
        value = getattr(self.api_message, "received", None)
        return value if isinstance(value, datetime) else None

    @property
    def is_read(self) -> bool:
        return bool(getattr(self.api_message, "is_read", False))


class OutlookClient:
    """Implementazione del protocollo ``MailClient`` su Microsoft Graph."""

    def __init__(
        self,
        settings: OutlookSettings,
        allowed_extensions: Optional[List[str]] = None,
    ) -> None:
        self._settings = settings
        self._allowed_extensions = {ext.lower() for ext in (allowed_extensions or [])}
        self._account: Any = None
        self._folder: Any = None

    # ------------------------------------------------------------ connessione

    def connect(self) -> None:
        """Costruisce l'account O365 e risolve la cartella da sorvegliare."""
        self._account = self._build_account()

        if not self._account.is_authenticated:
            if self._settings.auth_flow == "credentials":
                # Flusso solo-applicazione: il token si ottiene senza interazione.
                if not self._account.authenticate():
                    raise OutlookError(
                        "Autenticazione applicativa non riuscita: verificare "
                        f"{CLIENT_ID_ENV}, {CLIENT_SECRET_ENV} e il tenant."
                    )
            else:
                raise OutlookError(
                    "Nessun token valido in "
                    f"{self._settings.token_path}: eseguire una volta "
                    "'python -m inoltro_email authenticate' per dare il consenso."
                )

        try:
            mailbox = self._account.mailbox()
            self._folder = _resolve_folder(mailbox, self._settings.folder)
        except OutlookError:
            raise
        except Exception as exc:  # noqa: BLE001 - errori HTTP della libreria
            raise OutlookError(f"Impossibile aprire la casella: {exc}") from exc

        logger.info(
            "Collegato alla casella %s, cartella sorvegliata: %s",
            self._settings.mailbox or "dell'utente autenticato",
            self._settings.folder,
        )

    def authenticate(self) -> bool:
        """Esegue il consenso interattivo e salva il token su disco."""
        account = self._build_account()
        self._account = account
        if self._settings.auth_flow == "credentials":
            return bool(account.authenticate())
        return bool(account.authenticate(requested_scopes=DELEGATED_SCOPES))

    def _build_account(self) -> Any:
        try:
            from O365 import Account, FileSystemTokenBackend  # noqa: PLC0415
        except ImportError as exc:
            raise OutlookError(
                "Libreria O365 non installata: eseguire 'pip install -r requirements.txt'."
            ) from exc

        settings = self._settings
        if not settings.client_id:
            raise OutlookError(
                f"Variabile d'ambiente {CLIENT_ID_ENV} non impostata: copiare "
                ".env.example in .env e inserire i dati dell'applicazione registrata."
            )
        if settings.auth_flow == "public":
            credentials: Any = (settings.client_id,)
        else:
            if not settings.client_secret:
                raise OutlookError(
                    f"Variabile d'ambiente {CLIENT_SECRET_ENV} non impostata "
                    f"(richiesta dal flusso '{settings.auth_flow}')."
                )
            credentials = (settings.client_id, settings.client_secret)

        token_path = Path(settings.token_path)
        token_backend = FileSystemTokenBackend(
            token_path=token_path.parent, token_filename=token_path.name
        )
        try:
            return Account(
                credentials,
                auth_flow_type=settings.auth_flow,
                tenant_id=settings.tenant_id,
                token_backend=token_backend,
                main_resource=settings.mailbox or None,
                timeout=settings.request_timeout_seconds,
            )
        except ValueError as exc:  # credenziali di forma sbagliata
            raise OutlookError(f"Credenziali non valide: {exc}") from exc

    @property
    def folder(self) -> Any:
        if self._folder is None:
            raise OutlookError("Client non connesso: chiamare prima connect().")
        return self._folder

    # -------------------------------------------------------------- messaggi

    def get_message(self, entry_id: str) -> Optional[OutlookMessage]:
        try:
            message = self.folder.get_message(entry_id)
        except Exception as exc:  # noqa: BLE001 - messaggio spostato o cancellato
            logger.warning("Messaggio %s non recuperabile: %s", entry_id, exc)
            return None
        return OutlookMessage(message) if message is not None else None

    def recent_messages(self, minutes: int, unread_only: bool = True) -> List[OutlookMessage]:
        """Messaggi ricevuti negli ultimi ``minutes`` minuti.

        Il filtro viene applicato dal servizio (``$filter`` di Graph): si
        scaricano solo i messaggi che interessano, non l'intera cartella.
        """
        if minutes <= 0:
            return []

        threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        folder = self.folder
        query = folder.new_query()
        criteria = query.greater_equal("received_date_time", threshold)
        if unread_only:
            criteria = criteria & query.equals("is_read", False)

        try:
            found = folder.get_messages(
                limit=self._settings.max_messages_per_poll,
                query=criteria,
                order_by="receivedDateTime desc",
            )
            messages = [OutlookMessage(item) for item in found]
        except Exception as exc:  # noqa: BLE001 - rete, token scaduto, HTTP 429
            raise OutlookError(f"Lettura della casella non riuscita: {exc}") from exc

        logger.info(
            "Trovati %d messaggi%s negli ultimi %d minuti.",
            len(messages), " non letti" if unread_only else "", minutes,
        )
        return messages

    # -------------------------------------------------------------- allegati

    def save_attachments(self, message: OutlookMessage, dest_dir: Path) -> List[AttachmentFile]:
        """Scarica su disco gli allegati analizzabili del messaggio."""
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        saved: List[AttachmentFile] = []

        try:
            attachments = message.api_message.attachments
            attachments.download_attachments()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Allegati non scaricabili per '%s': %s", message.subject, exc)
            return saved

        for index, attachment in enumerate(_iter_attachments(attachments), start=1):
            original_name = str(getattr(attachment, "name", "") or f"allegato_{index}")
            try:
                if getattr(attachment, "attachment_type", "file") != "file":
                    # Es. un messaggio allegato a un altro messaggio.
                    logger.debug("Allegato '%s' non e' un file, ignorato.", original_name)
                    continue

                extension = Path(original_name).suffix.lower()
                if self._allowed_extensions and extension not in self._allowed_extensions:
                    logger.debug("Allegato '%s' di tipo non previsto, ignorato.", original_name)
                    continue
                if extension in _IMAGE_EXTENSIONS and getattr(attachment, "is_inline", False):
                    # Tipicamente il logo della firma: non e' un documento.
                    logger.debug("Immagine incorporata nel corpo '%s', ignorata.", original_name)
                    continue

                target = _unique_path(dest_dir, _sanitize_filename(original_name, index))
                if not attachment.save(str(dest_dir), custom_name=target.name):
                    logger.warning("Allegato '%s' non salvato su disco.", original_name)
                    continue

                saved.append(
                    AttachmentFile(
                        path=target,
                        original_name=original_name,
                        size_bytes=target.stat().st_size,
                    )
                )
                logger.info("Allegato salvato: %s (%d byte)", original_name, target.stat().st_size)
            except Exception as exc:  # noqa: BLE001 - un allegato rotto non blocca gli altri
                logger.warning("Allegato '%s' di '%s' non salvato: %s",
                               original_name, message.subject, exc)

        return saved

    # --------------------------------------------------------------- inoltro

    def forward(
        self,
        message: OutlookMessage,
        to: List[str],
        cc: List[str],
        subject_prefix: str = "",
        body_note: str = "",
    ) -> None:
        """Inoltra il messaggio con tutti i suoi allegati."""
        try:
            draft = message.api_message.forward()
            if draft is None:
                raise OutlookError("Graph non ha restituito la bozza di inoltro.")
            draft.to.add(list(to))
            if cc:
                draft.cc.add(list(cc))
            if subject_prefix:
                draft.subject = f"{subject_prefix}{draft.subject or ''}"
            if body_note:
                # Il setter di 'body' antepone il testo a quello gia' presente,
                # cosi' la nota compare in cima e l'originale resta leggibile.
                draft.body = _format_note(body_note, str(getattr(draft, "body_type", "html")))
            draft.send()
        except OutlookError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise OutlookError(f"Inoltro non riuscito per '{message.subject}': {exc}") from exc

        logger.info("Messaggio '%s' inoltrato a %s", message.subject, ", ".join(to))

    def mark_processed(self, message: OutlookMessage, category: str) -> None:
        """Aggiunge una categoria al messaggio (traccia visibile in Outlook)."""
        if not category:
            return
        try:
            api_message = message.api_message
            existing = [str(item) for item in (getattr(api_message, "categories", None) or [])]
            if category in existing:
                return
            api_message.add_category(category)
            api_message.save_message()
        except Exception as exc:  # noqa: BLE001 - marcatura non essenziale
            logger.warning("Categoria non applicata a '%s': %s", message.subject, exc)


# ------------------------------------------------------------------- utili


def _resolve_folder(mailbox: Any, path: str) -> Any:
    """Risolve "Inbox" o un percorso tipo "Inbox/Televisite"."""
    parts = [part.strip() for part in re.split(r"[\\/]", path) if part.strip()]
    if not parts or parts[0].lower() in _INBOX_NAMES:
        folder = mailbox.inbox_folder()
        parts = parts[1:] if parts else []
    else:
        folder = mailbox.get_folder(folder_name=parts[0])
        parts = parts[1:]

    for part in parts:
        if folder is None:
            break
        folder = folder.get_folder(folder_name=part)

    if folder is None:
        raise OutlookError(f"Cartella non trovata nella casella: {path!r}")
    return folder


def _iter_attachments(attachments: Any) -> Iterable[Any]:
    try:
        return list(attachments)
    except TypeError:  # collection non iterabile (non dovrebbe accadere)
        return []


def _format_note(note: str, body_type: str) -> str:
    """Prepara la nota da anteporre al corpo, nel formato del messaggio."""
    if body_type.lower() != "html":
        return f"{note}\r\n"
    escaped = (
        note.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    )
    return f"<p>{escaped}</p>"


def _sanitize_filename(name: str, index: int) -> str:
    """Ripulisce il nome fornito dal mittente prima di scriverlo su disco."""
    name = Path(name).name  # neutralizza eventuali percorsi ("../../x.pdf")
    name = _UNSAFE_FILENAME_CHARS.sub("_", name).strip(" .")
    if not name:
        name = f"allegato_{index}"
    return name[:120]


def _unique_path(directory: Path, filename: str) -> Path:
    """Evita che due allegati omonimi si sovrascrivano."""
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem, suffix = candidate.stem, candidate.suffix
    counter = 2
    while True:
        candidate = directory / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
