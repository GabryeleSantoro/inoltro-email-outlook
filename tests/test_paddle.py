"""Test dell'adapter PaddleOCR senza caricare pesi o librerie native."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from inoltro_email.config import OcrSettings
from inoltro_email.ocr.paddle import OcrError, PaddleOcrClient


class FakeEngine:
    def __init__(self, pages):
        self.pages = pages
        self.paths: list[str] = []

    def predict(self, path: str):
        self.paths.append(path)
        return self.pages


def configured(tmp_path: Path) -> OcrSettings:
    settings = OcrSettings(model_cache_dir=tmp_path / "cache")
    models = settings.model_cache_dir / "official_models"
    for name in (
        settings.detection_model,
        settings.recognition_model,
        "PP-LCNet_x1_0_doc_ori",
    ):
        (models / name).mkdir(parents=True, exist_ok=True)
    return settings


def test_unisce_testo_da_tutte_le_pagine(tmp_path: Path) -> None:
    image = tmp_path / "referto.png"
    image.write_bytes(b"png")
    engine = FakeEngine([
        {"res": {"rec_texts": ["TELEMEDICINA"]}},
        {"res": {"rec_texts": ["codice 1501A"]}},
    ])
    client = PaddleOcrClient(configured(tmp_path), engine_factory=lambda **_: engine)

    result = client.parse_file(image)

    assert result.text == "TELEMEDICINA\ncodice 1501A"
    assert result.exit_code == 1
    assert engine.paths == [str(image)]


def test_risposta_vuota_e_errore(tmp_path: Path) -> None:
    image = tmp_path / "vuota.png"
    image.write_bytes(b"png")
    client = PaddleOcrClient(
        configured(tmp_path), engine_factory=lambda **_: FakeEngine([{"res": {"rec_texts": []}}])
    )

    with pytest.raises(OcrError, match="non ha riconosciuto"):
        client.parse_file(image)


def test_cache_incompleta_blocca_il_server_prima_del_motore(tmp_path: Path) -> None:
    settings = OcrSettings(model_cache_dir=tmp_path / "cache")

    with pytest.raises(OcrError, match="prepara-ocr"):
        PaddleOcrClient(settings, engine_factory=lambda **_: FakeEngine([]))


def test_eccezione_motore_diventa_errore_ocr(tmp_path: Path) -> None:
    image = tmp_path / "rotta.png"
    image.write_bytes(b"png")

    class BrokenEngine:
        def predict(self, _path: str):
            raise RuntimeError("backend rotto")

    client = PaddleOcrClient(configured(tmp_path), engine_factory=lambda **_: BrokenEngine())
    with pytest.raises(OcrError, match="PaddleOCR non riuscito"):
        client.parse_file(image)


@pytest.mark.paddle
@pytest.mark.skipif(
    os.environ.get("RUN_PADDLE_SMOKE") != "1",
    reason="richiede pesi PaddleOCR pre-caricati; eseguire con RUN_PADDLE_SMOKE=1",
)
def test_smoke_reale_italiano(tmp_path: Path) -> None:
    """Verifica opzionale con il vero modello Latin e cache locale pronta."""
    from inoltro_email.ocr.paddle import _create_check_image

    image = tmp_path / "smoke.png"
    _create_check_image(image)
    result = PaddleOcrClient(OcrSettings()).parse_file(image)

    assert "TELEMEDICINA" in result.text.upper()
    assert "1501A" in result.text.upper()
