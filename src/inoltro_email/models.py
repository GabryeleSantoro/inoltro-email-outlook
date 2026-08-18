"""Strutture dati condivise fra i moduli.

Sono tutte dataclass semplici, senza dipendenze da Windows o da rete, cosi'
possono essere costruite liberamente nei test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TextSource(str, Enum):
    """Da dove arriva il testo di un allegato."""

    PDF_TEXT = "pdf_text"  # livello di testo gia' presente nel PDF
    OCR = "ocr"  # estratto da ocr.space
    SKIPPED = "skipped"  # allegato non analizzato (estensione/dimensione)
    ERROR = "error"  # estrazione fallita


class Decision(str, Enum):
    """Esito dell'elaborazione di un messaggio."""

    FORWARDED = "forwarded"
    FORWARDED_DRY_RUN = "forwarded_dry_run"
    NO_MATCH = "no_match"
    SKIPPED_DUPLICATE = "skipped_duplicate"
    SKIPPED_NO_ATTACHMENT = "skipped_no_attachment"
    ERROR = "error"


@dataclass
class AttachmentFile:
    """Allegato salvato su disco, pronto per essere analizzato."""

    path: Path
    original_name: str
    size_bytes: int

    @property
    def extension(self) -> str:
        return self.path.suffix.lower()


@dataclass
class OcrResult:
    """Risposta di ocr.space per un singolo file."""

    text: str
    exit_code: int
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedText:
    """Testo ricavato da un allegato, con la provenienza e l'eventuale errore."""

    attachment: AttachmentFile
    text: str
    source: TextSource
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.source in (TextSource.PDF_TEXT, TextSource.OCR)


@dataclass
class MatchReport:
    """Esito del confronto fra testo estratto e regole configurate."""

    matched: bool
    found_keywords: List[str] = field(default_factory=list)
    found_codes: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    missing_codes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        found = ", ".join(self.found_keywords + self.found_codes) or "-"
        missing = ", ".join(self.missing_keywords + self.missing_codes) or "-"
        return f"trovati=[{found}] mancanti=[{missing}]"


@dataclass
class ProcessResult:
    """Risultato completo dell'elaborazione di un messaggio."""

    message_key: str
    subject: str
    decision: Decision
    match: Optional[MatchReport] = None
    matched_attachment: Optional[str] = None
    error: Optional[str] = None
    extractions: List[ExtractedText] = field(default_factory=list)

    @property
    def forwarded(self) -> bool:
        return self.decision in (Decision.FORWARDED, Decision.FORWARDED_DRY_RUN)
