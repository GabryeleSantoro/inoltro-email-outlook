"""Client COM per Outlook Desktop.

``win32com`` viene importato dentro ``connect()`` e non a livello di modulo:
in questo modo il file resta importabile su Linux/macOS (utile per i test e
per il comando ``check-file``), e fallisce con un messaggio chiaro solo se si
prova davvero a collegarsi a Outlook fuori da Windows.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional

from ..models import AttachmentFile

logger = logging.getLogger(__name__)

OL_FOLDER_INBOX = 6
OL_MAIL_ITEM = "IPM.Note"
OL_ATTACHMENT_BY_VALUE = 1

PR_INTERNET_MESSAGE_ID = "http://schemas.microsoft.com/mapi/proptag/0x1035001F"
PR_ATTACH_CONTENT_ID = "http://schemas.microsoft.com/mapi/proptag/0x3712001F"

# Quanti elementi al massimo scorrere durante il recupero all'avvio: evita di
# percorrere per intero una Posta in arrivo con decine di migliaia di messaggi.
MAX_SCAN_ITEMS = 500

_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff"}


class OutlookError(Exception):
    """Errore di connessione o di dialogo con Outlook."""


class OutlookMessage:
    """Adattatore attorno a un MailItem COM che implementa ``MailMessage``."""

    def __init__(self, com_item: Any) -> None:
        self.com_item = com_item

    @property
    def entry_id(self) -> str:
        return _safe_get(self.com_item, "EntryID", "")

    @property
    def message_id(self) -> str:
        """Internet Message-ID; stringa vuota se non disponibile."""
        try:
            value = self.com_item.PropertyAccessor.GetProperty(PR_INTERNET_MESSAGE_ID)
            return str(value or "").strip()
        except Exception:  # noqa: BLE001 - proprieta' assente su alcuni elementi
            return ""

    @property
    def subject(self) -> str:
        return _safe_get(self.com_item, "Subject", "")

    @property
    def sender(self) -> str:
        return _safe_get(self.com_item, "SenderEmailAddress", "") or _safe_get(
            self.com_item, "SenderName", ""
        )

    @property
    def has_attachments(self) -> bool:
        try:
            return self.com_item.Attachments.Count > 0
        except Exception:  # noqa: BLE001
            return False

    @property
    def received_time(self) -> Optional[datetime]:
        try:
            value = self.com_item.ReceivedTime
            return datetime(value.year, value.month, value.day, value.hour, value.minute, value.second)
        except Exception:  # noqa: BLE001
            return None


class OutlookClient:
    """Implementazione COM del protocollo ``MailClient``."""

    def __init__(self, folder_path: str = "Inbox", allowed_extensions: Optional[List[str]] = None) -> None:
        self._folder_path = folder_path
        self._allowed_extensions = {ext.lower() for ext in (allowed_extensions or [])}
        self._app: Any = None
        self._namespace: Any = None
        self._folder: Any = None

    # ------------------------------------------------------------ connessione

    def connect(self) -> None:
        """Si aggancia all'istanza di Outlook in esecuzione (o la avvia)."""
        try:
            import win32com.client  # noqa: PLC0415 - import volutamente tardivo
        except ImportError as exc:
            raise OutlookError(
                "pywin32 non disponibile: la modalita' Outlook funziona solo su Windows "
                "con Outlook Desktop installato (pip install pywin32)."
            ) from exc

        try:
            self._app = win32com.client.Dispatch("Outlook.Application")
            self._namespace = self._app.GetNamespace("MAPI")
            self._folder = self._resolve_folder(self._folder_path)
        except Exception as exc:  # noqa: BLE001 - pywintypes.com_error e simili
            raise OutlookError(f"Impossibile collegarsi a Outlook: {exc}") from exc

        logger.info("Collegato a Outlook, cartella sorvegliata: %s", self._folder_path)

    @property
    def namespace(self) -> Any:
        if self._namespace is None:
            raise OutlookError("Client non connesso: chiamare prima connect().")
        return self._namespace

    def _resolve_folder(self, path: str) -> Any:
        """Risolve "Inbox" o un percorso tipo "Inbox/Televisite"."""
        parts = [part for part in re.split(r"[\\/]", path) if part.strip()]
        if not parts or parts[0].lower() in ("inbox", "posta in arrivo"):
            folder = self._namespace.GetDefaultFolder(OL_FOLDER_INBOX)
            parts = parts[1:] if parts else []
        else:
            folder = self._namespace.Folders(parts[0])
            parts = parts[1:]

        for part in parts:
            folder = folder.Folders(part)
        return folder

    # -------------------------------------------------------------- messaggi

    def get_message(self, entry_id: str) -> Optional[OutlookMessage]:
        try:
            item = self.namespace.GetItemFromID(entry_id)
        except Exception as exc:  # noqa: BLE001 - messaggio spostato o cancellato
            logger.warning("EntryID %s non recuperabile: %s", entry_id, exc)
            return None
        if not _is_mail_item(item):
            logger.debug("EntryID %s non e' un messaggio di posta, ignorato.", entry_id)
            return None
        return OutlookMessage(item)

    def recent_messages(self, minutes: int) -> List[OutlookMessage]:
        """Messaggi ricevuti negli ultimi ``minutes`` minuti.

        Si ordina per data decrescente e si interrompe al primo messaggio piu'
        vecchio della soglia: evita sia i problemi di formato data di
        ``Restrict`` (che dipende dalle impostazioni locali di Windows) sia la
        scansione dell'intera cartella.
        """
        if minutes <= 0:
            return []

        threshold = datetime.now() - timedelta(minutes=minutes)
        items = self._folder.Items
        items.Sort("[ReceivedTime]", True)

        messages: List[OutlookMessage] = []
        item = items.GetFirst()
        scanned = 0
        while item is not None and scanned < MAX_SCAN_ITEMS:
            scanned += 1
            message = OutlookMessage(item)
            received = message.received_time
            if received is not None and received < threshold:
                break
            if _is_mail_item(item):
                messages.append(message)
            item = items.GetNext()

        logger.info("Recupero iniziale: %d messaggi negli ultimi %d minuti.", len(messages), minutes)
        return messages

    # -------------------------------------------------------------- allegati

    def save_attachments(self, message: OutlookMessage, dest_dir: Path) -> List[AttachmentFile]:
        """Salva su disco gli allegati analizzabili del messaggio."""
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        saved: List[AttachmentFile] = []

        try:
            attachments = message.com_item.Attachments
            count = attachments.Count
        except Exception as exc:  # noqa: BLE001
            logger.warning("Allegati non leggibili per '%s': %s", message.subject, exc)
            return saved

        for index in range(1, count + 1):  # le collection COM partono da 1
            try:
                attachment = attachments.Item(index)
                original_name = str(attachment.FileName or f"allegato_{index}")

                if _safe_get(attachment, "Type", OL_ATTACHMENT_BY_VALUE) != OL_ATTACHMENT_BY_VALUE:
                    logger.debug("Allegato '%s' non e' un file incorporato, ignorato.", original_name)
                    continue

                extension = Path(original_name).suffix.lower()
                if self._allowed_extensions and extension not in self._allowed_extensions:
                    logger.debug("Allegato '%s' di tipo non previsto, ignorato.", original_name)
                    continue
                if extension in _IMAGE_EXTENSIONS and _is_inline(attachment):
                    # Tipicamente il logo della firma: non e' un documento.
                    logger.debug("Immagine incorporata nel corpo '%s', ignorata.", original_name)
                    continue

                target = _unique_path(dest_dir, _sanitize_filename(original_name, index))
                attachment.SaveAsFile(str(target))
                saved.append(
                    AttachmentFile(
                        path=target,
                        original_name=original_name,
                        size_bytes=target.stat().st_size,
                    )
                )
                logger.info("Allegato salvato: %s (%d byte)", original_name, target.stat().st_size)
            except Exception as exc:  # noqa: BLE001 - un allegato rotto non blocca gli altri
                logger.warning("Allegato %d di '%s' non salvato: %s", index, message.subject, exc)

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
            forwarded = message.com_item.Forward()
            forwarded.To = "; ".join(to)
            if cc:
                forwarded.CC = "; ".join(cc)
            if subject_prefix:
                forwarded.Subject = f"{subject_prefix}{forwarded.Subject}"
            if body_note:
                forwarded.Body = f"{body_note}\r\n\r\n{forwarded.Body}"
            forwarded.Send()
        except Exception as exc:  # noqa: BLE001
            raise OutlookError(f"Inoltro non riuscito per '{message.subject}': {exc}") from exc

        logger.info("Messaggio '%s' inoltrato a %s", message.subject, ", ".join(to))

    def mark_processed(self, message: OutlookMessage, category: str) -> None:
        """Aggiunge una categoria al messaggio (traccia visibile in Outlook)."""
        if not category:
            return
        try:
            existing = _safe_get(message.com_item, "Categories", "") or ""
            categories = [item.strip() for item in existing.split(",") if item.strip()]
            if category not in categories:
                categories.append(category)
                message.com_item.Categories = ", ".join(categories)
                message.com_item.Save()
        except Exception as exc:  # noqa: BLE001 - marcatura non essenziale
            logger.warning("Categoria non applicata a '%s': %s", message.subject, exc)


# ------------------------------------------------------------------- utili


def _is_mail_item(item: Any) -> bool:
    """True se l'elemento e' un normale messaggio di posta.

    Nella Posta in arrivo finiscono anche convocazioni di riunione, rapporti di
    mancato recapito e altri tipi che non espongono la stessa interfaccia.
    """
    try:
        return str(item.MessageClass or "").startswith(OL_MAIL_ITEM)
    except Exception:  # noqa: BLE001
        return False


def _is_inline(attachment: Any) -> bool:
    """True se l'allegato e' un'immagine incorporata nel corpo del messaggio."""
    try:
        content_id = attachment.PropertyAccessor.GetProperty(PR_ATTACH_CONTENT_ID)
        return bool(str(content_id or "").strip())
    except Exception:  # noqa: BLE001 - proprieta' assente = allegato normale
        return False


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


def _safe_get(com_object: Any, attribute: str, default: Any = None) -> Any:
    try:
        value = getattr(com_object, attribute)
        return default if value is None else value
    except Exception:  # noqa: BLE001
        return default
