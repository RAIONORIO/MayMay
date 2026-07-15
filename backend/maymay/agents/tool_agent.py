"""Agente inicial da MayMay capaz de executar ferramentas locais."""

from __future__ import annotations

import json
import unicodedata
from typing import Any

from maymay.llm.ollama_client import OllamaClient, OllamaError
from maymay.tools import ToolError, ToolRegistry


def normalize_text(value: str) -> str:
    """Normaliza texto para classificação simples."""

    normalized = unicodedata.normalize(
        "NFKD",
        value.casefold(),
    )

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


def render_tool_result(result: str) -> str:
    """Obtém a resposta factual preparada pela ferramenta."""

    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return result

    if isinstance(data, dict):
        summary = data.get("summary")

        if isinstance(summary, str) and summary.strip():
            return summary.strip()

    return result


def select_tool_for_request(
    user_message: str,
) -> str | None:
    """Seleciona uma ferramenta para solicitações reconhecidas."""

    message = normalize_text(user_message)

    datetime_markers = (
        "que horas",
        "qual horario",
        "horario atual",
        "hora atual",
        "data de hoje",
        "que dia e hoje",
        "qual a data",
        "dia da semana",
    )

    if any(
        marker in message
        for marker in datetime_markers
    ):
        return "get_current_datetime"

    system_markers = (
        "meu computador",
        "informacoes do computador",
        "informacoes do sistema",
        "status do sistema",
        "meu processador",
        "qual processador",
        "quantos nucleos",
        "espaco em disco",
        "disco livre",
        "sistema operacional",
        "versao do windows",
        "qual windows",
        "nome do computador",
    )

    if any(
        marker in message
        for marker in system_markers
    ):
        return "get_system_info"

    return None


def should_use_tools(user_message: str) -> bool:
    """Indica se existe uma ferramenta adequada à solicitação."""

    return select_tool_for_request(user_message) is not None


class ToolAgent:
    """Executa ferramentas locais e produz uma resposta final."""

    def __init__(
        self,
        *,
        client: OllamaClient,
        registry: ToolRegistry,
    ) -> None:
        self._client = client
        self._registry = registry

    def run(
        self,
        messages: list[dict[str, Any]],
        *,
        preferred_tool: str | None = None,
        preferred_arguments: dict[str, Any] | None = None,
    ) -> str:
        """Executa a conversa, as ferramentas e a resposta final."""

        conversation = list(messages)
        schemas = self._registry.schemas()

        assistant_message = self._client.chat_message(
            conversation,
            tools=schemas,
        )

        raw_tool_calls = assistant_message.get(
            "tool_calls",
            [],
        )

        tool_calls = (
            raw_tool_calls
            if isinstance(raw_tool_calls, list)
            else []
        )

        if not tool_calls and preferred_tool is not None:
            tool_calls = [
                {
                    "type": "function",
                    "function": {
                        "name": preferred_tool,
                        "arguments": dict(
                            preferred_arguments or {}
                        ),
                    },
                }
            ]

            assistant_message = {
                "role": "assistant",
                "content": "",
                "tool_calls": tool_calls,
            }

        if not tool_calls:
            content = assistant_message.get(
                "content",
                "",
            )

            if not isinstance(content, str):
                raise OllamaError(
                    "O agente retornou conteúdo inválido."
                )

            return content

        conversation.append(assistant_message)

        executed_tools = 0
        executed_results: list[str] = []

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue

            function = tool_call.get(
                "function",
                {},
            )

            if not isinstance(function, dict):
                continue

            tool_name = function.get(
                "name",
                "",
            )
            arguments = function.get(
                "arguments",
                {},
            )

            if not isinstance(tool_name, str) or not tool_name:
                continue

            if isinstance(arguments, str):
                try:
                    decoded_arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    decoded_arguments = {}

                arguments = (
                    decoded_arguments
                    if isinstance(decoded_arguments, dict)
                    else {}
                )

            if not isinstance(arguments, dict):
                arguments = {}

            try:
                result = self._registry.execute(
                    tool_name,
                    arguments,
                )
            except ToolError as error:
                result = json.dumps(
                    {
                        "error": str(error),
                    },
                    ensure_ascii=False,
                )

            conversation.append(
                {
                    "role": "tool",
                    "tool_name": tool_name,
                    "content": result,
                }
            )

            executed_tools += 1
            executed_results.append(result)

        if executed_tools == 0:
            raise OllamaError(
                "Nenhuma ferramenta válida pôde ser executada."
            )

        if (
            preferred_tool is not None
            and len(executed_results) == 1
        ):
            return render_tool_result(
                executed_results[0]
            )

        final_message = self._client.chat_message(
            conversation,
            tools=schemas,
        )

        final_content = final_message.get(
            "content",
            "",
        )

        if not isinstance(final_content, str):
            raise OllamaError(
                "O agente retornou uma resposta final inválida."
            )

        if not final_content.strip():
            raise OllamaError(
                "O agente retornou uma resposta final vazia."
            )

        return final_content
