"""Ferramentas locais disponíveis para a MayMay."""

from maymay.tools.base import BaseTool, ToolError
from maymay.tools.datetime_tool import CurrentDateTimeTool
from maymay.tools.registry import ToolRegistry
from maymay.tools.system_info import SystemInfoTool


def create_default_tool_registry() -> ToolRegistry:
    """Cria o registro inicial de ferramentas seguras."""

    return ToolRegistry(
        [
            CurrentDateTimeTool(),
            SystemInfoTool(),
        ]
    )


__all__ = [
    "BaseTool",
    "CurrentDateTimeTool",
    "SystemInfoTool",
    "ToolError",
    "ToolRegistry",
    "create_default_tool_registry",
]
