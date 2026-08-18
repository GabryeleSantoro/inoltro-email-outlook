"""Prova d'insieme: casella (finta) -> client Graph -> pipeline -> poller.

I test degli altri file guardano un pezzo per volta; qui si verifica che i
pezzi siano davvero collegati: il messaggio arriva dalla cartella, l'allegato
viene scaricato e letto, i criteri decidono e l'inoltro parte davvero. L'unica
cosa finta e' cio' che sta oltre la rete (Microsoft Graph e ocr.space).
"""

from __future__ import annotations

from typing import List

from conftest import FakeOcrClient, make_pdf
from test_client import FakeApiMessage, FakeAttachment, FakeAttachments, FakeFolder

from inoltro_email.config import Settings
from inoltro_email.models import Decision
from inoltro_email.ocr.extractor import TextExtractor
from inoltro_email.outlook.client import OutlookClient
from inoltro_email.outlook.poller import MailPoller
from inoltro_email.pipeline import ForwardPipeline
from inoltro_email.state import ProcessedStore

TESTO_CONFORME = "Richiesta di TELEVISITA per prestazione codice 1501A, paziente Rossi"


def build_all(settings: Settings, folder: FakeFolder):
    client = OutlookClient(settings.outlook, settings.attachments.allowed_extensions)
    client._folder = folder  # come dopo connect(), ma senza rete
    store = ProcessedStore(settings.storage.db_path)
    pipeline = ForwardPipeline(settings, client, TextExtractor(settings, FakeOcrClient()), store)
    attese: List[float] = []
    poller = MailPoller(settings, pipeline, sleeper=attese.append, clock=lambda: 0.0)
    return poller, store, attese


def test_dal_messaggio_non_letto_all_inoltro(settings: Settings) -> None:
    api = FakeApiMessage(attachments=FakeAttachments([
        FakeAttachment("referto.pdf", make_pdf([TESTO_CONFORME])),
    ]))
    folder = FakeFolder([api])
    poller, store, attese = build_all(settings, folder)

    poller.run(max_cycles=2)

    # Alla casella si chiedono solo i non letti della finestra richiesta.
    assert "isRead eq false" in folder.chiamate[0]["query"].render()
    # L'inoltro e' partito una volta sola, benche' i due giri vedano lo stesso messaggio.
    assert api.draft.inviata is True
    assert api.draft.to.indirizzi == ["destinatario@example.com"]
    assert api.draft.subject == "[TELEVISITA] Richiesta"
    assert "Criteri riconosciuti: televisita, 1501A" in api.draft.body
    assert api.categories == ["Inoltrata"]
    assert store.get_decision(api.internet_message_id) == Decision.FORWARDED.value
    assert attese == [300.0]  # cinque minuti fra un controllo e l'altro
    store.close()


def test_messaggio_non_conforme_non_viene_inoltrato(settings: Settings) -> None:
    api = FakeApiMessage(attachments=FakeAttachments([
        FakeAttachment("referto.pdf", make_pdf(["Referto di visita ambulatoriale ordinaria"])),
    ]))
    poller, store, _ = build_all(settings, FakeFolder([api]))

    poller.run(max_cycles=1)

    assert api.draft.inviata is False
    assert api.categories == []
    assert store.get_decision(api.internet_message_id) == Decision.NO_MATCH.value
    store.close()
