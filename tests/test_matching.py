"""Test delle regole di riconoscimento sul testo estratto."""

from __future__ import annotations

import pytest

from inoltro_email.config import RuleSettings
from inoltro_email.matching import alnum_collapse, evaluate, normalize


@pytest.mark.parametrize(
    "text",
    [
        "Richiesta di TELEVISITA - codice 15A10",
        "richiesta di televisita codice 15 A 10",
        "TELEVISITA\nprestazione 15-A10",
        "Prestazione: 15A10  Tipo: Tele visita cardiologica",
        "codice15A10 televisita",
        "TELEVISITÀ e codice 15A10",  # accento: normalizzato
    ],
)
def test_riconosce_entrambi_i_criteri(text: str) -> None:
    assert evaluate(text, RuleSettings()).matched


@pytest.mark.parametrize(
    "text",
    [
        "Richiesta di televisita senza alcun codice",
        "Prestazione codice 15A10 in presenza",
        "Nessuno dei due termini presenti nel referto",
        "",
        "televisita 15A11",
        "televisita 15B10",
    ],
)
def test_in_and_serve_tutto(text: str) -> None:
    assert not evaluate(text, RuleSettings()).matched


def test_confusioni_ocr_attive_per_default() -> None:
    # L'OCR legge spesso "1" come "l" e "0" come "O".
    assert evaluate("televisita prestazione l5A1O", RuleSettings()).matched


def test_confusioni_ocr_disattivabili() -> None:
    rules = RuleSettings(fuzzy_ocr_confusions=False)
    assert not evaluate("televisita prestazione l5A1O", rules).matched
    # Il codice scritto correttamente continua a essere riconosciuto.
    assert evaluate("televisita prestazione 15A10", rules).matched


def test_confusioni_non_applicate_alle_keyword() -> None:
    """'televisita' non deve combaciare con la sua versione storpiata in cifre."""
    assert not evaluate("te1ev151ta 15A10", RuleSettings()).matched


def test_modalita_any_basta_un_criterio() -> None:
    rules = RuleSettings(mode="any")
    assert evaluate("solo televisita", rules).matched
    assert evaluate("solo 15A10", rules).matched
    assert not evaluate("nessun criterio", rules).matched


def test_report_elenca_trovati_e_mancanti() -> None:
    report = evaluate("richiesta di televisita", RuleSettings())
    assert report.found_keywords == ["televisita"]
    assert report.missing_codes == ["15A10"]
    assert "15A10" in report.summary()


def test_normalizzazione() -> None:
    assert normalize("  TELEVISITÀ   à\tpiù ") == "televisita a piu"
    assert alnum_collapse("15 - A / 10") == "15a10"
