"""Modelos de entrada e saída da API local da MayMay."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    """Mensagem individual enviada para a conversa."""

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """Impede mensagens compostas apenas por espaços."""

        content = value.strip()

        if not content:
            raise ValueError("A mensagem não pode estar vazia.")

        return content


class ChatRequest(BaseModel):
    """Requisição de conversa enviada pela interface."""

    messages: list[ChatMessage] = Field(min_length=1)


class HealthResponse(BaseModel):
    """Estado atual do backend e do Ollama."""

    status: Literal["online"]
    assistant: str
    model: str
    model_available: bool
    ollama_version: str
