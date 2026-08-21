"""Test del caricamento e della validazione della configurazione."""

from __future__ import annotations

from pathlib import Path

import pytest

from inoltro_email.config import ConfigError, Settings

VALID_YAML = """
api:
  host: "127.0.0.1"
  port: 9000
screening:
  keywords: ["telemedicina", "televisita"]
  mode: any
rules:
  keywords: ["telemedicina"]
  codes: ["1501A"]
  mode: all
ocr:
  engine: 2
  max_pdf_pages_per_request: 3
attachments:
  allowed_extensions: ["PDF", ".JPG"]
logging:
  level: "WARNING"
  file: null
"""


@pytest.fixture(autouse=True)
def ambiente_pulito(monkeypatch: pytest.MonkeyPatch) -> None:
    """I test non devono dipendere dal .env della macchina di sviluppo."""
    monkeypatch.setattr("inoltro_email.config.load_dotenv", lambda *a, **k: None)
    for name in ("OCR_SPACE_API_KEY", "SERVICE_API_KEY", "API_HOST", "PORT"):
        monkeypatch.delenv(name, raising=False)


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_carica_configurazione_valida(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave-di-prova")
    settings = Settings.load(write_config(tmp_path, VALID_YAML))

    assert settings.ocr.api_key == "chiave-di-prova"
    assert settings.api.port == 9000
    assert settings.screening.keywords == ["telemedicina", "televisita"]
    assert settings.rules.codes == ["1501A"]
    # Le estensioni vengono normalizzate: minuscole e con il punto iniziale.
    assert settings.attachments.allowed_extensions == [".pdf", ".jpg"]


def test_chiave_ocr_mancante(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="OCR_SPACE_API_KEY"):
        Settings.load(write_config(tmp_path, VALID_YAML))


def test_file_esplicito_assente(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="non trovato"):
        Settings.load(tmp_path / "manca.yaml")


def test_senza_file_valgono_i_valori_predefiniti(tmp_path: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    """In un container si configura tutto da variabili d'ambiente."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    settings = Settings.load()

    assert settings.api.port == 8000
    assert settings.screening.keywords == ["telemedicina", "televisita"]
    assert settings.rules.keywords == ["telemedicina"]
    assert settings.rules.codes == ["1501A"]


def test_ambiente_ha_la_precedenza(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    monkeypatch.setenv("SERVICE_API_KEY", "chiave-power-automate")
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "8080")

    settings = Settings.load(write_config(tmp_path, VALID_YAML))

    assert settings.api.api_key == "chiave-power-automate"
    assert settings.api.host == "0.0.0.0"
    assert settings.api.port == 8080  # sovrascrive il 9000 del YAML


def test_porta_non_numerica(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    monkeypatch.setenv("PORT", "ottomila")
    with pytest.raises(ConfigError, match="PORT"):
        Settings.load(write_config(tmp_path, VALID_YAML))


def test_yaml_non_valido(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    with pytest.raises(ConfigError, match="YAML non valido"):
        Settings.load(write_config(tmp_path, "rules: [non\n  - chiuso: ["))


def test_sezione_non_mappa(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    with pytest.raises(ConfigError, match="sezione 'rules'"):
        Settings.load(write_config(tmp_path, "rules:\n  - televisita\n"))


def test_modalita_regole_sconosciuta(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML.replace("  mode: all", "  mode: forse")
    with pytest.raises(ConfigError, match="rules.mode"):
        Settings.load(write_config(tmp_path, yaml_text))


def test_screening_senza_parole(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML.replace('  keywords: ["telemedicina", "televisita"]', "  keywords: []")
    with pytest.raises(ConfigError, match="screening.keywords"):
        Settings.load(write_config(tmp_path, yaml_text))


def test_engine_ocr_non_valido(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML.replace("engine: 2", "engine: 7")
    with pytest.raises(ConfigError, match="ocr.engine"):
        Settings.load(write_config(tmp_path, yaml_text))


def test_porta_fuori_intervallo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML.replace("port: 9000", "port: 70000")
    with pytest.raises(ConfigError, match="api.port"):
        Settings.load(write_config(tmp_path, yaml_text))


def test_soglia_di_prenotazione_fuori_intervallo(tmp_path: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML + "sentiment:\n  booking_threshold: 3.0\n"
    with pytest.raises(ConfigError, match="booking_threshold"):
        Settings.load(write_config(tmp_path, yaml_text))


def test_config_di_esempio_e_valido(monkeypatch: pytest.MonkeyPatch) -> None:
    """config.example.yaml deve poter essere copiato e usato cosi' com'e'."""
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    example = Path(__file__).resolve().parents[1] / "config.example.yaml"
    settings = Settings.load(example)

    assert settings.screening.keywords == ["telemedicina", "televisita"]
    assert settings.screening.mode == "any"
    assert settings.rules.keywords == ["telemedicina"]
    assert settings.rules.codes == ["1501A"]
    assert settings.attachments.include_inline_images is True


def test_ensure_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    settings = Settings.load(write_config(tmp_path, VALID_YAML))
    settings.logging.file = tmp_path / "registri" / "servizio.log"
    settings.ensure_directories()
    assert (tmp_path / "dati").is_dir() and (tmp_path / "registri").is_dir()
    assert (tmp_path / "credenziali").is_dir()


def test_impostazioni_log_predefinite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Senza sezione 'logging' si scrive un file nuovo per ogni sessione."""
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    settings = Settings.load(write_config(tmp_path, VALID_YAML))

    assert settings.logging.file == Path("logs/inoltro.log")
    assert settings.logging.per_session is True
    assert settings.logging.keep_sessions == 30


def test_impostazioni_log_dal_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML + """
logging:
  level: "debug"
  file: "registri/app.log"
  per_session: false
  keep_sessions: 5
"""
    settings = Settings.load(write_config(tmp_path, yaml_text))

    assert settings.logging.level == "DEBUG"
    assert settings.logging.file == Path("registri/app.log")
    assert settings.logging.per_session is False
    assert settings.logging.keep_sessions == 5


def test_keep_sessions_negativo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML + "\nlogging:\n  keep_sessions: -1\n"
    with pytest.raises(ConfigError, match="keep_sessions"):
        Settings.load(write_config(tmp_path, yaml_text))
