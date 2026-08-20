"""Traduzione del risultato dell'analisi nel JSON della risposta.

Le chiavi sono in italiano come il resto del progetto: in Power Automate si
leggono cosi' come sono (``body('Analizza_email')?['conforme']``), quindi
conviene che parlino la stessa lingua di chi costruisce il flusso.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..models import (
    AttachmentAnalysis, ConfidenceScore, EmailAnalysis, MatchReport, SentimentScore,
)


def analysis_to_dict(
    analysis: EmailAnalysis,
    *,
    include_text: bool = True,
    max_text_chars: int = 0,
) -> Dict[str, Any]:
    """Rappresentazione JSON completa del verdetto.

    ``include_text`` e ``max_text_chars`` vengono da
    ``attachments.return_text`` e ``attachments.max_text_chars``: il testo
    letto dai documenti e' un dato sanitario, chi non lo vuole in giro puo'
    escluderlo o troncarlo senza toccare il resto della risposta.
    """
    return {
        "id_messaggio": analysis.message_key,
        "oggetto": analysis.subject,
        "esito": analysis.esito.value,
        "conforme": analysis.conforme,
        # Verdetto sintetico: e' una prenotazione di telemedicina? Vale solo se
        # entrambe le percentuali superano la rispettiva soglia.
        "prenotazione_telemedicina": analysis.e_prenotazione_telemedicina,
        "telemedicina": confidence_to_dict(analysis.telemedicina),
        "prenotazione": confidence_to_dict(analysis.prenotazione),
        "screening": {
            "superato": analysis.screening.passed,
            "termini": analysis.screening.terms,
            "dove": analysis.screening.where,
        },
        "criteri": _criteria_to_dict(analysis.match, analysis.matched_attachment),
        "documenti": [
            _document_to_dict(item, include_text=include_text, max_text_chars=max_text_chars)
            for item in analysis.attachments
        ],
        "documenti_letti": sum(1 for item in analysis.attachments if item.chars > 0),
        "documenti_conformi": sum(1 for item in analysis.attachments if item.matched),
        "sentiment": sentiment_to_dict(analysis.sentiment),
        "avvisi": analysis.warnings,
        "errore": analysis.error,
        "durata_ms": analysis.duration_ms,
        "analizzato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def confidence_to_dict(score: ConfidenceScore) -> Dict[str, Any]:
    """Percentuale di sicurezza con gli indizi che l'hanno determinata.

    ``indizi_a_favore`` e ``indizi_contrari`` sono in ordine di applicazione e
    riportano il peso di ciascuno: la percentuale resta verificabile a mano.
    """
    return {
        "percentuale": score.percent,
        "livello": score.level,
        "confermato": score.holds,
        "indizi_a_favore": [_evidence_to_dict(item) for item in score.positives],
        "indizi_contrari": [_evidence_to_dict(item) for item in score.negatives],
    }


def _evidence_to_dict(item: Any) -> Dict[str, Any]:
    return {"indizio": item.label, "dove": item.where, "peso": item.weight}


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


def _document_to_dict(
    item: AttachmentAnalysis,
    *,
    include_text: bool,
    max_text_chars: int,
) -> Dict[str, Any]:
    trovati: List[str] = item.match.found if item.match else []
    mancanti: List[str] = item.match.missing if item.match else []
    documento: Dict[str, Any] = {
        "nome": item.name,
        "origine": item.origine.value,
        "sorgente": item.source.value,
        "caratteri": item.chars,
        "conforme": item.matched,
        "trovati": trovati,
        "mancanti": mancanti,
        # Cosa e' stato fatto al file prima di leggerlo (ridimensionamento).
        "nota": item.note,
        "errore": item.error,
    }
    if include_text:
        documento["testo"] = _clip(item.text, max_text_chars)
        documento["testo_troncato"] = _is_clipped(item.text, max_text_chars)
    return documento


def _clip(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars]


def _is_clipped(text: str, max_chars: int) -> bool:
    return max_chars > 0 and len(text) > max_chars
