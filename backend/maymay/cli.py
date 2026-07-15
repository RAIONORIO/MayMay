"""Interface de terminal inicial da MayMay."""

from __future__ import annotations

import argparse
import sys

from maymay.core.config import Settings
from maymay.core.prompts import build_system_prompt
from maymay.llm.ollama_client import OllamaClient, OllamaError


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
    ask_parser.add_argument(
        "message",
        help="Mensagem enviada à MayMay.",
    )

    commands.add_parser(
        "chat",
        help="Inicia uma conversa contínua.",
    )

    serve_parser = commands.add_parser(
        "serve",
        help="Inicia a API local da MayMay.",
    )
    serve_parser.add_argument(
        "--host",
        help="Endereço usado pelo servidor.",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        help="Porta usada pelo servidor.",
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


def run_ask(
    client: OllamaClient,
    message: str,
    system_prompt: str,
) -> None:
    """Executa uma pergunta isolada."""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": message,
        },
    ]

    stream_response(client, messages)


def run_chat(
    client: OllamaClient,
    system_prompt: str,
) -> None:
    """Executa uma conversa contínua em memória."""

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": system_prompt,
        },
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

        if user_message.lower() in {
            "/sair",
            "/quit",
            "/exit",
        }:
            print("Conversa encerrada.")
            return

        messages.append(
            {
                "role": "user",
                "content": user_message,
            },
        )

        print("MayMay> ", end="", flush=True)
        assistant_message = stream_response(
            client,
            messages,
        )

        messages.append(
            {
                "role": "assistant",
                "content": assistant_message,
            },
        )


def run_server(
    settings: Settings,
    host: str | None,
    port: int | None,
) -> None:
    """Inicia o servidor HTTP local da MayMay."""

    import uvicorn

    from maymay.api.app import create_app

    resolved_host = host or settings.api_host
    resolved_port = port or settings.api_port

    print(
        f"MayMay API iniciando em "
        f"http://{resolved_host}:{resolved_port}"
    )

    uvicorn.run(
        create_app(settings),
        host=resolved_host,
        port=resolved_port,
        log_level="info",
    )


def main() -> None:
    """Ponto de entrada da MayMay no terminal."""

    parser = build_parser()
    args = parser.parse_args()
    settings = Settings.from_environment()
    system_prompt = build_system_prompt(
        settings.ollama_model,
    )

    if args.command == "serve":
        run_server(
            settings,
            args.host,
            args.port,
        )
        return

    try:
        with create_client(settings) as client:
            if args.command == "doctor":
                run_doctor(client, settings)
            elif args.command == "ask":
                run_ask(
                    client,
                    args.message,
                    system_prompt,
                )
            elif args.command == "chat":
                run_chat(client, system_prompt)
    except OllamaError as error:
        print(
            f"Erro: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
