"""Configurações centrais da MayMay."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_VOICE_MODEL_DIR = (
    PROJECT_ROOT
    / "data"
    / "voice"
    / "vits-piper-pt_BR-dii-high"
)


@dataclass(frozen=True, slots=True)
class Settings:
    """Configurações necessárias para executar o núcleo local."""

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3.5:4b"
    request_timeout_seconds: float = 180.0

    api_host: str = "127.0.0.1"
    api_port: int = 8765

    voice_model_dir: Path = DEFAULT_VOICE_MODEL_DIR
    voice_speed: float = 1.0
    voice_num_threads: int = 2

    @classmethod
    def from_environment(cls) -> "Settings":
        """Carrega as configurações a partir do ambiente."""

        timeout_text = os.getenv(
            "MAYMAY_REQUEST_TIMEOUT",
            "180",
        )

        port_text = os.getenv(
            "MAYMAY_API_PORT",
            "8765",
        )

        voice_speed_text = os.getenv(
            "MAYMAY_VOICE_SPEED",
            "1.0",
        )

        voice_threads_text = os.getenv(
            "MAYMAY_VOICE_THREADS",
            "2",
        )

        try:
            timeout = float(timeout_text)
        except ValueError as error:
            raise ValueError(
                "MAYMAY_REQUEST_TIMEOUT precisa ser um número."
            ) from error

        try:
            api_port = int(port_text)
        except ValueError as error:
            raise ValueError(
                "MAYMAY_API_PORT precisa ser um número inteiro."
            ) from error

        try:
            voice_speed = float(voice_speed_text)
        except ValueError as error:
            raise ValueError(
                "MAYMAY_VOICE_SPEED precisa ser um número."
            ) from error

        try:
            voice_num_threads = int(voice_threads_text)
        except ValueError as error:
            raise ValueError(
                "MAYMAY_VOICE_THREADS precisa ser um número inteiro."
            ) from error

        if not 1 <= api_port <= 65535:
            raise ValueError(
                "MAYMAY_API_PORT precisa estar entre 1 e 65535."
            )

        if not 0.5 <= voice_speed <= 2.0:
            raise ValueError(
                "MAYMAY_VOICE_SPEED precisa estar entre 0.5 e 2.0."
            )

        if not 1 <= voice_num_threads <= 16:
            raise ValueError(
                "MAYMAY_VOICE_THREADS precisa estar entre 1 e 16."
            )

        voice_model_dir = Path(
            os.getenv(
                "MAYMAY_VOICE_MODEL_DIR",
                str(DEFAULT_VOICE_MODEL_DIR),
            )
        ).expanduser().resolve()

        return cls(
            ollama_base_url=os.getenv(
                "MAYMAY_OLLAMA_URL",
                "http://127.0.0.1:11434",
            ).rstrip("/"),
            ollama_model=os.getenv(
                "MAYMAY_MODEL",
                "qwen3.5:4b",
            ),
            request_timeout_seconds=timeout,
            api_host=os.getenv(
                "MAYMAY_API_HOST",
                "127.0.0.1",
            ),
            api_port=api_port,
            voice_model_dir=voice_model_dir,
            voice_speed=voice_speed,
            voice_num_threads=voice_num_threads,
        )