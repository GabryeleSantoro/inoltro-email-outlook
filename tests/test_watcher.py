"""Test del gestore dell'evento NewMailEx.

Il gestore non e' collaudabile end-to-end senza Outlook, ma la sua parte
delicata si': deve spezzare correttamente l'elenco di EntryID e non lasciare
mai sfuggire un'eccezione, che nel message pump COM fermerebbe il servizio.
"""

from __future__ import annotations

from typing import List

import pytest

from inoltro_email.models import Decision, ProcessResult
from inoltro_email.outlook import watcher


class SpyPipeline:
    def __init__(self, esplode: bool = False) -> None:
        self.visti: List[str] = []
        self.esplode = esplode

    def process_entry_id(self, entry_id: str):
        self.visti.append(entry_id)
        if self.esplode:
            raise RuntimeError("Outlook ha restituito un errore COM")
        return ProcessResult(entry_id, "Oggetto", Decision.FORWARDED)


@pytest.fixture
def spy(monkeypatch: pytest.MonkeyPatch) -> SpyPipeline:
    pipeline = SpyPipeline()
    monkeypatch.setattr(watcher, "_ACTIVE_PIPELINE", pipeline)
    return pipeline


def test_elabora_ogni_entry_id_dell_elenco(spy: SpyPipeline) -> None:
    """NewMailEx consegna gli EntryID separati da virgola."""
    watcher.NewMailHandler().OnNewMailEx("AAA111,BBB222,CCC333")
    assert spy.visti == ["AAA111", "BBB222", "CCC333"]


def test_ignora_spazi_e_voci_vuote(spy: SpyPipeline) -> None:
    watcher.NewMailHandler().OnNewMailEx(" AAA111 , , BBB222,")
    assert spy.visti == ["AAA111", "BBB222"]


def test_un_errore_non_interrompe_gli_altri_messaggi(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nel pump COM fermerebbe l'ascolto: va assorbita."""
    pipeline = SpyPipeline(esplode=True)
    monkeypatch.setattr(watcher, "_ACTIVE_PIPELINE", pipeline)

    watcher.NewMailHandler().OnNewMailEx("AAA111,BBB222")  # non deve sollevare

    assert pipeline.visti == ["AAA111", "BBB222"]  # il secondo e' stato comunque tentato


def test_senza_pipeline_attiva_non_solleva(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(watcher, "_ACTIVE_PIPELINE", None)
    watcher.NewMailHandler().OnNewMailEx("AAA111")


def test_collezione_vuota_gestita(spy: SpyPipeline) -> None:
    watcher.NewMailHandler().OnNewMailEx("")
    assert spy.visti == []
