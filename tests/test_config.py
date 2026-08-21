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


def test_auth_flow_sconosciuto(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML + "outlook:\n  auth_flow: magico\n"
    with pytest.raises(ConfigError, match="outlook.auth_flow"):
        Settings.load(write_config(tmp_path, yaml_text))


def test_flusso_applicativo_richiede_la_casella(tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    """Senza utente connesso non si sa quale casella leggere."""
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML + "outlook:\n  auth_flow: credentials\n"
    with pytest.raises(ConfigError, match="outlook.mailbox"):
        Settings.load(write_config(tmp_path, yaml_text))

    yaml_text += '  mailbox: "casella@example.com"\n'
    settings = Settings.load(write_config(tmp_path, yaml_text))
    assert settings.outlook.mailbox == "casella@example.com"


def test_intervallo_di_controllo_non_valido(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    yaml_text = VALID_YAML + "outlook:\n  poll_interval_minutes: 0\n"
    with pytest.raises(ConfigError, match="poll_interval_minutes"):
        Settings.load(write_config(tmp_path, yaml_text))


def test_credenziali_microsoft_dall_ambiente(tmp_path: Path,
                                             monkeypatch: pytest.MonkeyPatch) -> None:
    """Client id, segreto e tenant non stanno nel YAML ma nell'ambiente."""
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    monkeypatch.setenv("MS_CLIENT_ID", "id-applicazione")
    monkeypatch.setenv("MS_CLIENT_SECRET", "segreto")
    monkeypatch.setenv("MS_TENANT_ID", "contoso.onmicrosoft.com")

    settings = Settings.load(write_config(tmp_path, VALID_YAML))

    assert settings.outlook.client_id == "id-applicazione"
    assert settings.outlook.client_secret == "segreto"
    assert settings.outlook.tenant_id == "contoso.onmicrosoft.com"


def test_tenant_predefinito(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    monkeypatch.delenv("MS_TENANT_ID", raising=False)
    monkeypatch.setattr("inoltro_email.config.load_dotenv", lambda *a, **k: None)

    assert Settings.load(write_config(tmp_path, VALID_YAML)).outlook.tenant_id == "common"


def test_valori_di_controllo_predefiniti(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Senza sezione 'outlook' si controlla la posta ogni 5 minuti, solo non letti."""
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    settings = Settings.load(write_config(tmp_path, VALID_YAML))

    assert settings.outlook.poll_interval_minutes == 5
    assert settings.outlook.lookback_minutes == 5
    assert settings.outlook.unread_only is True


def test_ensure_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_SPACE_API_KEY", "chiave")
    settings = Settings.load(write_config(tmp_path, VALID_YAML))
    settings.storage.db_path = tmp_path / "dati" / "db.sqlite3"
    settings.logging.file = tmp_path / "registri" / "app.log"
    settings.outlook.token_path = tmp_path / "credenziali" / "o365_token.txt"
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
