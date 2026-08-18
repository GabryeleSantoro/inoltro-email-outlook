"""Test del caricamento e della validazione della configurazione."""

from __future__ import annotations

from pathlib import Path

import pytest

from inoltro_email.config import ConfigError, Settings

VALID_YAML = """
ocr:
  engine: 2
  max_pdf_pages_per_request: 3
rules:
  keywords: ["televisita"]
  codes: ["1501A"]
  mode: all
forward:
  to: ["destinatario@example.com"]
  dry_run: true
attachments:
  allowed_extensions: ["PDF", ".JPG"]
storage:
  db_path: "state/db.sqlite3"
"""


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_carica_configurazione_valida(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave-di-prova")
    settings = Settings.load(write_config(tmp_path, VALID_YAML))

    assert settings.ocr.api_key == "chiave-di-prova"
    assert settings.rules.codes == ["1501A"]
    assert settings.forward.dry_run is True
    # Le estensioni vengono normalizzate: minuscole e con il punto iniziale.
    assert settings.attachments.allowed_extensions == [".pdf", ".jpg"]


def test_chiave_api_mancante(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OCR_SPACE_API_KEY", raising=False)
    monkeypatch.setattr("inoltro_email.config.load_dotenv", lambda *a, **k: None)
    with pytest.raises(ConfigError, match="OCR_SPACE_API_KEY"):
        Settings.load(write_config(tmp_path, VALID_YAML))


def test_file_assente(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="non trovato"):
        Settings.load(tmp_path / "manca.yaml")


def test_yaml_non_valido(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    with pytest.raises(ConfigError, match="YAML non valido"):
        Settings.load(write_config(tmp_path, "forward: [non\n  - chiuso: ["))


def test_serve_almeno_un_destinatario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML.replace('  to: ["destinatario@example.com"]', "  to: []")
    with pytest.raises(ConfigError, match="forward.to"):
        Settings.load(write_config(tmp_path, yaml_text))


def test_indirizzo_non_valido(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML.replace('"destinatario@example.com"', '"non-un-indirizzo"')
    with pytest.raises(ConfigError, match="non valido"):
        Settings.load(write_config(tmp_path, yaml_text))


def test_modalita_regole_sconosciuta(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML.replace("mode: all", "mode: forse")
    with pytest.raises(ConfigError, match="rules.mode"):
        Settings.load(write_config(tmp_path, yaml_text))


def test_engine_ocr_non_valido(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML.replace("engine: 2", "engine: 7")
    with pytest.raises(ConfigError, match="ocr.engine"):
        Settings.load(write_config(tmp_path, yaml_text))


def test_config_di_esempio_e_valido(monkeypatch: pytest.MonkeyPatch) -> None:
    """config.example.yaml deve poter essere copiato e usato cosi' com'e'."""
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    example = Path(__file__).resolve().parents[1] / "config.example.yaml"
    settings = Settings.load(example)
    assert settings.rules.keywords == ["televisita"]
    assert settings.rules.codes == ["1501A"]
    assert settings.forward.dry_run is True  # default prudente


def test_ensure_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    settings = Settings.load(write_config(tmp_path, VALID_YAML))
    settings.storage.db_path = tmp_path / "dati" / "db.sqlite3"
    settings.logging.file = tmp_path / "registri" / "app.log"
    settings.ensure_directories()
    assert (tmp_path / "dati").is_dir() and (tmp_path / "registri").is_dir()
