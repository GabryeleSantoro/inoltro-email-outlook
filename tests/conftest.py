"""Fixture condivise: configurazione di prova, OCR fittizio, payload di esempio."""

from __future__ import annotations

import base64
import io
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from inoltro_email.config import (
    ApiSettings, AttachmentSettings, LoggingSettings, OcrSettings, RuleSettings,
    ScreeningSettings, SentimentSettings, Settings,
)
from inoltro_email.models import OcrResult


@pytest.fixture
def settings() -> Settings:
    """Configurazione minima e coerente per i test."""
    return Settings(
        api=ApiSettings(host="127.0.0.1", port=8123, api_key=""),
        screening=ScreeningSettings(keywords=["telemedicina", "televisita"], mode="any"),
        rules=RuleSettings(keywords=["telemedicina"], codes=["1501A"], mode="all"),
        ocr=OcrSettings(
            api_key="chiave-di-prova",
            endpoint="https://api.ocr.space/parse/image",
            engine=2,
            max_retries=3,
            timeout_seconds=5,
            max_file_bytes=1_048_576,
            max_pdf_pages_per_request=3,
        ),
        attachments=AttachmentSettings(max_bytes=10_485_760),
        sentiment=SentimentSettings(),
        logging=LoggingSettings(level="DEBUG", file=None),
    )


class FakeOcrClient:
    """Restituisce testi predefiniti per nome file e conta le chiamate."""

    def __init__(self, texts: Optional[Dict[str, str]] = None, default_text: str = "") -> None:
        self.texts = texts or {}
        self.default_text = default_text
        self.calls: List[str] = []
        # Dimensione di cio' che e' stato davvero inviato: serve a verificare
        # che un'immagine ridimensionata arrivi sotto il limite dell'API.
        self.sizes: List[int] = []

    def parse_file(self, path: Path) -> OcrResult:
        path = Path(path)
        self.calls.append(path.name)
        self.sizes.append(path.stat().st_size if path.is_file() else 0)
        for fragment, text in self.texts.items():
            if fragment in path.name:
                return OcrResult(text=text, exit_code=1)
        return OcrResult(text=self.default_text, exit_code=1)


@pytest.fixture
def fake_ocr() -> FakeOcrClient:
    return FakeOcrClient()


# ------------------------------------------------------- payload di esempio


def b64(content: bytes) -> str:
    return base64.b64encode(content).decode("ascii")


def attachment_payload(
    name: str,
    content: bytes,
    *,
    content_type: str = "application/pdf",
    inline: bool = False,
) -> Dict[str, Any]:
    """Allegato nella forma prodotta dal connettore Office 365 Outlook."""
    return {
        "name": name,
        "contentType": content_type,
        "contentBytes": b64(content),
        "size": len(content),
        "isInline": inline,
    }


def email_payload(
    subject: str = "Richiesta prenotazione televisita",
    body: str = "Buongiorno, vorrei prenotare una televisita. In allegato l'impegnativa. Grazie.",
    attachments: Optional[List[Dict[str, Any]]] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Payload come quello inviato dall'azione HTTP di Power Automate."""
    payload: Dict[str, Any] = {
        "id": "AAMkAGI2TEST",
        "internetMessageId": "<msg-1@example.com>",
        "subject": subject,
        "body": body,
        "isHtml": False,
        "from": "paziente@example.com",
        "receivedDateTime": "2026-08-19T08:00:00Z",
        "hasAttachment": bool(attachments),
        "attachments": attachments or [],
    }
    payload.update(extra)
    return payload


# ------------------------------------------------------------ file di prova


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


def make_photo(width: int = 2400, height: int = 1800) -> bytes:
    """PNG che si comporta come una foto scattata col telefono.

    Serve un'immagine con struttura continua: il rumore puro non si comprime
    in nessun formato e sarebbe il caso peggiore possibile, una tinta unita si
    comprimerebbe a pochi byte e non proverebbe nulla. Una macchia di colori
    ingrandita ha la stessa natura di una foto - PNG pesante, JPEG leggero -
    ed e' immediata da costruire.
    """
    import random

    from PIL import Image

    generatore = random.Random(12345)  # stessa immagine a ogni esecuzione
    seme = Image.new("RGB", (60, 45))
    seme.putdata([
        (generatore.randint(0, 255), generatore.randint(0, 255), generatore.randint(0, 255))
        for _ in range(60 * 45)
    ])
    buffer = io.BytesIO()
    seme.resize((width, height), Image.BICUBIC).save(buffer, format="PNG")
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
