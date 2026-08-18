"""Test del controllo periodico della casella.

Il ciclo di polling e' collaudabile per intero senza rete: si iniettano un
orologio e una funzione di attesa finti, cosi' i "5 minuti" passano
istantaneamente e si puo' verificare quando e con quale finestra viene
interrogata la casella.
"""

from __future__ import annotations

from typing import List, Optional

from inoltro_email.config import Settings
from inoltro_email.models import Decision, ProcessResult
from inoltro_email.outlook.poller import MailPoller


class FakeClock:
    """Orologio monotono governato dai test: avanza solo quando si dorme."""

    def __init__(self, work_seconds: float = 0.0) -> None:
        self.now = 0.0
        self.work_seconds = work_seconds
        self.sleeps: List[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    def work(self) -> None:
        """Simula il tempo speso a elaborare i messaggi di un giro."""
        self.now += self.work_seconds


class SpyPipeline:
    def __init__(self, clock: Optional[FakeClock] = None, errore: Optional[Exception] = None) -> None:
        self.chiamate: List[dict] = []
        self.errore = errore
        self._clock = clock

    def process_recent(self, minutes: int, unread_only: bool = True) -> List[ProcessResult]:
        self.chiamate.append({"minutes": minutes, "unread_only": unread_only})
        if self._clock is not None:
            self._clock.work()
        if self.errore is not None:
            raise self.errore
        return [ProcessResult("chiave", "Oggetto", Decision.FORWARDED)]


def build_poller(settings: Settings, pipeline, clock: FakeClock) -> MailPoller:
    return MailPoller(settings, pipeline, sleeper=clock.sleep, clock=clock)


def test_primo_giro_recupera_la_finestra_di_avvio(settings: Settings) -> None:
    """All'avvio si guarda indietro di catch_up_minutes, poi bastano 5 minuti."""
    clock = FakeClock()
    pipeline = SpyPipeline(clock)

    build_poller(settings, pipeline, clock).run(max_cycles=3)

    assert [call["minutes"] for call in pipeline.chiamate] == [30, 5, 5]


def test_esamina_solo_i_messaggi_non_letti(settings: Settings) -> None:
    clock = FakeClock()
    pipeline = SpyPipeline(clock)

    build_poller(settings, pipeline, clock).run(max_cycles=1)

    assert pipeline.chiamate[0]["unread_only"] is True


def test_puo_esaminare_anche_i_letti(settings: Settings) -> None:
    settings.outlook.unread_only = False
    clock = FakeClock()
    pipeline = SpyPipeline(clock)

    build_poller(settings, pipeline, clock).run(max_cycles=1)

    assert pipeline.chiamate[0]["unread_only"] is False


def test_attende_l_intervallo_configurato(settings: Settings) -> None:
    """Con giri istantanei l'attesa e' esattamente l'intervallo (5 minuti)."""
    clock = FakeClock()
    pipeline = SpyPipeline(clock)

    build_poller(settings, pipeline, clock).run(max_cycles=3)

    assert clock.sleeps == [300.0, 300.0]  # nessuna attesa dopo l'ultimo giro


def test_un_giro_lento_non_fa_slittare_i_successivi(settings: Settings) -> None:
    """L'attesa si accorcia del tempo gia' speso: i giri restano a passo di 5 minuti."""
    clock = FakeClock(work_seconds=60.0)  # ogni giro impiega un minuto
    pipeline = SpyPipeline(clock)

    build_poller(settings, pipeline, clock).run(max_cycles=2)

    assert clock.sleeps == [240.0]


def test_finestra_allargata_se_il_giro_sfora_l_intervallo(settings: Settings) -> None:
    """Se un giro dura piu' dell'intervallo, il successivo copre il buco."""
    clock = FakeClock(work_seconds=8 * 60.0)  # otto minuti, piu' dei cinque previsti
    pipeline = SpyPipeline(clock)

    build_poller(settings, pipeline, clock).run(max_cycles=2)

    assert clock.sleeps == [0.0]  # niente attesa: si e' gia' in ritardo
    assert pipeline.chiamate[1]["minutes"] == 8  # finestra estesa al tempo trascorso


def test_un_errore_non_ferma_il_ciclo(settings: Settings) -> None:
    """Rete assente o token rifiutato: si registra l'errore e si riprova."""
    clock = FakeClock()
    pipeline = SpyPipeline(clock, errore=RuntimeError("Graph non raggiungibile"))

    build_poller(settings, pipeline, clock).run(max_cycles=3)  # non deve sollevare

    assert len(pipeline.chiamate) == 3


def test_poll_once_restituisce_gli_esiti(settings: Settings) -> None:
    clock = FakeClock()
    pipeline = SpyPipeline(clock)

    results = build_poller(settings, pipeline, clock).poll_once()

    assert [result.decision for result in results] == [Decision.FORWARDED]
    assert pipeline.chiamate == [{"minutes": 5, "unread_only": True}]


def test_poll_once_assorbe_gli_errori(settings: Settings) -> None:
    clock = FakeClock()
    pipeline = SpyPipeline(clock, errore=RuntimeError("timeout"))

    assert build_poller(settings, pipeline, clock).poll_once() == []


def test_intervallo_letto_dalla_configurazione(settings: Settings) -> None:
    settings.outlook.poll_interval_minutes = 2
    settings.outlook.lookback_minutes = 3
    settings.outlook.catch_up_minutes = 0
    clock = FakeClock()
    pipeline = SpyPipeline(clock)

    build_poller(settings, pipeline, clock).run(max_cycles=2)

    assert clock.sleeps == [120.0]
    assert [call["minutes"] for call in pipeline.chiamate] == [3, 3]
