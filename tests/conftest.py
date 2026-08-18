"""Fixture condivise: configurazione di prova, client Outlook e OCR fittizi."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from inoltro_email.config import (
    AttachmentSettings, ForwardSettings, LoggingSettings, OcrSettings,
    OutlookSettings, RuleSettings, Settings, StorageSettings,
)
from inoltro_email.models import AttachmentFile, OcrResult


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Configurazione minima e coerente per i test."""
    return Settings(
        ocr=OcrSettings(
            api_key="chiave-di-prova",
            endpoint="https://api.ocr.space/parse/image",
            engine=2,
            max_retries=3,
            timeout_seconds=5,
            max_file_bytes=1_048_576,
            max_pdf_pages_per_request=3,
        ),
        rules=RuleSettings(keywords=["televisita"], codes=["1501A"], mode="all"),
        forward=ForwardSettings(
            to=["destinatario@example.com"],
            subject_prefix="[TELEVISITA] ",
            body_note="Inoltro automatico.",
            dry_run=False,
        ),
        outlook=OutlookSettings(catch_up_minutes=30, processed_category="Inoltrata"),
        attachments=AttachmentSettings(max_bytes=10_485_760),
        storage=StorageSettings(db_path=tmp_path / "state.sqlite3"),
        logging=LoggingSettings(level="DEBUG", file=None),
    )


class FakeOcrClient:
    """Restituisce testi predefiniti per nome file e conta le chiamate."""

    def __init__(self, texts: Optional[Dict[str, str]] = None, default_text: str = "") -> None:
        self.texts = texts or {}
        self.default_text = default_text
        self.calls: List[str] = []

    def parse_file(self, path: Path) -> OcrResult:
        path = Path(path)
        self.calls.append(path.name)
        for fragment, text in self.texts.items():
            if fragment in path.name:
                return OcrResult(text=text, exit_code=1)
        return OcrResult(text=self.default_text, exit_code=1)


class FakeMessage:
    """Messaggio di posta finto conforme al protocollo MailMessage."""

    def __init__(
        self,
        subject: str = "Richiesta",
        message_id: str = "<msg-1@example.com>",
        entry_id: str = "ENTRY1",
        attachments: Optional[Dict[str, bytes]] = None,
        sender: str = "mittente@example.com",
    ) -> None:
        self.subject = subject
        self.message_id = message_id
        self.entry_id = entry_id
        self.sender = sender
        self.attachments = attachments or {}

    @property
    def has_attachments(self) -> bool:
        return bool(self.attachments)


class FakeMailClient:
    """Client Outlook finto: registra inoltri e categorie applicate."""

    def __init__(self, messages: Optional[List[FakeMessage]] = None) -> None:
        self.messages = messages or []
        self.forwarded: List[Dict[str, object]] = []
        self.categories: List[str] = []

    def get_message(self, entry_id: str) -> Optional[FakeMessage]:
        return next((m for m in self.messages if m.entry_id == entry_id), None)

    def recent_messages(self, minutes: int) -> List[FakeMessage]:
        return list(self.messages)

    def save_attachments(self, message: FakeMessage, dest_dir: Path) -> List[AttachmentFile]:
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        saved = []
        for name, content in message.attachments.items():
            target = dest_dir / name
            target.write_bytes(content)
            saved.append(AttachmentFile(target, name, len(content)))
        return saved

    def forward(self, message, to, cc, subject_prefix, body_note) -> None:
        self.forwarded.append({
            "subject": message.subject, "to": list(to), "cc": list(cc),
            "prefix": subject_prefix, "note": body_note,
        })

    def mark_processed(self, message, category: str) -> None:
        if category:
            self.categories.append(category)


@pytest.fixture
def fake_ocr() -> FakeOcrClient:
    return FakeOcrClient()


def make_pdf(text_pages: List[str]) -> bytes:
    """PDF con un vero livello di testo, una pagina per elemento."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    font = writer._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    }))
    for text in text_pages:
        page = writer.add_blank_page(width=595, height=842)
        # Flusso di contenuto PDF minimo che disegna il testo indicato.
        escaped = text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 50 700 Td ({escaped}) Tj ET".encode("latin-1"))
        page[NameObject("/Contents")] = writer._add_object(stream)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
        })
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def make_blank_pdf(pages: int = 1) -> bytes:
    """PDF senza alcun testo: simula una scansione da mandare all'OCR."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()
