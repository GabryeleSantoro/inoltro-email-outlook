"""Interfacce fra la pipeline e Outlook.

La pipeline non conosce COM: dipende soltanto dai Protocol definiti qui. In
produzione li implementa ``OutlookClient``; nei test un oggetto finto. Questo
tiene la logica di business testabile su qualsiasi sistema operativo.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Protocol, runtime_checkable

from ..models import AttachmentFile


@runtime_checkable
class MailMessage(Protocol):
    """Il minimo che serve alla pipeline per trattare un messaggio."""

    @property
    def entry_id(self) -> str:
        """Identificativo Outlook, valido finche' il messaggio resta dov'e'."""

    @property
    def message_id(self) -> str:
        """Internet Message-ID: stabile fra riavvii e spostamenti di cartella."""

    @property
    def subject(self) -> str: ...

    @property
    def sender(self) -> str: ...

    @property
    def has_attachments(self) -> bool: ...


@runtime_checkable
class MailClient(Protocol):
    """Operazioni sulla casella richieste dalla pipeline."""

    def get_message(self, entry_id: str) -> Optional[MailMessage]:
        """Recupera un messaggio dal suo EntryID (None se non piu' esistente)."""

    def recent_messages(self, minutes: int) -> List[MailMessage]:
        """Messaggi ricevuti negli ultimi ``minutes`` minuti, dal piu' recente."""

    def save_attachments(self, message: MailMessage, dest_dir: Path) -> List[AttachmentFile]:
        """Salva gli allegati analizzabili in ``dest_dir``."""

    def forward(
        self,
        message: MailMessage,
        to: List[str],
        cc: List[str],
        subject_prefix: str,
        body_note: str,
    ) -> None:
        """Inoltra il messaggio originale ai destinatari indicati."""

    def mark_processed(self, message: MailMessage, category: str) -> None:
        """Applica una categoria al messaggio, come traccia visibile in Outlook."""
