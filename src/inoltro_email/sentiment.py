"""Punteggio di sentiment e intento di prenotazione.

Due misure distinte, calcolate sullo stesso testo (oggetto + corpo):

* **sentiment** - polarita' del messaggio, da -1 (negativo) a +1 (positivo).
  Serve a distinguere "vorrei prenotare, grazie mille" da "e' la terza volta
  che scrivo, servizio pessimo".
* **prenotazione** - da 0 a 1, quanto il messaggio somiglia alla richiesta di
  prenotare una telemedicina. E' un punteggio a indizi: ogni termine
  riconosciuto porta il suo peso, le richieste di disdetta lo abbassano.

Il calcolo e' deterministico e senza dipendenze esterne: nessuna chiamata di
rete, nessun modello da scaricare, quindi la risposta HTTP resta immediata e
il risultato e' sempre spiegabile (i termini che lo hanno determinato sono
riportati nella risposta).
"""

from __future__ import annotations

import re
from typing import Dict, List, Sequence, Tuple

from .config import SentimentSettings
from .matching import normalize
from .models import BookingScore, SentimentScore

# --- polarita' -------------------------------------------------------------
# Forme flesse elencate per esteso: piu' righe, ma nessun falso positivo del
# tipo "contenuto" riconosciuto come "contento".

POSITIVE_TERMS: Dict[str, float] = {
    "grazie": 0.6, "ringrazio": 0.6, "ringraziandovi": 0.6, "ringraziamenti": 0.5,
    "gentilmente": 0.5, "gentile": 0.4, "cortesemente": 0.5, "cortese": 0.4,
    "ottimo": 0.8, "ottima": 0.8, "eccellente": 0.9, "perfetto": 0.8, "perfetta": 0.8,
    "felice": 0.7, "contento": 0.6, "contenta": 0.6, "soddisfatto": 0.8, "soddisfatta": 0.8,
    "volentieri": 0.5, "apprezzo": 0.6, "apprezzato": 0.6, "utile": 0.4, "utilissimo": 0.7,
    "comodo": 0.4, "comoda": 0.4, "efficiente": 0.6, "veloce": 0.4, "puntuale": 0.5,
    "risolto": 0.6, "chiarissimo": 0.6, "gradita": 0.4, "gradito": 0.4, "grato": 0.5,
}

NEGATIVE_TERMS: Dict[str, float] = {
    "reclamo": 0.9, "lamentela": 0.8, "lamento": 0.6, "disservizio": 0.9, "disservizi": 0.9,
    "inaccettabile": 1.0, "vergognoso": 1.0, "vergogna": 1.0, "scandaloso": 1.0,
    "pessimo": 1.0, "pessima": 1.0, "terribile": 0.9, "assurdo": 0.8, "assurda": 0.8,
    "deluso": 0.8, "delusa": 0.8, "delusione": 0.8, "scontento": 0.8, "arrabbiato": 0.9,
    "insoddisfatto": 0.9, "insoddisfatta": 0.9, "protesta": 0.7,
    "ritardo": 0.6, "ritardi": 0.6, "problema": 0.5, "problemi": 0.5, "guasto": 0.5,
    "errore": 0.6, "errata": 0.6, "errato": 0.6, "sbagliato": 0.6, "sbagliata": 0.6,
    "impossibile": 0.6, "difficolta": 0.5, "malfunzionamento": 0.7,
    "preoccupato": 0.5, "preoccupata": 0.5, "inutile": 0.7,
}

# "non sono soddisfatto" deve pesare come un negativo, non come un positivo.
NEGATIONS = frozenset({"non", "mai", "senza", "ne", "niente", "nulla", "nessun", "nessuna", "nessuno"})
INTENSIFIERS = frozenset({"molto", "davvero", "veramente", "estremamente", "assolutamente",
                          "particolarmente", "parecchio", "troppo", "decisamente"})
NEGATION_WINDOW = 3  # quante parole prima si guarda per trovare una negazione
NEGATION_FACTOR = -0.8  # la negazione ribalta il segno, ma attenua l'intensita'
INTENSIFIER_FACTOR = 1.5

# --- intento di prenotazione ----------------------------------------------
# Ogni indizio ha un peso; la somma, troncata a 1, e' il punteggio.

BOOKING_SIGNALS: Sequence[Tuple[str, str, float]] = (
    # (espressione regolare sul testo normalizzato, etichetta, peso)
    (r"\bprenot\w*", "prenotazione", 0.40),
    (r"\bappuntament\w*", "appuntamento", 0.30),
    (r"\bfissare\b|\bfissiamo\b|\bfissato\b", "fissare un appuntamento", 0.25),
    (r"\bdisponibil\w*", "richiesta di disponibilita", 0.15),
    (r"\bagenda\b|\bcalendario\b|\bslot\b", "agenda", 0.10),
    (r"\bdata\b|\bdate\b|\borari\w*", "data o orario", 0.10),
    (r"\btelemedicin\w*|\btelevisit\w*", "telemedicina", 0.25),
    (r"\bvideoconsult\w*|\bvideochiamat\w*|\bvisita a distanza\b", "visita a distanza", 0.20),
    (r"\bimpegnativ\w*|\bricett\w*|\bprescrizion\w*", "impegnativa", 0.20),
    (r"\b1501a\b", "codice 1501A", 0.20),
    (r"\bvorrei\b|\bchiedo\b|\brichiedo\b|\brichiesta\b|\bpotrei\b", "richiesta esplicita", 0.10),
    (r"\bpaziente\b|\bassistit\w*|\bcodice fiscale\b|\btessera sanitaria\b", "dati del paziente", 0.10),
)

# Chi scrive per disdire non sta prenotando: i pesi sono alti apposta, devono
# poter azzerare gli indizi di prenotazione contenuti nello stesso messaggio
# ("vorrei disdire l'appuntamento prenotato").
CANCEL_SIGNALS: Sequence[Tuple[str, str, float]] = (
    (r"\bdisdet\w*|\bdisdire\b", "disdetta", 0.90),
    (r"\bannull\w*", "annullamento", 0.80),
    (r"\bcancell\w*", "cancellazione", 0.70),
    (r"\bspostare\b|\brimandare\b|\brinviare\b", "spostamento", 0.30),
)

_TOKEN = re.compile(r"[a-z0-9]+")


def analyze_sentiment(
    text: str,
    settings: SentimentSettings,
    *,
    attachment_matched: bool = False,
) -> SentimentScore:
    """Calcola polarita' e intento di prenotazione del testo indicato."""
    normalized = normalize(text)
    score, positives, negatives = _polarity(normalized)
    booking = _booking(normalized, settings, attachment_matched=attachment_matched)

    return SentimentScore(
        score=score,
        label=_label(score, settings),
        positive_terms=positives,
        negative_terms=negatives,
        booking=booking,
    )


# ---------------------------------------------------------------- polarita'


def _polarity(normalized: str) -> Tuple[float, List[str], List[str]]:
    tokens = _TOKEN.findall(normalized)
    positive_total = 0.0
    negative_total = 0.0
    positives: List[str] = []
    negatives: List[str] = []

    for index, token in enumerate(tokens):
        weight = POSITIVE_TERMS.get(token)
        polarity = 1.0
        if weight is None:
            weight = NEGATIVE_TERMS.get(token)
            polarity = -1.0
        if weight is None:
            continue

        context = tokens[max(0, index - NEGATION_WINDOW):index]
        if any(word in NEGATIONS for word in context):
            polarity *= NEGATION_FACTOR
        if context and context[-1] in INTENSIFIERS:
            weight *= INTENSIFIER_FACTOR

        value = weight * polarity
        if value >= 0:
            positive_total += value
            positives.append(token)
        else:
            negative_total += -value
            negatives.append(token)

    total = positive_total + negative_total
    score = 0.0 if total == 0 else (positive_total - negative_total) / total
    return round(_clamp(score, -1.0, 1.0), 3), _unique(positives), _unique(negatives)


def _label(score: float, settings: SentimentSettings) -> str:
    if score >= settings.positive_threshold:
        return "positivo"
    if score <= settings.negative_threshold:
        return "negativo"
    return "neutro"


# ------------------------------------------------------------- prenotazione


def _booking(
    normalized: str,
    settings: SentimentSettings,
    *,
    attachment_matched: bool,
) -> BookingScore:
    total = 0.0
    signals: List[str] = []

    for pattern, label, weight in BOOKING_SIGNALS:
        if re.search(pattern, normalized):
            total += weight
            signals.append(label)

    for pattern, label, weight in CANCEL_SIGNALS:
        if re.search(pattern, normalized):
            total -= weight
            signals.append(f"-{label}")

    if attachment_matched:
        # L'impegnativa conforme allegata e' l'indizio piu' concreto di tutti.
        total += settings.attachment_bonus
        signals.append("allegato conforme")

    score = round(_clamp(total, 0.0, 1.0), 3)
    return BookingScore(
        score=score,
        is_booking=score >= settings.booking_threshold,
        signals=signals,
    )


# --------------------------------------------------------------------- utili


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _unique(values: List[str]) -> List[str]:
    seen: List[str] = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen
