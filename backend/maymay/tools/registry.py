"""Registro central de ferramentas da MayMay."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from maymay.tools.base import BaseTool, ToolError


class ToolRegistry:
    """Armazena e executa as ferramentas disponíveis."""

    def __init__(
        self,
        tools: Iterable[BaseTool] | None = None,
    ) -> None:
        self._tools: dict[str, BaseTool] = {}

        for tool in tools or []:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        """Registra uma ferramenta pelo nome."""

        if tool.name in self._tools:
            raise ValueError(
                f"A ferramenta '{tool.name}' já está registrada."
            )

        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        """Obtém uma ferramenta registrada."""

        try:
            return self._tools[name]
        except KeyError as error:
            raise ToolError(
                f"Ferramenta desconhecida: {name}"
            ) from error

    def schemas(self) -> list[dict[str, Any]]:
        """Retorna os esquemas enviados ao modelo."""

        return [
            tool.to_ollama_schema()
            for tool in self._tools.values()
        ]

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> str:
        """Executa uma ferramenta registrada."""

        return self.get(name).execute(arguments)

    def names(self) -> list[str]:
        """Lista os nomes das ferramentas registradas."""

        return list(self._tools)
