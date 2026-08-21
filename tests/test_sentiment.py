"""Test del punteggio di sentiment e dell'intento di prenotazione."""

from __future__ import annotations

from inoltro_email.config import SentimentSettings
from inoltro_email.sentiment import analyze_sentiment


def analizza(text: str, settings: SentimentSettings | None = None, **kwargs):
    return analyze_sentiment(text, settings or SentimentSettings(), **kwargs)


# ----------------------------------------------------------------- polarita'


def test_messaggio_cortese_e_positivo() -> None:
    score = analizza("Buongiorno, vorrei prenotare una televisita. Grazie mille, gentilissimi.")

    assert score.label == "positivo"
    assert score.score > 0
    assert "grazie" in score.positive_terms


def test_reclamo_e_negativo() -> None:
    score = analizza("Servizio pessimo, ritardi inaccettabili: e' la terza volta che scrivo.")

    assert score.label == "negativo"
    assert score.score < 0
    assert "pessimo" in score.negative_terms


def test_messaggio_informativo_e_neutro() -> None:
    score = analizza("Si comunica l'orario di apertura degli ambulatori.")

    assert score.label == "neutro"
    assert score.score == 0.0


def test_negazione_ribalta_il_termine() -> None:
    """'non sono soddisfatto' non deve contare come un complimento."""
    assert analizza("Non sono soddisfatto del servizio ricevuto").label == "negativo"
    assert analizza("Sono soddisfatto del servizio ricevuto").label == "positivo"


def test_intensificatore_aumenta_il_peso() -> None:
    normale = analizza("Il servizio e' pessimo ma vi ringrazio")
    intenso = analizza("Il servizio e' molto pessimo ma vi ringrazio")

    assert intenso.score < normale.score


def test_soglie_configurabili() -> None:
    testo = "Vi ringrazio, ma segnalo un problema"
    prudente = SentimentSettings(positive_threshold=0.9, negative_threshold=-0.9)

    assert analizza(testo, prudente).label == "neutro"


# ------------------------------------------------------------- prenotazione


def test_richiesta_di_prenotazione_riconosciuta() -> None:
    score = analizza("Vorrei prenotare una televisita cardiologica, allego l'impegnativa.")

    assert score.booking.is_booking
    assert score.booking.score >= 0.5
    assert "prenotazione" in score.booking.signals
    assert "telemedicina" in score.booking.signals


def test_email_estranea_non_e_una_prenotazione() -> None:
    score = analizza("Trasmettiamo la fattura del mese di luglio.")

    assert not score.booking.is_booking
    assert score.booking.score == 0.0


def test_disdetta_abbassa_il_punteggio() -> None:
    prenotazione = analizza("Vorrei prenotare un appuntamento di telemedicina.")
    disdetta = analizza("Vorrei disdire l'appuntamento di telemedicina prenotato.")

    assert prenotazione.booking.is_booking
    assert not disdetta.booking.is_booking
    assert "-disdetta" in disdetta.booking.signals


def test_allegato_conforme_rafforza_il_punteggio() -> None:
    testo = "Buongiorno, invio la documentazione per la televisita."
    senza = analizza(testo)
    con = analizza(testo, attachment_matched=True)

    assert con.booking.score > senza.booking.score
    assert "allegato conforme" in con.booking.signals


def test_punteggio_limitato_a_uno() -> None:
    score = analizza(
        "Vorrei prenotare un appuntamento di telemedicina, fissare data e orario, "
        "verificate la disponibilita' in agenda; allego impegnativa con codice 1501A "
        "del paziente.",
        attachment_matched=True,
    )
    assert score.booking.score == 1.0


def test_soglia_di_prenotazione_configurabile() -> None:
    testo = "Chiedo informazioni sulla telemedicina."
    assert not analizza(testo).booking.is_booking
    assert analizza(testo, SentimentSettings(booking_threshold=0.2)).booking.is_booking
