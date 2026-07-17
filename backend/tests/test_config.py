from pathlib import Path

import pytest

from maymay.core.config import (
    DEFAULT_VOICE_MODEL_DIR,
    Settings,
)


ENVIRONMENT_VARIABLES = [
    "MAYMAY_OLLAMA_URL",
    "MAYMAY_MODEL",
    "MAYMAY_REQUEST_TIMEOUT",
    "MAYMAY_API_HOST",
    "MAYMAY_API_PORT",
    "MAYMAY_VOICE_MODEL_DIR",
    "MAYMAY_VOICE_SPEED",
    "MAYMAY_VOICE_THREADS",
]


def clear_environment(monkeypatch) -> None:
    for variable_name in ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(
            variable_name,
            raising=False,
        )


def test_default_settings(monkeypatch):
    clear_environment(monkeypatch)

    settings = Settings.from_environment()

    assert settings.ollama_base_url == (
        "http://127.0.0.1:11434"
    )
    assert settings.ollama_model == "qwen3.5:4b"
    assert settings.request_timeout_seconds == 180.0
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8765

    assert settings.voice_model_dir == (
        DEFAULT_VOICE_MODEL_DIR.resolve()
    )
    assert settings.voice_speed == 1.0
    assert settings.voice_num_threads == 2


def test_environment_settings(
    monkeypatch,
    tmp_path: Path,
):
    clear_environment(monkeypatch)

    voice_model_dir = tmp_path / "voice-model"

    monkeypatch.setenv(
        "MAYMAY_OLLAMA_URL",
        "http://localhost:9999/",
    )
    monkeypatch.setenv(
        "MAYMAY_MODEL",
        "modelo-teste",
    )
    monkeypatch.setenv(
        "MAYMAY_REQUEST_TIMEOUT",
        "30",
    )
    monkeypatch.setenv(
        "MAYMAY_API_HOST",
        "0.0.0.0",
    )
    monkeypatch.setenv(
        "MAYMAY_API_PORT",
        "9000",
    )
    monkeypatch.setenv(
        "MAYMAY_VOICE_MODEL_DIR",
        str(voice_model_dir),
    )
    monkeypatch.setenv(
        "MAYMAY_VOICE_SPEED",
        "1.15",
    )
    monkeypatch.setenv(
        "MAYMAY_VOICE_THREADS",
        "4",
    )

    settings = Settings.from_environment()

    assert settings.ollama_base_url == (
        "http://localhost:9999"
    )
    assert settings.ollama_model == "modelo-teste"
    assert settings.request_timeout_seconds == 30.0
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 9000
    assert settings.voice_model_dir == (
        voice_model_dir.resolve()
    )
    assert settings.voice_speed == 1.15
    assert settings.voice_num_threads == 4


@pytest.mark.parametrize(
    ("variable_name", "value", "message"),
    [
        (
            "MAYMAY_VOICE_SPEED",
            "rápida",
            "MAYMAY_VOICE_SPEED precisa ser um número.",
        ),
        (
            "MAYMAY_VOICE_SPEED",
            "3",
            (
                "MAYMAY_VOICE_SPEED precisa estar "
                "entre 0.5 e 2.0."
            ),
        ),
        (
            "MAYMAY_VOICE_THREADS",
            "muitas",
            (
                "MAYMAY_VOICE_THREADS precisa ser "
                "um número inteiro."
            ),
        ),
        (
            "MAYMAY_VOICE_THREADS",
            "0",
            (
                "MAYMAY_VOICE_THREADS precisa estar "
                "entre 1 e 16."
            ),
        ),
    ],
)
def test_invalid_voice_settings(
    monkeypatch,
    variable_name: str,
    value: str,
    message: str,
):
    clear_environment(monkeypatch)

    monkeypatch.setenv(
        variable_name,
        value,
    )

    with pytest.raises(
        ValueError,
        match=message,
    ):
        Settings.from_environment()