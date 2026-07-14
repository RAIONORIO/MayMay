"""Interface de terminal inicial da MayMay."""

from __future__ import annotations

import argparse
import sys

from maymay.core.config import Settings
from maymay.llm.ollama_client import OllamaClient, OllamaError


SYSTEM_PROMPT = """
Você é MayMay, uma assistente pessoal local em desenvolvimento.
Responda sempre em português do Brasil, de forma direta e clara.
Não revele raciocínio interno, cadeia de pensamento ou anotações privadas.
""".strip()


def build_parser() -> argparse.ArgumentParser:
    """Cria os comandos disponíveis no terminal."""

    parser = argparse.ArgumentParser(
        prog="maymay",
        description="Assistente pessoal local MayMay",
    )

    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser(
        "doctor",
        help="Verifica o Ollama e o modelo configurado.",
    )

    ask_parser = commands.add_parser(
        "ask",
        help="Envia uma pergunta única para a MayMay.",
    )
    ask_parser.add_argument("message", help="Mensagem enviada à MayMay.")

    commands.add_parser(
        "chat",
        help="Inicia uma conversa contínua.",
    )

    return parser


def create_client(settings: Settings) -> OllamaClient:
    """Cria o cliente Ollama usando as configurações atuais."""

    return OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout=settings.request_timeout_seconds,
    )


def stream_response(
    client: OllamaClient,
    messages: list[dict[str, str]],
) -> str:
    """Exibe e devolve a resposta recebida em streaming."""

    chunks: list[str] = []

    for chunk in client.chat_stream(messages):
        print(chunk, end="", flush=True)
        chunks.append(chunk)

    print()
    return "".join(chunks)


def run_doctor(client: OllamaClient, settings: Settings) -> None:
    """Verifica serviço e modelo configurado."""

    version = client.health().get("version", "desconhecida")
    models = client.list_models()

    print(f"Ollama: funcionando, versão {version}")
    print(f"Modelo configurado: {settings.ollama_model}")

    if settings.ollama_model in models:
        print("Modelo: instalado e disponível")
        return

    print("Modelo: não encontrado")
    print("Modelos instalados:")

    for model in models:
        print(f"- {model}")

    raise SystemExit(1)


def run_ask(client: OllamaClient, message: str) -> None:
    """Executa uma pergunta isolada."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    stream_response(client, messages)


def run_chat(client: OllamaClient) -> None:
    """Executa uma conversa contínua em memória."""

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    print("MayMay Chat")
    print("Digite /sair para encerrar.")
    print()

    while True:
        try:
            user_message = input("Você> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nConversa encerrada.")
            return

        if not user_message:
            continue

        if user_message.lower() in {"/sair", "/quit", "/exit"}:
            print("Conversa encerrada.")
            return

        messages.append(
            {"role": "user", "content": user_message},
        )

        print("MayMay> ", end="", flush=True)
        assistant_message = stream_response(client, messages)

        messages.append(
            {"role": "assistant", "content": assistant_message},
        )


def main() -> None:
    """Ponto de entrada da MayMay no terminal."""

    parser = build_parser()
    args = parser.parse_args()
    settings = Settings.from_environment()

    try:
        with create_client(settings) as client:
            if args.command == "doctor":
                run_doctor(client, settings)
            elif args.command == "ask":
                run_ask(client, args.message)
            elif args.command == "chat":
                run_chat(client)
    except OllamaError as error:
        print(f"Erro: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
