"""Traduzione del risultato dell'analisi nel JSON della risposta.

Le chiavi sono in italiano come il resto del progetto: in Power Automate si
leggono cosi' come sono (``body('Analizza_email')?['conforme']``), quindi
conviene che parlino la stessa lingua di chi costruisce il flusso.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..models import AttachmentAnalysis, EmailAnalysis, MatchReport, SentimentScore


def analysis_to_dict(analysis: EmailAnalysis) -> Dict[str, Any]:
    """Rappresentazione JSON completa del verdetto."""
    return {
        "id_messaggio": analysis.message_key,
        "oggetto": analysis.subject,
        "esito": analysis.esito.value,
        "conforme": analysis.conforme,
        "screening": {
            "superato": analysis.screening.passed,
            "termini": analysis.screening.terms,
            "dove": analysis.screening.where,
        },
        "criteri": _criteria_to_dict(analysis.match, analysis.matched_attachment),
        "documenti": [_document_to_dict(item) for item in analysis.attachments],
        "sentiment": sentiment_to_dict(analysis.sentiment),
        "errore": analysis.error,
        "durata_ms": analysis.duration_ms,
        "analizzato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def sentiment_to_dict(sentiment: SentimentScore) -> Dict[str, Any]:
    return {
        "punteggio": sentiment.score,
        "etichetta": sentiment.label,
        "termini_positivi": sentiment.positive_terms,
        "termini_negativi": sentiment.negative_terms,
        "prenotazione": {
            "punteggio": sentiment.booking.score,
            "e_prenotazione": sentiment.booking.is_booking,
            "indizi": sentiment.booking.signals,
        },
    }


def _criteria_to_dict(match: Optional[MatchReport], documento: Optional[str]) -> Dict[str, Any]:
    if match is None:
        return {"soddisfatti": False, "trovati": [], "mancanti": [], "documento": None}
    return {
        "soddisfatti": match.matched,
        "trovati": match.found,
        "mancanti": match.missing,
        "documento": documento,
    }


def _document_to_dict(item: AttachmentAnalysis) -> Dict[str, Any]:
    trovati: List[str] = item.match.found if item.match else []
    mancanti: List[str] = item.match.missing if item.match else []
    return {
        "nome": item.name,
        "origine": item.origine.value,
        "sorgente": item.source.value,
        "caratteri": item.chars,
        "conforme": item.matched,
        "trovati": trovati,
        "mancanti": mancanti,
        "errore": item.error,
    }
