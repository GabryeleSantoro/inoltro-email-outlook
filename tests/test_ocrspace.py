"""Test del client HTTP verso ocr.space (rete simulata con `responses`)."""

from __future__ import annotations

from pathlib import Path

import pytest
import responses

from inoltro_email.config import OcrSettings
from inoltro_email.ocr.ocrspace import OcrSpaceClient, OcrSpaceError

ENDPOINT = "https://api.ocr.space/parse/image"


@pytest.fixture
def image(tmp_path: Path) -> Path:
    path = tmp_path / "referto.png"
    path.write_bytes(b"finto-contenuto-png")
    return path


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Azzera l'attesa fra i tentativi: i test non devono impiegare secondi."""
    monkeypatch.setattr("inoltro_email.ocr.ocrspace.time.sleep", lambda _seconds: None)


def make_client(**overrides) -> OcrSpaceClient:
    return OcrSpaceClient(OcrSettings(api_key="chiave", endpoint=ENDPOINT, **overrides))


@responses.activate
def test_estrae_il_testo_da_tutte_le_pagine(image: Path) -> None:
    responses.add(responses.POST, ENDPOINT, status=200, json={
        "ParsedResults": [
            {"ParsedText": "TELEVISITA", "FileParseExitCode": 1},
            {"ParsedText": "codice 1501A", "FileParseExitCode": 1},
        ],
        "OCRExitCode": 1,
        "IsErroredOnProcessing": False,
    })
    result = make_client().parse_file(image)
    assert "TELEVISITA" in result.text and "1501A" in result.text


@responses.activate
def test_invia_chiave_e_parametri_corretti(image: Path) -> None:
    responses.add(responses.POST, ENDPOINT, status=200, json={
        "ParsedResults": [{"ParsedText": "x", "FileParseExitCode": 1}],
        "OCRExitCode": 1, "IsErroredOnProcessing": False,
    })
    make_client(engine=2).parse_file(image)

    request = responses.calls[0].request
    assert request.headers["apikey"] == "chiave"
    body = request.body.decode("utf-8", errors="ignore") if isinstance(request.body, bytes) else str(request.body)
    assert "OCREngine" in body and "PNG" in body
    # L'engine 2 rileva la lingua da solo: il parametro non va inviato.
    assert 'name="language"' not in body


@responses.activate
def test_language_inviato_con_engine_1(image: Path) -> None:
    responses.add(responses.POST, ENDPOINT, status=200, json={
        "ParsedResults": [{"ParsedText": "x", "FileParseExitCode": 1}],
        "OCRExitCode": 1, "IsErroredOnProcessing": False,
    })
    make_client(engine=1, language="ita").parse_file(image)
    body = responses.calls[0].request.body
    body = body.decode("utf-8", errors="ignore") if isinstance(body, bytes) else str(body)
    assert "ita" in body


@responses.activate
def test_errore_applicativo_con_http_200(image: Path) -> None:
    """ocr.space segnala gli errori nel corpo, non nello status code."""
    responses.add(responses.POST, ENDPOINT, status=200, json={
        "IsErroredOnProcessing": True,
        "ErrorMessage": ["File size exceeds the maximum limit"],
        "OCRExitCode": 99,
    })
    with pytest.raises(OcrSpaceError, match="maximum limit"):
        make_client().parse_file(image)


@responses.activate
def test_riprova_dopo_un_429_e_riesce(image: Path) -> None:
    responses.add(responses.POST, ENDPOINT, status=429)
    responses.add(responses.POST, ENDPOINT, status=200, json={
        "ParsedResults": [{"ParsedText": "televisita 1501A", "FileParseExitCode": 1}],
        "OCRExitCode": 1, "IsErroredOnProcessing": False,
    })
    assert "1501A" in make_client(max_retries=3).parse_file(image).text
    assert len(responses.calls) == 2


@responses.activate
def test_non_riprova_su_chiave_non_valida(image: Path) -> None:
    responses.add(responses.POST, ENDPOINT, status=401)
    with pytest.raises(OcrSpaceError, match="401"):
        make_client(max_retries=3).parse_file(image)
    assert len(responses.calls) == 1  # nessun tentativo aggiuntivo


@responses.activate
def test_si_arrende_dopo_i_tentativi_previsti(image: Path) -> None:
    for _ in range(3):
        responses.add(responses.POST, ENDPOINT, status=503)
    with pytest.raises(OcrSpaceError):
        make_client(max_retries=3).parse_file(image)
    assert len(responses.calls) == 3


@responses.activate
def test_risultati_vuoti_sono_un_errore(image: Path) -> None:
    responses.add(responses.POST, ENDPOINT, status=200,
                  json={"ParsedResults": [], "IsErroredOnProcessing": False})
    with pytest.raises(OcrSpaceError, match="nessun risultato|non ha restituito"):
        make_client().parse_file(image)
