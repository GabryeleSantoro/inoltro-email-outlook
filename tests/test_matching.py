"""Test dello screening su oggetto/corpo e delle regole sul testo estratto."""

from __future__ import annotations

import pytest

from inoltro_email.config import RuleSettings, ScreeningSettings
from inoltro_email.matching import alnum_collapse, evaluate, normalize, screen


# ------------------------------------------------ criteri sul testo estratto


@pytest.mark.parametrize(
    "text",
    [
        "Richiesta di TELEMEDICINA - codice 1501A",
        "richiesta di telemedicina codice 15 0 1A",
        "TELEMEDICINA\nprestazione 15-01A",
        "Prestazione: 1501A  Tipo: Tele medicina cardiologica",
        "codice1501A telemedicina",
        "TELEMEDICINÀ e codice 1501A",  # accento: normalizzato
    ],
)
def test_riconosce_entrambi_i_criteri(text: str) -> None:
    assert evaluate(text, RuleSettings()).matched


@pytest.mark.parametrize(
    "text",
    [
        "Richiesta di telemedicina senza alcun codice",
        "Prestazione codice 1501A in presenza",
        "Nessuno dei due termini presenti nel referto",
        "",
        "telemedicina 15A11",
        "telemedicina 15B10",
    ],
)
def test_in_and_serve_tutto(text: str) -> None:
    assert not evaluate(text, RuleSettings()).matched


def test_confusioni_ocr_attive_per_default() -> None:
    # L'OCR legge spesso "1" come "l" e "0" come "O".
    assert evaluate("telemedicina prestazione l5O1A", RuleSettings()).matched


def test_confusioni_ocr_disattivabili() -> None:
    rules = RuleSettings(fuzzy_ocr_confusions=False)
    assert not evaluate("telemedicina prestazione l5O1A", rules).matched
    # Il codice scritto correttamente continua a essere riconosciuto.
    assert evaluate("telemedicina prestazione 1501A", rules).matched


def test_confusioni_non_applicate_alle_keyword() -> None:
    """'telemedicina' non deve combaciare con la sua versione storpiata in cifre."""
    assert not evaluate("te1emed1c1na 1501A", RuleSettings()).matched


def test_modalita_any_basta_un_criterio() -> None:
    rules = RuleSettings(mode="any")
    assert evaluate("solo telemedicina", rules).matched
    assert evaluate("solo il codice 1501A", rules).matched


def test_report_elenca_trovati_e_mancanti() -> None:
    report = evaluate("richiesta di telemedicina", RuleSettings())

    assert report.found == ["telemedicina"]
    assert report.missing == ["1501A"]
    assert "telemedicina" in report.summary()


def test_normalizzazione_del_testo() -> None:
    assert normalize("  TELEVISITÀ   urgente\n") == "televisita urgente"
    assert alnum_collapse("15-01 A") == "1501a"


# -------------------------------------------------- screening oggetto/corpo


def test_screening_riconosce_la_parola_nell_oggetto() -> None:
    report = screen("Prenotazione TELEMEDICINA", "Buongiorno, allego impegnativa.",
                    ScreeningSettings())

    assert report.passed
    assert report.in_subject == ["telemedicina"]
    assert report.in_body == []
    assert report.where == ["oggetto"]


def test_screening_riconosce_la_parola_nel_corpo() -> None:
    report = screen("Richiesta visita", "Vorrei prenotare una televisita cardiologica.",
                    ScreeningSettings())

    assert report.passed
    assert report.terms == ["televisita"]
    assert report.where == ["corpo"]


def test_screening_non_passa_senza_termini() -> None:
    report = screen("Richiesta di visita", "Vorrei prenotare una visita in ambulatorio.",
                    ScreeningSettings())

    assert not report.passed
    assert report.terms == []
    assert report.where == []


def test_screening_tollera_spezzature_e_accenti() -> None:
    """L'oggetto scritto a mano puo' contenere spazi o accenti di troppo."""
    report = screen("TELE-VISITA di controllo", "", ScreeningSettings())
    assert report.passed


def test_screening_in_modalita_all_richiede_tutti_i_termini() -> None:
    rules = ScreeningSettings(mode="all")

    assert not screen("Prenotazione telemedicina", "", rules).passed
    assert screen("Prenotazione telemedicina", "si tratta di una televisita", rules).passed


def test_screening_senza_ripetizioni_nei_termini() -> None:
    """Lo stesso termine in oggetto e corpo va riportato una volta sola."""
    report = screen("Telemedicina", "richiesta di telemedicina", ScreeningSettings())

    assert report.terms == ["telemedicina"]
    assert report.where == ["oggetto", "corpo"]
