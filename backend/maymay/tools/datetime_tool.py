"""Ferramenta local de data e hora."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from maymay.tools.base import BaseTool


class CurrentDateTimeTool(BaseTool):
    """Consulta a data e a hora local do computador."""

    name = "get_current_datetime"
    description = (
        "Obtém a data, o horário e o fuso horário atuais "
        "diretamente do computador do usuário."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    def execute(self, arguments: dict[str, Any]) -> str:
        """Retorna a data e a hora locais."""

        del arguments

        current = datetime.now().astimezone()

        result = {
            "datetime_iso": current.isoformat(),
            "date": current.strftime("%d/%m/%Y"),
            "time": current.strftime("%H:%M:%S"),
            "weekday": current.strftime("%A"),
            "timezone": current.tzname() or "desconhecido",
            "summary": (
                f"Agora são {current.strftime('%H:%M')} "
                f"do dia {current.strftime('%d/%m/%Y')}."
            ),
        }

        return json.dumps(
            result,
            ensure_ascii=False,
        )
