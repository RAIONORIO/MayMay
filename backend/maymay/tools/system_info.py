"""Ferramenta de informações locais do computador."""

from __future__ import annotations

import getpass
import json
import os
import platform
import shutil
import socket
import sys
from pathlib import Path
from typing import Any

from maymay.tools.base import BaseTool


def bytes_to_gib(value: int) -> float:
    """Converte bytes para gibibytes."""

    return round(value / (1024 ** 3), 2)


def format_gib(value: float) -> str:
    """Formata um valor em GiB usando vírgula decimal."""

    return f"{value:.2f}".replace(".", ",")


class SystemInfoTool(BaseTool):
    """Consulta informações básicas e não destrutivas do sistema."""

    name = "get_system_info"
    description = (
        "Obtém informações reais do computador local, incluindo "
        "Windows, processador, núcleos, usuário e espaço em disco."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    def execute(self, arguments: dict[str, Any]) -> str:
        """Retorna informações básicas do sistema."""

        del arguments

        home = Path.home()
        disk_root = Path(home.anchor) if home.anchor else home
        disk = shutil.disk_usage(disk_root)

        total_gib = bytes_to_gib(disk.total)
        used_gib = bytes_to_gib(disk.used)
        free_gib = bytes_to_gib(disk.free)

        processor = platform.processor().strip()

        if not processor:
            processor = os.getenv(
                "PROCESSOR_IDENTIFIER",
                "desconhecido",
            )

        result = {
            "operating_system": platform.system(),
            "operating_system_version": platform.version(),
            "release": platform.release(),
            "architecture": platform.machine(),
            "processor": processor,
            "logical_cores": os.cpu_count(),
            "hostname": socket.gethostname(),
            "username": getpass.getuser(),
            "home_directory": str(home),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "disk": {
                "root": str(disk_root),
                "total_gib": total_gib,
                "used_gib": used_gib,
                "free_gib": free_gib,
            },
            "summary": (
                f"Seu computador usa {platform.system()}. "
                f"O disco principal ({disk_root}) possui "
                f"{format_gib(free_gib)} GiB livres, "
                f"{format_gib(used_gib)} GiB usados e "
                f"{format_gib(total_gib)} GiB no total."
            ),
        }

        return json.dumps(
            result,
            ensure_ascii=False,
        )
