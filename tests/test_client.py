"""Test del client Microsoft Graph.

La libreria O365 non viene contattata: si passano al client oggetti finti con
la stessa forma (cartella, messaggio, allegati). Il filtro OData viene pero'
costruito con il vero ``QueryBuilder``, cosi' si verifica la stringa che
finirebbe davvero nella richiesta.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
from O365 import MSGraphProtocol
from O365.utils.query import QueryBuilder

from inoltro_email.config import OutlookSettings
from inoltro_email.outlook.client import OutlookClient, OutlookError, OutlookMessage, _resolve_folder


class FakeAttachment:
    """Allegato scaricato, con la stessa interfaccia di O365."""

    def __init__(self, name: str, content: bytes = b"contenuto",
                 attachment_type: str = "file", is_inline: bool = False) -> None:
        self.name = name
        self.content_bytes = content
        self.attachment_type = attachment_type
        self.is_inline = is_inline

    def save(self, location: str, custom_name: Optional[str] = None) -> bool:
        target = Path(location) / (custom_name or self.name)
        target.write_bytes(self.content_bytes)
        return True


class FakeAttachments(list):
    def __init__(self, items: Optional[List[FakeAttachment]] = None) -> None:
        super().__init__(items or [])
        self.scaricati = False

    def download_attachments(self) -> bool:
        self.scaricati = True
        return True


class FakeRecipients:
    def __init__(self) -> None:
        self.indirizzi: List[str] = []

    def add(self, addresses) -> None:
        self.indirizzi.extend(addresses if isinstance(addresses, list) else [addresses])


class FakeDraft:
    """Bozza restituita da ``forward()``."""

    def __init__(self, subject: str = "Richiesta", body: str = "<p>originale</p>",
                 body_type: str = "html") -> None:
        self.subject = subject
        self.body_type = body_type
        self._body = body
        self.to = FakeRecipients()
        self.cc = FakeRecipients()
        self.inviata = False

    @property
    def body(self) -> str:
        return self._body

    @body.setter
    def body(self, value: str) -> None:
        # Come in O365: il testo assegnato viene anteposto a quello esistente.
        self._body = value + self._body

    def send(self) -> bool:
        self.inviata = True
        return True


class FakeApiMessage:
    """Messaggio O365 finto."""

    def __init__(self, subject: str = "Richiesta", object_id: str = "AAMk-1",
                 internet_message_id: str = "<msg-1@example.com>",
                 attachments: Optional[FakeAttachments] = None,
                 categories: Optional[List[str]] = None,
                 draft: Optional[FakeDraft] = None) -> None:
        self.subject = subject
        self.object_id = object_id
        self.internet_message_id = internet_message_id
        self.attachments = attachments if attachments is not None else FakeAttachments()
        self.has_attachments = bool(self.attachments)
        self.categories = categories if categories is not None else []
        self.is_read = False
        self.received = datetime.now(timezone.utc)
        self.draft = draft or FakeDraft()
        self.salvato = False

    def forward(self) -> FakeDraft:
        return self.draft

    def add_category(self, category: str) -> None:
        self.categories.append(category)

    def save_message(self) -> bool:
        self.salvato = True
        return True


class FakeFolder:
    """Cartella della casella: registra le interrogazioni ricevute."""

    def __init__(self, messages: Optional[List[FakeApiMessage]] = None,
                 children: Optional[Dict[str, "FakeFolder"]] = None,
                 name: str = "Inbox") -> None:
        self.messages = messages or []
        self.children = children or {}
        self.name = name
        self.chiamate: List[Dict[str, Any]] = []

    def new_query(self) -> QueryBuilder:
        return QueryBuilder(MSGraphProtocol())

    def get_messages(self, limit=25, *, query=None, order_by=None, **_kwargs):
        self.chiamate.append({"limit": limit, "query": query, "order_by": order_by})
        return list(self.messages)

    def get_message(self, object_id=None, **_kwargs):
        return next((m for m in self.messages if m.object_id == object_id), None)

    def get_folder(self, *, folder_name=None, **_kwargs):
        return self.children.get(folder_name)


class FakeMailbox:
    def __init__(self, inbox: FakeFolder, folders: Optional[Dict[str, FakeFolder]] = None) -> None:
        self._inbox = inbox
        self._folders = folders or {}

    def inbox_folder(self) -> FakeFolder:
        return self._inbox

    def get_folder(self, *, folder_name=None, **_kwargs):
        return self._folders.get(folder_name)


@pytest.fixture
def outlook_settings(tmp_path: Path) -> OutlookSettings:
    return OutlookSettings(
        client_id="id-di-prova",
        client_secret="segreto-di-prova",
        token_path=tmp_path / "o365_token.txt",
        max_messages_per_poll=17,
    )


def build_client(settings: OutlookSettings, folder: FakeFolder,
                 extensions: Optional[List[str]] = None) -> OutlookClient:
    client = OutlookClient(settings, allowed_extensions=extensions or [".pdf", ".png"])
    client._folder = folder  # come dopo connect(), ma senza rete
    return client


# ------------------------------------------------------------------ cartelle


def test_inbox_predefinita() -> None:
    inbox = FakeFolder()
    assert _resolve_folder(FakeMailbox(inbox), "Inbox") is inbox
    assert _resolve_folder(FakeMailbox(inbox), "Posta in arrivo") is inbox
    assert _resolve_folder(FakeMailbox(inbox), "") is inbox


def test_sottocartella_della_inbox() -> None:
    televisite = FakeFolder(name="Televisite")
    inbox = FakeFolder(children={"Televisite": televisite})
    assert _resolve_folder(FakeMailbox(inbox), "Inbox/Televisite") is televisite


def test_cartella_inesistente_e_un_errore_chiaro() -> None:
    inbox = FakeFolder()
    with pytest.raises(OutlookError, match="Cartella non trovata"):
        _resolve_folder(FakeMailbox(inbox), "Inbox/Manca")


# ------------------------------------------------------------------ messaggi


def test_filtro_su_non_letti_e_finestra_temporale(outlook_settings: OutlookSettings) -> None:
    """La selezione la fa il servizio: si scaricano solo i messaggi utili."""
    folder = FakeFolder([FakeApiMessage()])
    prima = datetime.now(timezone.utc)

    messaggi = build_client(outlook_settings, folder).recent_messages(5)

    filtro = folder.chiamate[0]["query"].render()
    assert "isRead eq false" in filtro
    assert "receivedDateTime ge" in filtro
    momento = datetime.fromisoformat(filtro.split("receivedDateTime ge ")[1].split(" and ")[0])
    assert prima - timedelta(minutes=5, seconds=5) <= momento <= prima - timedelta(minutes=4)
    assert folder.chiamate[0]["limit"] == 17  # max_messages_per_poll
    assert folder.chiamate[0]["order_by"] == "receivedDateTime desc"
    assert [m.subject for m in messaggi] == ["Richiesta"]


def test_senza_filtro_sui_non_letti(outlook_settings: OutlookSettings) -> None:
    folder = FakeFolder([FakeApiMessage()])

    build_client(outlook_settings, folder).recent_messages(5, unread_only=False)

    assert "isRead" not in folder.chiamate[0]["query"].render()


def test_finestra_nulla_non_interroga_la_casella(outlook_settings: OutlookSettings) -> None:
    folder = FakeFolder([FakeApiMessage()])
    assert build_client(outlook_settings, folder).recent_messages(0) == []
    assert folder.chiamate == []


def test_errore_di_rete_diventa_outlook_error(outlook_settings: OutlookSettings) -> None:
    class FolderRotta(FakeFolder):
        def get_messages(self, *a, **k):
            raise RuntimeError("connessione interrotta")

    with pytest.raises(OutlookError, match="Lettura della casella"):
        build_client(outlook_settings, FolderRotta()).recent_messages(5)


def test_client_non_connesso(outlook_settings: OutlookSettings) -> None:
    with pytest.raises(OutlookError, match="connect"):
        OutlookClient(outlook_settings).recent_messages(5)


def test_proprieta_del_messaggio() -> None:
    api = FakeApiMessage()
    api.sender = type("Recipient", (), {"address": "mittente@example.com", "name": "Mario"})()
    message = OutlookMessage(api)

    assert message.entry_id == "AAMk-1"
    assert message.message_id == "<msg-1@example.com>"
    assert message.sender == "mittente@example.com"
    assert message.is_read is False


# ------------------------------------------------------------------ allegati


def test_salva_solo_gli_allegati_previsti(outlook_settings: OutlookSettings, tmp_path: Path) -> None:
    allegati = FakeAttachments([
        FakeAttachment("referto.pdf"),
        FakeAttachment("foglio.xlsx"),                      # estensione non prevista
        FakeAttachment("firma.png", is_inline=True),        # logo nel corpo
        FakeAttachment("inoltrata.eml", attachment_type="item"),  # messaggio allegato
    ])
    message = OutlookMessage(FakeApiMessage(attachments=allegati))

    salvati = build_client(outlook_settings, FakeFolder()).save_attachments(message, tmp_path)

    assert allegati.scaricati is True
    assert [a.original_name for a in salvati] == ["referto.pdf"]
    assert salvati[0].path.read_bytes() == b"contenuto"
    assert salvati[0].size_bytes == len(b"contenuto")


def test_nomi_pericolosi_e_omonimi(outlook_settings: OutlookSettings, tmp_path: Path) -> None:
    allegati = FakeAttachments([
        FakeAttachment("../../fuga.pdf"),
        FakeAttachment("referto.pdf"),
        FakeAttachment("referto.pdf"),
    ])
    message = OutlookMessage(FakeApiMessage(attachments=allegati))

    salvati = build_client(outlook_settings, FakeFolder()).save_attachments(message, tmp_path)

    percorsi = [a.path for a in salvati]
    assert [p.name for p in percorsi] == ["fuga.pdf", "referto.pdf", "referto_2.pdf"]
    assert all(p.parent == tmp_path for p in percorsi)  # nessuna scrittura fuori cartella


def test_allegato_illeggibile_non_blocca_gli_altri(outlook_settings: OutlookSettings,
                                                   tmp_path: Path) -> None:
    class AllegatoRotto(FakeAttachment):
        def save(self, location, custom_name=None):
            raise RuntimeError("contenuto corrotto")

    allegati = FakeAttachments([AllegatoRotto("rotto.pdf"), FakeAttachment("buono.pdf")])
    message = OutlookMessage(FakeApiMessage(attachments=allegati))

    salvati = build_client(outlook_settings, FakeFolder()).save_attachments(message, tmp_path)

    assert [a.original_name for a in salvati] == ["buono.pdf"]


def test_download_non_riuscito_non_solleva(outlook_settings: OutlookSettings, tmp_path: Path) -> None:
    class AllegatiRotti(FakeAttachments):
        def download_attachments(self):
            raise RuntimeError("HTTP 503")

    message = OutlookMessage(FakeApiMessage(attachments=AllegatiRotti([FakeAttachment("x.pdf")])))

    assert build_client(outlook_settings, FakeFolder()).save_attachments(message, tmp_path) == []


# ------------------------------------------------------------------- inoltro


def test_inoltro_compone_la_bozza(outlook_settings: OutlookSettings) -> None:
    draft = FakeDraft(subject="Richiesta")
    api = FakeApiMessage(draft=draft)
    client = build_client(outlook_settings, FakeFolder())

    client.forward(OutlookMessage(api), ["a@example.com"], ["b@example.com"],
                   "[TELEVISITA] ", "Criteri riconosciuti: televisita")

    assert draft.to.indirizzi == ["a@example.com"]
    assert draft.cc.indirizzi == ["b@example.com"]
    assert draft.subject == "[TELEVISITA] Richiesta"
    assert draft.body.startswith("<p>Criteri riconosciuti: televisita</p>")
    assert "originale" in draft.body  # il messaggio originale resta leggibile
    assert draft.inviata is True


def test_nota_su_corpo_di_solo_testo(outlook_settings: OutlookSettings) -> None:
    draft = FakeDraft(body="testo originale", body_type="text")
    api = FakeApiMessage(draft=draft)

    build_client(outlook_settings, FakeFolder()).forward(
        OutlookMessage(api), ["a@example.com"], [], "", "Nota\ncon a capo")

    assert draft.body.startswith("Nota\ncon a capo\r\n")
    assert "<p>" not in draft.body


def test_inoltro_fallito_diventa_outlook_error(outlook_settings: OutlookSettings) -> None:
    class MessaggioRotto(FakeApiMessage):
        def forward(self):
            raise RuntimeError("HTTP 403")

    with pytest.raises(OutlookError, match="Inoltro non riuscito"):
        build_client(outlook_settings, FakeFolder()).forward(
            OutlookMessage(MessaggioRotto()), ["a@example.com"], [], "", "")


# ----------------------------------------------------------------- categoria


def test_categoria_applicata_e_salvata(outlook_settings: OutlookSettings) -> None:
    api = FakeApiMessage()
    build_client(outlook_settings, FakeFolder()).mark_processed(OutlookMessage(api), "Inoltrata")

    assert api.categories == ["Inoltrata"] and api.salvato is True


def test_categoria_gia_presente_non_viene_ripetuta(outlook_settings: OutlookSettings) -> None:
    api = FakeApiMessage(categories=["Inoltrata"])
    build_client(outlook_settings, FakeFolder()).mark_processed(OutlookMessage(api), "Inoltrata")

    assert api.categories == ["Inoltrata"] and api.salvato is False


def test_categoria_non_essenziale_non_ferma_il_flusso(outlook_settings: OutlookSettings) -> None:
    class MessaggioRotto(FakeApiMessage):
        def save_message(self):
            raise RuntimeError("HTTP 500")

    build_client(outlook_settings, FakeFolder()).mark_processed(
        OutlookMessage(MessaggioRotto()), "Inoltrata")  # non deve sollevare


# ------------------------------------------------------------- credenziali


def test_credenziali_mancanti(tmp_path: Path) -> None:
    settings = OutlookSettings(token_path=tmp_path / "token.txt")
    with pytest.raises(OutlookError, match="MS_CLIENT_ID"):
        OutlookClient(settings)._build_account()

    settings.client_id = "id-di-prova"
    with pytest.raises(OutlookError, match="MS_CLIENT_SECRET"):
        OutlookClient(settings)._build_account()


def test_flusso_public_non_richiede_il_segreto(tmp_path: Path) -> None:
    settings = OutlookSettings(client_id="id-di-prova", auth_flow="public",
                               token_path=tmp_path / "token.txt")
    account = OutlookClient(settings)._build_account()

    assert account.con.auth_flow_type == "public"


def test_senza_token_la_connessione_spiega_cosa_fare(tmp_path: Path) -> None:
    settings = OutlookSettings(client_id="id", client_secret="segreto",
                               token_path=tmp_path / "token.txt")
    with pytest.raises(OutlookError, match="authenticate"):
        OutlookClient(settings).connect()
