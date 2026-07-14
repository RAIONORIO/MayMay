"""Configurações centrais da MayMay."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Configurações necessárias para executar o núcleo local."""

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3.5:4b"
    request_timeout_seconds: float = 180.0

    @classmethod
    def from_environment(cls) -> "Settings":
        """Carrega as configurações a partir do ambiente."""

        timeout_text = os.getenv("MAYMAY_REQUEST_TIMEOUT", "180")

        try:
            timeout = float(timeout_text)
        except ValueError as error:
            raise ValueError(
                "MAYMAY_REQUEST_TIMEOUT precisa ser um número."
            ) from error

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
        )
