"""Test del riconoscimento dei termini scritti male."""

from __future__ import annotations

import pytest

from inoltro_email.spelling import distanza_entro, trova_termini


# ----------------------------------------------------------------- distanza


@pytest.mark.parametrize(
    "prima,seconda,attesa",
    [
        ("televisita", "televisita", 0),
        ("telvisita", "televisita", 1),      # lettera mancante
        ("televisitaa", "televisita", 1),    # lettera in piu'
        ("telavisita", "televisita", 1),     # lettera sbagliata
        ("telveisita", "televisita", 1),     # due lettere scambiate
    ],
)
def test_distanza(prima: str, seconda: str, attesa: int) -> None:
    assert distanza_entro(prima, seconda, 2) == attesa


def test_distanza_oltre_il_limite() -> None:
    assert distanza_entro("preventivo", "prenotazione", 2) is None


def test_lo_scambio_di_lettere_vale_una_sola_differenza() -> None:
    """Senza questo, "telveisita" costerebbe due modifiche invece di una."""
    assert distanza_entro("telveisita", "televisita", 1) == 1


# ------------------------------------------------------------ riconoscimento


@pytest.mark.parametrize(
    "scritto,atteso",
    [
        ("telvisita", "televisita"),
        ("televista", "televisita"),
        ("telveisita", "televisita"),
        ("telemdicina", "telemedicina"),
        ("telemedicna", "telemedicina"),
        ("prenotazine", "prenotazione"),
        ("prentoazione", "prenotazione"),
        ("impegnatva", "impegnativa"),
        ("impegnativva", "impegnativa"),
        ("terapetico", "terapeutico"),
        ("appuntamneto", "appuntamento"),
        ("teleconsluto", "teleconsulto"),
    ],
)
def test_parole_sbagliate_riconosciute(scritto: str, atteso: str) -> None:
    trovati = trova_termini(f"testo con {scritto} dentro")

    assert atteso in trovati
    assert trovati[atteso] == scritto


def test_parola_corretta_riportata_com_e() -> None:
    """Quando e' scritta bene, la forma trovata coincide con il termine."""
    assert trova_termini("una televisita")["televisita"] == "televisita"


@pytest.mark.parametrize(
    "testo",
    [
        "dal mio punto di vista",
        "le viste della citta'",
        "ho visto il documento",
        "la rivista aziendale",
        "una ricerca di mercato",
        "la ricevuta di pagamento",
    ],
)
def test_parole_italiane_vicine_non_contano(testo: str) -> None:
    """"vista" dista una lettera da "visita": non deve valere come visita."""
    assert trova_termini(testo) == {}


def test_parole_corte_non_tollerano_errori() -> None:
    """Sotto le sei lettere una lettera di differenza cambia la parola."""
    assert trova_termini("il visto e' scaduto") == {}


def test_parole_lontane_non_vengono_forzate() -> None:
    assert "prenotazione" not in trova_termini("invio il preventivo richiesto")
    assert "telemedicina" not in trova_termini("comunicazione telefonica")


def test_accenti_e_maiuscole_non_disturbano() -> None:
    trovati = trova_termini("RICHIESTA DI TELEVISTA PERCHE' E' NECESSARIA")

    assert trovati["televisita"] == "televista"
