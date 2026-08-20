"""Test della lettura tollerante del JSON prodotto da Power Automate.

I payload di questo file sono presi dai log del servizio: il flusso costruisce
il JSON concatenando stringhe, quindi arriva quasi sempre non valido.
"""

from __future__ import annotations

import json

import pytest

from inoltro_email.rawjson import RawJsonError, loads_tolerant


def test_json_valido_non_viene_toccato() -> None:
    payload, riparazioni = loads_tolerant(json.dumps({"subject": "ciao", "n": 3}))

    assert payload == {"subject": "ciao", "n": 3}
    assert riparazioni == []


def test_a_capo_dentro_il_corpo() -> None:
    """"Invalid control character": l'HTML arriva con gli a capo veri."""
    raw = '{"subject":"prova","body":"<html>\n<head>\n</head>\n</html>\n"}'

    payload, riparazioni = loads_tolerant(raw)

    assert payload["subject"] == "prova"
    assert payload["body"] == "<html>\n<head>\n</head>\n</html>\n"
    assert any("carattere di controllo" in nota for nota in riparazioni)


def test_virgolette_degli_attributi_html() -> None:
    """"Expecting ',' delimiter": style="..." chiude la stringa a meta'."""
    raw = '{"subject":"prova","body":"<style type=\"text/css\"> P {margin:0} </style>","date":"x"}'

    payload, riparazioni = loads_tolerant(raw)

    assert payload["body"] == '<style type="text/css"> P {margin:0} </style>'
    assert payload["date"] == "x"
    assert any("virgolette non protette" in nota for nota in riparazioni)


def test_virgolette_dentro_l_oggetto_seguite_dai_due_punti() -> None:
    """Il caso insidioso: la virgoletta e' seguita da ':' ma non chiude nulla."""
    raw = '{"subject":"Audit News | Lettura "Mario Carrara": Gramsci","date":"05/16/2026"}'

    payload, _ = loads_tolerant(raw)

    assert payload["subject"] == 'Audit News | Lettura "Mario Carrara": Gramsci'
    assert payload["date"] == "05/16/2026"


def test_percorso_windows_con_escape_inesistenti() -> None:
    raw = r'{"attchment":"C:\Users\user\Documents\Power Automate\Allegati\image.png"}'

    payload, riparazioni = loads_tolerant(raw)

    assert payload["attchment"] == r"C:\Users\user\Documents\Power Automate\Allegati\image.png"
    assert any("percorso Windows" in nota for nota in riparazioni)


def test_piu_allegati_affiancati_diventano_un_elenco() -> None:
    """Il flusso scrive i percorsi in fila, senza ripetere la chiave."""
    raw = r'{"subject":"x","attchment":"C:\Allegati\uno.png","C:\Allegati\due.pdf"}'

    payload, riparazioni = loads_tolerant(raw)

    assert payload["attchment"] == [r"C:\Allegati\uno.png", r"C:\Allegati\due.pdf"]
    assert any("piu' valori per la chiave" in nota for nota in riparazioni)


def test_elenchi_e_oggetti_annidati_restano_leggibili() -> None:
    raw = '{"attachments":[{"name":"a.pdf","isInline":false},{"name":"b\npdf"}],"n":2}'

    payload, _ = loads_tolerant(raw)

    assert payload["attachments"][0] == {"name": "a.pdf", "isInline": False}
    assert payload["attachments"][1]["name"] == "b\npdf"
    assert payload["n"] == 2


def test_payload_del_log_letto_per_intero() -> None:
    """Tutti e tre i guasti insieme, come arrivano davvero."""
    raw = (
        '{"subject":"R: Agende telemedicina - NEUROLOGIA","body":"<html>\n'
        '<body dir="ltr">\n'
        '<div class="elementToProof" style="font-size: 12pt;">\n'
        "L'agenda del dr. Squillante e' stata configurata come da richiesta.</div>\n"
        '</body>\n</html>\n","date":"08/20/2026 10:25",'
        r'"attchment":"C:\Users\user\Documents\Power Automate\Allegati\image (2).png"}'
    )

    payload, riparazioni = loads_tolerant(raw)

    assert payload["subject"] == "R: Agende telemedicina - NEUROLOGIA"
    assert "Squillante" in payload["body"]
    assert payload["date"] == "08/20/2026 10:25"
    assert payload["attchment"].endswith(r"Allegati\image (2).png")
    assert len(riparazioni) >= 3


def test_spazzatura_resta_un_errore() -> None:
    """Se dalla riparazione non esce nulla di utile, e' giusto rifiutare."""
    with pytest.raises(RawJsonError):
        loads_tolerant("{non json")


def test_corpo_vuoto_resta_un_errore() -> None:
    with pytest.raises(RawJsonError):
        loads_tolerant("   ")
