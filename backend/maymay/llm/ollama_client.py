"""Cliente próprio da MayMay para a API local do Ollama."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx


class OllamaError(RuntimeError):
    """Erro retornado ou provocado durante uma operação com o Ollama."""


class OllamaClient:
    """Executa conversas com modelos locais pelo Ollama."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout: float = 180.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.model = model
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            transport=transport,
        )

    def __enter__(self) -> "OllamaClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Encerra os recursos HTTP."""

        self._client.close()

    def health(self) -> dict[str, Any]:
        """Verifica se o serviço do Ollama está disponível."""

        try:
            response = self._client.get("/api/version")
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise OllamaError(
                "Não foi possível acessar o Ollama local."
            ) from error

    def list_models(self) -> list[str]:
        """Retorna os nomes dos modelos instalados."""

        try:
            response = self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise OllamaError(
                "Não foi possível consultar os modelos instalados."
            ) from error

        return [
            str(item["name"])
            for item in data.get("models", [])
            if isinstance(item, dict) and item.get("name")
        ]

    def chat(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        """Executa uma conversa sem streaming."""

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
        }

        try:
            response = self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise OllamaError(
                "O Ollama não conseguiu gerar uma resposta."
            ) from error

        if error_message := data.get("error"):
            raise OllamaError(str(error_message))

        message = data.get("message", {})
        content = message.get("content", "")

        if not isinstance(content, str):
            raise OllamaError("O Ollama retornou uma resposta inválida.")

        return content

    def chat_stream(
        self,
        messages: list[dict[str, str]],
    ) -> Iterator[str]:
        """
        Executa uma conversa em streaming.

        O campo de raciocínio interno do modelo é deliberadamente ignorado.
        Somente o conteúdo final é exibido para o usuário.
        """

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "think": False,
        }

        try:
            with self._client.stream(
                "POST",
                "/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError as error:
                        raise OllamaError(
                            "O Ollama retornou um bloco JSON inválido."
                        ) from error

                    if error_message := data.get("error"):
                        raise OllamaError(str(error_message))

                    message = data.get("message", {})
                    content = message.get("content", "")

                    if isinstance(content, str) and content:
                        yield content

                    if data.get("done") is True:
                        break

        except httpx.HTTPError as error:
            raise OllamaError(
                "A comunicação em streaming com o Ollama falhou."
            ) from error
