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


# ------------------------------------------- keyword richieste e refusi


@pytest.mark.parametrize(
    "oggetto,corpo",
    [
        ("Richiesta televisita", "Buongiorno, chiedo una televisita di cardiologia."),
        ("Prenotazione", "Vorrei prenotare una televisita per la paziente. Allego l'impegnativa."),
        ("Prenotazione visita", "Si chiede una visita in telemedicina per la paziente."),
        ("Invio impegnativa", "Allego l'impegnativa per la televisita della paziente."),
        ("Rinnovo piano terapeutico",
         "Si chiede appuntamento di televisita per il rinnovo del piano terapeutico."),
        ("Telemedicina", "Vorrei prenotare una visita in telemedicina. Allego la ricetta."),
    ],
)
def test_keyword_di_prenotazione(oggetto: str, corpo: str, impostazioni: ConfidenceSettings) -> None:
    telemedicina, prenotazione = _percentuali(oggetto, corpo, impostazioni)

    assert telemedicina.holds and prenotazione.holds, prenotazione.evidence


@pytest.mark.parametrize(
    "oggetto,corpo",
    [
        # Stessa richiesta, scritta male in punti diversi.
        ("Richiesta prenotazine telvisita", "Vorrei prentoare una telvisita."),
        ("Richiesta", "Buongiorno, vorrei prenotre una telveisita. Allego l'impegnatva."),
        ("Rinnovo pinao terapetico", "Chiedo appuntamneto di telvisita per il piano."),
        ("Prenotazione televista", "Allego l'impegnatva per la televista di cardiologia."),
    ],
)
def test_prenotazione_riconosciuta_anche_scritta_male(
    oggetto: str, corpo: str, impostazioni: ConfidenceSettings
) -> None:
    telemedicina, prenotazione = _percentuali(oggetto, corpo, impostazioni)

    assert telemedicina.holds and prenotazione.holds, prenotazione.evidence


def test_il_refuso_non_cambia_il_punteggio(impostazioni: ConfidenceSettings) -> None:
    corretto = _percentuali(
        "Richiesta prenotazione televisita", "Vorrei prenotare una televisita.", impostazioni
    )
    sbagliato = _percentuali(
        "Richiesta prenotazine telvisita", "Vorrei prenotare una telvisita.", impostazioni
    )

    assert corretto[0].percent == sbagliato[0].percent
    assert corretto[1].percent == sbagliato[1].percent


def test_la_forma_scorretta_finisce_negli_indizi(impostazioni: ConfidenceSettings) -> None:
    """Chi legge la risposta deve vedere cosa e' stato interpretato e come."""
    telemedicina, _prenotazione = _percentuali(
        "Richiesta telvisita", "Buongiorno.", impostazioni
    )

    etichette = [indizio.label for indizio in telemedicina.evidence]
    assert any("scritto 'telvisita'" in etichetta for etichetta in etichette)


def test_refuso_nel_documento_letto_dall_ocr(impostazioni: ConfidenceSettings) -> None:
    """L'OCR sbaglia proprio questi termini: la tolleranza serve soprattutto qui."""
    punteggio = score_telemedicine(
        "Invio documento", "In allegato quanto in oggetto.", impostazioni,
        document_text="RICHIESTA DI TELEMDICINA prestazione 1501A",
    )

    assert punteggio.holds is True
    assert any("scritto" in indizio.label for indizio in punteggio.evidence)


def test_una_parola_vicina_non_diventa_una_prenotazione(
    impostazioni: ConfidenceSettings,
) -> None:
    """"punto di vista" non e' una richiesta di visita."""
    _telemedicina, prenotazione = _percentuali(
        "Preventivo", "Dal nostro punto di vista il preventivo e' congruo.", impostazioni
    )

    assert prenotazione.holds is False
    assert not any("visita" in indizio.label for indizio in prenotazione.positives)


def test_termine_nel_solo_corpo_supera_la_soglia(impostazioni: ConfidenceSettings) -> None:
    """L'oggetto generico non deve affossare un corpo esplicito."""
    punteggio = score_telemedicine(
        "Richiesta", "Buongiorno, vorrei prenotare una televisita.", impostazioni
    )

    assert punteggio.holds is True
