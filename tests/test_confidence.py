"""Test delle percentuali di sicurezza.

I casi non sono inventati: sono i messaggi che il servizio riceve davvero e
che nei log passavano tutti per "telemedicina" solo perche' contenevano la
parola.
"""

from __future__ import annotations

import pytest

from inoltro_email.config import ConfidenceSettings
from inoltro_email.confidence import score_booking, score_telemedicine


@pytest.fixture
def impostazioni() -> ConfidenceSettings:
    return ConfidenceSettings()


def _percentuali(oggetto, corpo, impostazioni, **extra):
    telemedicina = score_telemedicine(oggetto, corpo, impostazioni, **extra)
    prenotazione = score_booking(
        oggetto, corpo, impostazioni,
        telemedicine=telemedicina,
        document_matched=extra.get("document_matched", False),
        document_text=extra.get("document_text", ""),
    )
    return telemedicina, prenotazione


# ------------------------------------------------------------- telemedicina


def test_oggetto_esplicito_da_sicurezza_alta(impostazioni: ConfidenceSettings) -> None:
    punteggio = score_telemedicine(
        "Richiesta prenotazione televisita",
        "Buongiorno, vorrei prenotare una televisita.",
        impostazioni,
    )

    assert punteggio.percent > 80
    assert punteggio.level == "alta"
    assert punteggio.holds is True


def test_termine_solo_nell_indirizzo_non_fa_testo(impostazioni: ConfidenceSettings) -> None:
    """"telemedicina@aslsalerno.it" fra i destinatari non e' l'argomento."""
    punteggio = score_telemedicine(
        "Richiesta accesso piattaforma COT",
        "Si richiede accesso alla piattaforma COT.\n"
        "Da: Telemedicina <telemedicina@aslsalerno.it>",
        impostazioni,
    )

    assert punteggio.percent < 25
    assert punteggio.holds is False


def test_termine_solo_nel_testo_citato_pesa_meno(impostazioni: ConfidenceSettings) -> None:
    citato = score_telemedicine(
        "R: Segnalazione",
        "Lato Cup non si riscontrano anomalie.\n"
        "Da: Roberta Cafasso\nLa paziente aveva una televisita stamattina.",
        impostazioni,
    )
    scritto = score_telemedicine(
        "R: Segnalazione", "La paziente aveva una televisita stamattina.", impostazioni
    )

    assert citato.percent < scritto.percent


def test_documento_letto_alza_la_sicurezza(impostazioni: ConfidenceSettings) -> None:
    senza = score_telemedicine("Invio documento", "In allegato quanto in oggetto.", impostazioni)
    con = score_telemedicine(
        "Invio documento", "In allegato quanto in oggetto.", impostazioni,
        document_text="RICHIESTA DI TELEMEDICINA prestazione 1501A",
        document_matched=True,
    )

    assert con.percent > senza.percent
    assert con.holds is True


# ------------------------------------------------------------- prenotazione


def test_prenotazione_esplicita(impostazioni: ConfidenceSettings) -> None:
    telemedicina, prenotazione = _percentuali(
        "Prenotazione telemedicina - paziente Rossi",
        "Si chiede di fissare un appuntamento di televisita. Allego l'impegnativa.",
        impostazioni,
        document_text="TELEMEDICINA 1501A",
        document_matched=True,
    )

    assert telemedicina.holds and prenotazione.holds
    assert prenotazione.percent > 90


@pytest.mark.parametrize(
    "oggetto,corpo",
    [
        # Foglio degli accessi mensili: parla di telemedicina, non prenota nulla.
        ("Accessi Telemedicina Luglio 2026 Dott.ssa Caccavo",
         "In allegato gli accessi in Telemedicina del mese di Luglio 2026."),
        # Apertura di un'agenda: e' configurazione, non una prenotazione.
        ("Agende telemedicina DSB 68 - ORTOPEDIA - DOTT. PERNA",
         "Si inviano in allegato l'offering per l'apertura agenda telemedicina."),
        # Offerta commerciale di un fornitore.
        ("PROPOSTA OFFERTA SERVIZIO TELEASSISTENZA PICC CAREGIVERS",
         "Vi allego l'ultima proposta migliorativa informale per il servizio in oggetto."),
        # Pratica economica del personale.
        ("Variazioni economiche mese di Maggio 2026",
         "Allego gli accessi in telemedicina e copia del certificato di malattia."),
        # Segnalazione di malfunzionamento su una televisita gia' prenotata.
        ("Segnalazione",
         "La paziente aveva una televisita stamattina ma non compariva in agenda."),
    ],
)
def test_parlare_di_telemedicina_non_e_prenotare(
    oggetto: str, corpo: str, impostazioni: ConfidenceSettings
) -> None:
    _telemedicina, prenotazione = _percentuali(oggetto, corpo, impostazioni)

    assert prenotazione.holds is False, prenotazione.evidence
    assert prenotazione.percent < 50


def test_disdetta_non_e_prenotazione(impostazioni: ConfidenceSettings) -> None:
    _telemedicina, prenotazione = _percentuali(
        "Disdetta televisita",
        "Vorrei disdire l'appuntamento di televisita prenotato per domani.",
        impostazioni,
    )

    assert prenotazione.holds is False


def test_risposta_automatica_scende_a_zero(impostazioni: ConfidenceSettings) -> None:
    telemedicina, prenotazione = _percentuali("Accettata: OPAT", "", impostazioni)

    assert telemedicina.percent < 10
    assert prenotazione.percent < 10


# ------------------------------------------------------------- spiegabilita'


def test_gli_indizi_spiegano_il_punteggio(impostazioni: ConfidenceSettings) -> None:
    _telemedicina, prenotazione = _percentuali(
        "Accessi Telemedicina Luglio 2026",
        "In allegato gli accessi del mese.",
        impostazioni,
    )

    contrari = [indizio.label for indizio in prenotazione.negatives]
    assert any("accessi" in etichetta for etichetta in contrari)
    assert all(indizio.weight != 0 for indizio in prenotazione.evidence)


def test_soglie_configurabili(impostazioni: ConfidenceSettings) -> None:
    severe = ConfidenceSettings(telemedicine_threshold=99.9)
    normale = score_telemedicine("Televisita", "Prenoto una televisita", impostazioni)
    esigente = score_telemedicine("Televisita", "Prenoto una televisita", severe)

    assert normale.percent == esigente.percent
    assert normale.holds is True
    assert esigente.holds is False
