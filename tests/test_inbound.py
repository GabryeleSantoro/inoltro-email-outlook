"""Test della lettura del payload inviato da Power Automate."""

from __future__ import annotations

import base64

import pytest
from conftest import attachment_payload, b64, email_payload

from inoltro_email.inbound import InboundError, decode_base64, html_to_text, parse_email
from inoltro_email.models import Origine


def test_legge_oggetto_corpo_e_mittente() -> None:
    email = parse_email(email_payload())

    assert email.subject == "Richiesta prenotazione televisita"
    assert "prenotare una televisita" in email.body_text
    assert email.sender == "paziente@example.com"
    assert email.internet_message_id.startswith("<msg-")
    assert email.key == email.internet_message_id


def test_corpo_html_ridotto_a_testo() -> None:
    payload = email_payload(
        body="<html><body><p>Buongiorno,</p><div>vorrei una <b>televisita</b>.</div>"
             "<style>p{color:red}</style></body></html>",
        isHtml=True,
    )
    email = parse_email(payload)

    assert "Buongiorno," in email.body_text
    assert "vorrei una televisita." in email.body_text
    assert "color:red" not in email.body_text  # lo stile non e' testo del messaggio


def test_html_riconosciuto_anche_senza_flag() -> None:
    email = parse_email(email_payload(body="<div>Richiesta di <b>telemedicina</b></div>"))
    assert email.body_text == "Richiesta di telemedicina"


def test_entita_html_decodificate() -> None:
    email = parse_email(email_payload(body="<p>Visita &egrave; urgente &amp; necessaria</p>",
                                      isHtml=True))
    assert "è urgente & necessaria" in email.body_text


def test_forma_graph_del_corpo_e_del_mittente() -> None:
    """Microsoft Graph annida corpo e mittente in oggetti dedicati."""
    payload = {
        "subject": "Televisita",
        "body": {"contentType": "html", "content": "<p>Testo del messaggio</p>"},
        "from": {"emailAddress": {"address": "medico@example.com", "name": "Studio"}},
    }
    email = parse_email(payload)

    assert email.body_text == "Testo del messaggio"
    assert email.sender == "medico@example.com"


def test_chiavi_con_maiuscole_accettate() -> None:
    email = parse_email({"Subject": "Telemedicina", "Body": "corpo del messaggio"})

    assert email.subject == "Telemedicina"
    assert email.body_text == "corpo del messaggio"


def test_allegati_decodificati() -> None:
    payload = email_payload(attachments=[attachment_payload("impegnativa.pdf", b"%PDF-1.4 finto")])
    email = parse_email(payload)

    assert len(email.attachments) == 1
    allegato = email.attachments[0]
    assert allegato.name == "impegnativa.pdf"
    assert allegato.content == b"%PDF-1.4 finto"
    assert allegato.origine is Origine.ALLEGATO
    assert allegato.extension == ".pdf"


def test_allegato_inline_marcato_come_foto_del_corpo() -> None:
    payload = email_payload(attachments=[
        attachment_payload("foto.jpg", b"jpeg", content_type="image/jpeg", inline=True),
    ])
    email = parse_email(payload)

    assert email.attachments[0].origine is Origine.CORPO


def test_allegati_office365_desktop_annidati_in_properties() -> None:
    """PAD serializza gli oggetti del connettore in ``Properties``."""
    payload = email_payload(attachments=[
        {
            "Properties": attachment_payload("impegnativa.pdf", b"%PDF"),
            "TypeId": None,
        },
        {
            "Properties": attachment_payload(
                "image001.jpg", b"jpeg", content_type="image/jpeg", inline=True,
            ),
            "TypeId": None,
        },
    ])

    email = parse_email(payload)

    assert [(item.name, item.content, item.origine) for item in email.attachments] == [
        ("impegnativa.pdf", b"%PDF", Origine.ALLEGATO),
        ("image001.jpg", b"jpeg", Origine.CORPO),
    ]


def test_foto_inline_escluse_su_richiesta() -> None:
    payload = email_payload(attachments=[
        attachment_payload("foto.jpg", b"jpeg", content_type="image/jpeg", inline=True),
        attachment_payload("impegnativa.pdf", b"%PDF"),
    ])
    email = parse_email(payload, include_inline_images=False)

    assert [item.name for item in email.attachments] == ["impegnativa.pdf"]


def test_immagine_data_uri_nel_corpo_diventa_allegato() -> None:
    """La foto incollata nel corpo arriva come <img src="data:...">."""
    immagine = base64.b64encode(b"contenuto-png").decode()
    payload = email_payload(
        body=f'<p>Ecco l\'impegnativa:</p><img src="data:image/png;base64,{immagine}">',
        isHtml=True,
    )
    email = parse_email(payload)

    assert len(email.attachments) == 1
    foto = email.attachments[0]
    assert foto.origine is Origine.CORPO
    assert foto.name.endswith(".png")
    assert foto.content == b"contenuto-png"


def test_immagini_remote_nel_corpo_ignorate() -> None:
    """Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato."""
    payload = email_payload(body='<p>testo</p><img src="https://example.com/logo.png">',
                            isHtml=True)
    assert parse_email(payload).attachments == []


def test_allegato_oltre_il_limite_scartato() -> None:
    payload = email_payload(attachments=[attachment_payload("grande.pdf", b"x" * 100)])
    email = parse_email(payload, max_attachment_bytes=10)

    assert email.attachments == []


def test_allegato_senza_estensione_prende_quella_del_mime() -> None:
    payload = email_payload(attachments=[
        attachment_payload("scansione", b"jpeg", content_type="image/jpeg"),
    ])
    assert parse_email(payload).attachments[0].name == "scansione.jpg"


def test_allegato_con_base64_rotto_ignorato_senza_bloccare_gli_altri() -> None:
    payload = email_payload(attachments=[
        {"name": "rotto.pdf", "contentBytes": "!!!non-base64!!!"},
        attachment_payload("buono.pdf", b"%PDF"),
    ])
    email = parse_email(payload)

    assert [item.name for item in email.attachments] == ["buono.pdf"]


def test_payload_non_oggetto_rifiutato() -> None:
    with pytest.raises(InboundError, match="oggetto JSON"):
        parse_email(["non", "un", "oggetto"])


def test_email_vuota_rifiutata() -> None:
    with pytest.raises(InboundError, match="ne' oggetto ne' corpo"):
        parse_email({"subject": "", "body": ""})


def test_base64_tollerante_a_spazi_e_padding() -> None:
    valore = b64(b"ciao")
    assert decode_base64(f"  {valore[:2]}\n{valore[2:]}  ") == b"ciao"
    assert decode_base64(valore.rstrip("=")) == b"ciao"


def test_html_to_text_mantiene_gli_a_capo() -> None:
    assert html_to_text("<p>prima riga</p><p>seconda riga</p>") == "prima riga\n\nseconda riga"


# ------------------------------------- allegati indicati per percorso su disco


def test_allegato_letto_dal_percorso(tmp_path) -> None:
    """Il flusso salva il file e manda solo il percorso (campo 'attchment')."""
    from inoltro_email.config import LocalFileSettings

    file_allegato = tmp_path / "impegnativa.png"
    file_allegato.write_bytes(b"contenuto di prova")

    email = parse_email(
        {"subject": "Televisita", "body": "In allegato.", "attchment": str(file_allegato)},
        local_files=LocalFileSettings(),
    )

    assert len(email.attachments) == 1
    allegato = email.attachments[0]
    assert allegato.name == "impegnativa.png"
    assert allegato.source_path == file_allegato.resolve()
    assert allegato.size_bytes == len(b"contenuto di prova")
    assert allegato.has_content is True
    assert email.warnings == []


def test_piu_percorsi_in_elenco(tmp_path) -> None:
    from inoltro_email.config import LocalFileSettings

    primo = tmp_path / "uno.png"
    secondo = tmp_path / "due.pdf"
    primo.write_bytes(b"a")
    secondo.write_bytes(b"b")

    email = parse_email(
        {"subject": "Televisita", "body": "x", "attchment": [str(primo), str(secondo)]},
        local_files=LocalFileSettings(),
    )

    assert [item.name for item in email.attachments] == ["uno.png", "due.pdf"]


def test_percorso_windows_ritrovato_per_nome(tmp_path) -> None:
    """Servizio su un'altra macchina: il file si cerca nelle cartelle indicate."""
    from inoltro_email.config import LocalFileSettings

    (tmp_path / "image (2).png").write_bytes(b"foto")

    email = parse_email(
        {
            "subject": "Televisita",
            "body": "x",
            "attchment": r"C:\Users\user\Documents\Power Automate\Allegati\image (2).png",
        },
        local_files=LocalFileSettings(search_directories=[tmp_path]),
    )

    assert [item.name for item in email.attachments] == ["image (2).png"]


def test_percorso_mancante_diventa_un_avviso() -> None:
    from inoltro_email.config import LocalFileSettings

    email = parse_email(
        {"subject": "Televisita", "body": "x", "attchment": r"C:\Allegati\sparito.pdf"},
        local_files=LocalFileSettings(),
    )

    assert email.attachments == []
    assert len(email.warnings) == 1
    assert "sparito.pdf" in email.warnings[0]


def test_percorso_fuori_dalle_cartelle_consentite(tmp_path) -> None:
    """Un payload non deve poter far leggere un file qualsiasi della macchina."""
    from inoltro_email.config import LocalFileSettings

    consentita = tmp_path / "allegati"
    consentita.mkdir()
    riservato = tmp_path / "segreto.pdf"
    riservato.write_bytes(b"riservato")

    email = parse_email(
        {"subject": "Televisita", "body": "x", "attchment": str(riservato)},
        local_files=LocalFileSettings(allowed_directories=[consentita]),
    )

    assert email.attachments == []
    assert "cartelle consentite" in email.warnings[0]


def test_lettura_dei_file_locali_disattivabile(tmp_path) -> None:
    from inoltro_email.config import LocalFileSettings

    file_allegato = tmp_path / "impegnativa.png"
    file_allegato.write_bytes(b"x")

    email = parse_email(
        {"subject": "Televisita", "body": "x", "attchment": str(file_allegato)},
        local_files=LocalFileSettings(enabled=False),
    )

    assert email.attachments == []
    assert "disattivata" in email.warnings[0]


def test_campo_date_usato_come_data_di_ricezione() -> None:
    email = parse_email({"subject": "Televisita", "body": "x", "date": "08/20/2026 10:26"})

    assert email.received_at == "08/20/2026 10:26"


def test_corpo_non_risolto_dal_flusso_diventa_un_avviso() -> None:
    """Nei log: il corpo arriva come "Unknown Property 'HtmlBody'"."""
    email = parse_email({"subject": "Accettata: OPAT", "body": "Unknown Property 'HtmlBody'"})

    assert email.body_text == ""
    assert "Corpo non risolto" in email.warnings[0]
