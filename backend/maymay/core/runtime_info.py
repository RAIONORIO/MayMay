"""Respostas autoritativas sobre a execução atual da MayMay."""

from __future__ import annotations

import unicodedata


def normalize_text(value: str) -> str:
    """Normaliza texto para comparação de intenções simples."""

    normalized = unicodedata.normalize(
        "NFKD",
        value.casefold().strip(),
    )

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


def answer_runtime_question(
    user_message: str,
    *,
    model_name: str,
) -> str | None:
    """
    Responde perguntas sobre informações reais da execução.

    Essas respostas não são delegadas ao modelo de linguagem,
    pois o backend é a fonte confiável desses dados.
    """

    question = normalize_text(user_message)

    asks_about_model = (
        "modelo" in question
        and any(
            marker in question
            for marker in (
                "qual modelo",
                "que modelo",
                "modelo local",
                "modelo de linguagem",
                "modelo voce usa",
                "modelo esta usando",
                "seu modelo",
            )
        )
    )

    asks_about_llm = any(
        marker in question
        for marker in (
            "qual llm",
            "que llm",
            "qual e a llm",
        )
    )

    if asks_about_model or asks_about_llm:
        resolved_model = (
            model_name.strip()
            or "modelo local configurado"
        )

        return (
            "Sou MayMay e utilizo o modelo local "
            f"{resolved_model}, executado pelo Ollama "
            "no seu computador."
        )

    return None
