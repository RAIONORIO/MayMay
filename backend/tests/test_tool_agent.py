from typing import Any

from maymay.agents import (
    ToolAgent,
    select_tool_for_request,
)
from maymay.tools import BaseTool, ToolRegistry


class EchoTool(BaseTool):
    name = "echo"
    description = "Repete um texto."
    parameters: dict[str, Any] = {
        "type": "object",
        "required": [
            "text",
        ],
        "properties": {
            "text": {
                "type": "string",
            },
        },
    }

    def execute(self, arguments: dict[str, Any]) -> str:
        return f"eco: {arguments['text']}"


class ToolCallingClient:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, Any]]] = []

    def chat_message(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        assert tools
        self.calls.append(list(messages))

        if len(self.calls) == 1:
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {
                            "name": "echo",
                            "arguments": {
                                "text": "teste",
                            },
                        },
                    }
                ],
            }

        assert messages[-1] == {
            "role": "tool",
            "tool_name": "echo",
            "content": "eco: teste",
        }

        return {
            "role": "assistant",
            "content": "A ferramenta respondeu: eco: teste",
        }


class ToolIgnoringClient:
    def __init__(self) -> None:
        self.calls = 0

    def chat_message(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        assert tools
        self.calls += 1

        if self.calls == 1:
            return {
                "role": "assistant",
                "content": "Não vou usar ferramentas.",
            }

        assert messages[-1] == {
            "role": "tool",
            "tool_name": "echo",
            "content": "eco: forçado",
        }

        return {
            "role": "assistant",
            "content": "Ferramenta executada.",
        }


def test_select_tool_for_request():
    assert (
        select_tool_for_request("Que horas são?")
        == "get_current_datetime"
    )

    assert (
        select_tool_for_request(
            "Quanto espaço livre há no meu computador?"
        )
        == "get_system_info"
    )

    assert (
        select_tool_for_request("Conte uma história.")
        is None
    )


def test_agent_executes_model_tool_call():
    registry = ToolRegistry(
        [
            EchoTool(),
        ]
    )
    client = ToolCallingClient()
    agent = ToolAgent(
        client=client,
        registry=registry,
    )

    result = agent.run(
        [
            {
                "role": "user",
                "content": "Faça um eco.",
            }
        ]
    )

    assert result == (
        "A ferramenta respondeu: eco: teste"
    )
    assert len(client.calls) == 2


def test_agent_forces_preferred_tool():
    registry = ToolRegistry(
        [
            EchoTool(),
        ]
    )
    client = ToolIgnoringClient()
    agent = ToolAgent(
        client=client,
        registry=registry,
    )

    result = agent.run(
        [
            {
                "role": "user",
                "content": "Use o eco.",
            }
        ],
        preferred_tool="echo",
        preferred_arguments={
            "text": "forçado",
        },
    )

    assert result == "eco: forçado"
    assert client.calls == 1
