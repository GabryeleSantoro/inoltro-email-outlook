"""Regole di riconoscimento sul testo estratto dagli allegati.

Il testo che arriva dall'OCR non e' mai pulito: puo' contenere spazi di troppo
("15 A 10"), trattini ("15-A10"), a capo in mezzo alle parole e le classiche
confusioni fra caratteri simili (O/0, l/1, S/5). Le funzioni di questo modulo
normalizzano testo e termini cercati prima del confronto, in modo che la
ricerca resti robusta senza dover ricorrere a fuzzy matching generico (che
produrrebbe falsi positivi su un codice come 15A10).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List

from .config import RuleSettings
from .models import MatchReport

# Confusioni piu' comuni dei motori OCR. Applicate solo ai codici: su una
# parola come "televisita" trasformerebbero le lettere in cifre senza motivo.
OCR_CONFUSIONS = str.maketrans({"o": "0", "i": "1", "l": "1", "s": "5", "b": "8"})

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Minuscolo, senza accenti, con gli spazi collassati."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return _WHITESPACE.sub(" ", without_accents.lower()).strip()


def alnum_collapse(text: str) -> str:
    """Tiene solo lettere e cifre.

    Serve a rendere equivalenti "1501A", "15 0 1A", "15-01A" e "TELE VISITA"
    spezzata da un a capo.
    """
    return _NON_ALNUM.sub("", normalize(text))


def apply_ocr_confusions(text: str) -> str:
    """Riconduce i caratteri ambigui a una forma unica (O->0, l->1, ...)."""
    return text.translate(OCR_CONFUSIONS)


def contains_keyword(haystack_collapsed: str, keyword: str) -> bool:
    needle = alnum_collapse(keyword)
    return bool(needle) and needle in haystack_collapsed


def contains_code(haystack_collapsed: str, code: str, fuzzy: bool) -> bool:
    needle = alnum_collapse(code)
    if not needle:
        return False
    if needle in haystack_collapsed:
        return True
    if not fuzzy:
        return False
    # Stessa normalizzazione su entrambi i lati: cosi' "l5A1O" letto dall'OCR
    # e il codice atteso "15A10" convergono sulla stessa stringa.
    return apply_ocr_confusions(needle) in apply_ocr_confusions(haystack_collapsed)


def evaluate(text: str, rules: RuleSettings) -> MatchReport:
    """Confronta il testo con le regole e restituisce un report dettagliato.

    Con ``mode='all'`` (impostazione predefinita) servono tutte le keyword e
    tutti i codici; con ``mode='any'`` ne basta uno qualsiasi.
    """
    haystack = alnum_collapse(text)

    found_keywords: List[str] = []
    missing_keywords: List[str] = []
    for keyword in _clean(rules.keywords):
        (found_keywords if contains_keyword(haystack, keyword) else missing_keywords).append(keyword)

    found_codes: List[str] = []
    missing_codes: List[str] = []
    for code in _clean(rules.codes):
        hit = contains_code(haystack, code, rules.fuzzy_ocr_confusions)
        (found_codes if hit else missing_codes).append(code)

    if rules.mode == "any":
        matched = bool(found_keywords or found_codes)
    else:  # "all"
        matched = not missing_keywords and not missing_codes and bool(found_keywords or found_codes)

    return MatchReport(
        matched=matched,
        found_keywords=found_keywords,
        found_codes=found_codes,
        missing_keywords=missing_keywords,
        missing_codes=missing_codes,
    )


def _clean(values: Iterable[str]) -> List[str]:
    return [value for value in values if value and value.strip()]
