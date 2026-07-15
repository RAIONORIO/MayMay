"""Contratos fundamentais do sistema de ferramentas da MayMay."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ToolError(RuntimeError):
    """Erro ocorrido durante a execução de uma ferramenta."""


class BaseTool(ABC):
    """Contrato implementado por todas as ferramentas da MayMay."""

    name: str
    description: str
    parameters: dict[str, Any]

    def to_ollama_schema(self) -> dict[str, Any]:
        """Converte a ferramenta para o formato aceito pelo Ollama."""

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @abstractmethod
    def execute(self, arguments: dict[str, Any]) -> str:
        """Executa a ferramenta e devolve um resultado textual."""
