from maymay.core.config import Settings


def test_default_settings(monkeypatch):
    monkeypatch.delenv("MAYMAY_OLLAMA_URL", raising=False)
    monkeypatch.delenv("MAYMAY_MODEL", raising=False)
    monkeypatch.delenv("MAYMAY_REQUEST_TIMEOUT", raising=False)

    settings = Settings.from_environment()

    assert settings.ollama_base_url == "http://127.0.0.1:11434"
    assert settings.ollama_model == "qwen3.5:4b"
    assert settings.request_timeout_seconds == 180.0


def test_environment_settings(monkeypatch):
    monkeypatch.setenv("MAYMAY_OLLAMA_URL", "http://localhost:9999/")
    monkeypatch.setenv("MAYMAY_MODEL", "modelo-teste")
    monkeypatch.setenv("MAYMAY_REQUEST_TIMEOUT", "30")

    settings = Settings.from_environment()

    assert settings.ollama_base_url == "http://localhost:9999"
    assert settings.ollama_model == "modelo-teste"
    assert settings.request_timeout_seconds == 30.0
