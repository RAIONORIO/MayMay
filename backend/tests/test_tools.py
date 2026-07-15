import json
from typing import Any

import pytest

from maymay.tools import (
    BaseTool,
    CurrentDateTimeTool,
    SystemInfoTool,
    ToolRegistry,
)


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
        return str(arguments["text"])


def test_tool_schema():
    schema = EchoTool().to_ollama_schema()

    assert schema["type"] == "function"
    assert schema["function"]["name"] == "echo"
    assert schema["function"]["parameters"]["required"] == [
        "text",
    ]


def test_registry_registers_and_executes():
    registry = ToolRegistry(
        [
            EchoTool(),
        ]
    )

    result = registry.execute(
        "echo",
        {
            "text": "MayMay",
        },
    )

    assert result == "MayMay"
    assert registry.names() == [
        "echo",
    ]


def test_registry_rejects_duplicate_tool():
    registry = ToolRegistry(
        [
            EchoTool(),
        ]
    )

    with pytest.raises(ValueError):
        registry.register(EchoTool())


def test_current_datetime_tool():
    result = json.loads(
        CurrentDateTimeTool().execute({})
    )

    assert result["date"]
    assert result["time"]
    assert result["datetime_iso"]
    assert result["timezone"]
    assert result["summary"].startswith("Agora são ")


def test_system_info_tool():
    result = json.loads(
        SystemInfoTool().execute({})
    )

    assert result["operating_system"]
    assert result["hostname"]
    assert result["username"]
    assert result["logical_cores"]
    assert result["disk"]["total_gib"] > 0
    assert result["disk"]["free_gib"] >= 0
    assert "GiB livres" in result["summary"]
    assert "GiB no total" in result["summary"]
