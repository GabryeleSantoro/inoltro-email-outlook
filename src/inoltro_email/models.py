"""Strutture dati condivise fra i moduli.

Sono tutte dataclass semplici, senza dipendenze da rete o da un framework
web, cosi' possono essere costruite liberamente nei test.

Il flusso del servizio le attraversa in quest'ordine:

    InboundEmail -> ScreeningReport -> AttachmentAnalysis* -> SentimentScore
                 -> EmailAnalysis (la risposta HTTP)
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


class Esito(str, Enum):
    """Esito complessivo dell'analisi di un messaggio."""

    CONFORME = "conforme"  # screening superato e contenuto con tutti i criteri
    NON_CONFORME = "non_conforme"  # screening superato, contenuto senza i criteri
    SCARTATA = "scartata"  # oggetto e corpo non parlano di telemedicina
    SENZA_CONTENUTO = "senza_contenuto"  # nessun allegato o foto analizzabile
    ERRORE = "errore"  # analisi interrotta da un errore


class Origine(str, Enum):
    """Provenienza di un'immagine o di un documento analizzato."""

    ALLEGATO = "allegato"  # allegato vero e proprio
    CORPO = "corpo"  # foto incorporata nel corpo del messaggio


@dataclass
class InboundAttachment:
    """Allegato ricevuto da Power Automate.

    Arriva in due forme, entrambe supportate:

    * ``content`` valorizzato -> il file viaggia in base64 dentro il payload;
    * ``source_path`` valorizzato -> il payload porta solo il percorso del file
      (campo ``attchment`` del flusso Power Automate) e il file sta gia' su
      disco: non lo si ricopia, lo si manda all'OCR da dove si trova.
    """

    name: str
    content: bytes = b""
    content_type: str = ""
    origine: Origine = Origine.ALLEGATO
    source_path: Optional[Path] = None

    @property
    def extension(self) -> str:
        return Path(self.name).suffix.lower()

    @property
    def size_bytes(self) -> int:
        if self.content:
            return len(self.content)
        if self.source_path is not None:
            try:
                return self.source_path.stat().st_size
            except OSError:
                return 0
        return 0

    @property
    def has_content(self) -> bool:
        """C'e' qualcosa da leggere: byte in memoria o un file raggiungibile."""
        if self.content:
            return True
        return self.source_path is not None and self.source_path.is_file()


@dataclass
class InboundEmail:
    """Email singola inviata dal flusso Power Automate.

    ``body_text`` e' sempre testo semplice: se il corpo arriva in HTML viene
    ripulito da ``inbound.py`` prima di costruire questo oggetto.
    """

    subject: str = ""
    body_text: str = ""
    body_html: str = ""
    message_id: str = ""
    internet_message_id: str = ""
    sender: str = ""
    received_at: str = ""
    attachments: List[InboundAttachment] = field(default_factory=list)
    # Problemi non bloccanti trovati nel payload: percorsi di allegati non
    # raggiungibili, corpo non risolto dal flusso, riparazioni al JSON.
    warnings: List[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        """Identificativo usato nei log e nella risposta."""
        return (self.internet_message_id or self.message_id or "").strip() or "(senza id)"

    @property
    def screening_text(self) -> str:
        """Oggetto e corpo insieme: e' cio' su cui si fa la prima verifica."""
        return f"{self.subject}\n{self.body_text}".strip()


@dataclass
class AttachmentFile:
    """Allegato salvato su disco, pronto per essere analizzato."""

    path: Path
    original_name: str
    size_bytes: int
    origine: Origine = Origine.ALLEGATO

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
    """Esito del confronto fra un testo e le regole configurate."""

    matched: bool
    found_keywords: List[str] = field(default_factory=list)
    found_codes: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    missing_codes: List[str] = field(default_factory=list)

    @property
    def found(self) -> List[str]:
        return self.found_keywords + self.found_codes

    @property
    def missing(self) -> List[str]:
        return self.missing_keywords + self.missing_codes

    def summary(self) -> str:
        found = ", ".join(self.found) or "-"
        missing = ", ".join(self.missing) or "-"
        return f"trovati=[{found}] mancanti=[{missing}]"


@dataclass
class ScreeningReport:
    """Prima verifica: telemedicina/televisita nell'oggetto o nel corpo."""

    passed: bool
    in_subject: List[str] = field(default_factory=list)
    in_body: List[str] = field(default_factory=list)

    @property
    def terms(self) -> List[str]:
        """Termini riconosciuti, senza ripetizioni e in ordine stabile."""
        seen: List[str] = []
        for term in self.in_subject + self.in_body:
            if term not in seen:
                seen.append(term)
        return seen

    @property
    def where(self) -> List[str]:
        places: List[str] = []
        if self.in_subject:
            places.append("oggetto")
        if self.in_body:
            places.append("corpo")
        return places


@dataclass
class AttachmentAnalysis:
    """Esito della lettura di un singolo allegato o di una foto del corpo."""

    name: str
    origine: Origine
    source: TextSource
    chars: int = 0
    match: Optional[MatchReport] = None
    error: Optional[str] = None

    @property
    def matched(self) -> bool:
        return bool(self.match and self.match.matched)


@dataclass
class BookingScore:
    """Quanto il messaggio somiglia a una prenotazione di telemedicina."""

    score: float  # da 0 (per nulla) a 1 (certamente una prenotazione)
    is_booking: bool
    signals: List[str] = field(default_factory=list)


@dataclass
class Evidence:
    """Un singolo indizio che sposta la percentuale di sicurezza.

    ``weight`` e' espresso in log-odds: positivo se l'indizio depone a favore,
    negativo se depone contro. La somma dei pesi diventa una percentuale.
    """

    label: str
    where: str  # oggetto | corpo | citato | allegati | documento | indirizzi
    weight: float


@dataclass
class ConfidenceScore:
    """Quanto il servizio e' sicuro di un'affermazione, in percentuale."""

    percent: float  # da 0 a 100
    level: str  # "molto alta" | "alta" | "media" | "bassa" | "molto bassa"
    holds: bool  # la percentuale supera la soglia configurata
    evidence: List[Evidence] = field(default_factory=list)

    @property
    def positives(self) -> List[Evidence]:
        return [item for item in self.evidence if item.weight > 0]

    @property
    def negatives(self) -> List[Evidence]:
        return [item for item in self.evidence if item.weight < 0]

    def summary(self) -> str:
        return f"{self.percent:.1f}% ({self.level})"


@dataclass
class SentimentScore:
    """Polarita' del testo piu' l'intento di prenotazione."""

    score: float  # da -1 (negativo) a +1 (positivo)
    label: str  # "positivo" | "neutro" | "negativo"
    positive_terms: List[str] = field(default_factory=list)
    negative_terms: List[str] = field(default_factory=list)
    booking: BookingScore = field(
        default_factory=lambda: BookingScore(score=0.0, is_booking=False)
    )


@dataclass
class EmailAnalysis:
    """Risultato completo restituito dal servizio HTTP."""

    message_key: str
    subject: str
    esito: Esito
    screening: ScreeningReport
    sentiment: SentimentScore
    telemedicina: ConfidenceScore
    prenotazione: ConfidenceScore
    attachments: List[AttachmentAnalysis] = field(default_factory=list)
    matched_attachment: Optional[str] = None
    match: Optional[MatchReport] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def conforme(self) -> bool:
        return self.esito is Esito.CONFORME

    @property
    def e_prenotazione_telemedicina(self) -> bool:
        """Verdetto richiesto dal flusso: e' una prenotazione di telemedicina?"""
        return self.telemedicina.holds and self.prenotazione.holds
