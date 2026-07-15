"""Servidor HTTP local da MayMay."""

from __future__ import annotations

from collections.abc import Callable, Iterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from maymay.api.models import ChatRequest, HealthResponse
from maymay.core.config import Settings
from maymay.core.prompts import build_system_prompt
from maymay.core.runtime_info import answer_runtime_question
from maymay.llm.ollama_client import OllamaClient, OllamaError


ClientFactory = Callable[[Settings], OllamaClient]


CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
]


def create_ollama_client(settings: Settings) -> OllamaClient:
    """Cria o cliente Ollama usado pela API."""

    return OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout=settings.request_timeout_seconds,
    )


def prepare_messages(
    request_body: ChatRequest,
    model_name: str,
) -> list[dict[str, str]]:
    """Converte e prepara as mensagens enviadas pela interface."""

    messages = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in request_body.messages
    ]

    has_system_prompt = any(
        message["role"] == "system"
        for message in messages
    )

    if not has_system_prompt:
        messages.insert(
            0,
            {
                "role": "system",
                "content": build_system_prompt(model_name),
            },
        )

    return messages


def create_app(
    settings: Settings | None = None,
    client_factory: ClientFactory | None = None,
) -> FastAPI:
    """Cria e configura a aplicação FastAPI da MayMay."""

    resolved_settings = settings or Settings.from_environment()
    resolved_client_factory = client_factory or create_ollama_client

    app = FastAPI(
        title="MayMay API",
        description="API local da assistente pessoal MayMay",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = resolved_settings
    app.state.client_factory = resolved_client_factory

    @app.get("/")
    def root() -> dict[str, str]:
        """Informa que o serviço local está em execução."""

        return {
            "assistant": "MayMay",
            "status": "online",
        }

    @app.get(
        "/api/health",
        response_model=HealthResponse,
    )
    def health() -> HealthResponse:
        """Verifica o backend, o Ollama e o modelo configurado."""

        try:
            with resolved_client_factory(resolved_settings) as client:
                version = str(
                    client.health().get(
                        "version",
                        "desconhecida",
                    )
                )
                models = client.list_models()
        except OllamaError as error:
            raise HTTPException(
                status_code=503,
                detail=str(error),
            ) from error

        return HealthResponse(
            status="online",
            assistant="MayMay",
            model=resolved_settings.ollama_model,
            model_available=resolved_settings.ollama_model in models,
            ollama_version=version,
        )

    @app.get("/api/models")
    def models() -> dict[str, object]:
        """Lista os modelos instalados no Ollama."""

        try:
            with resolved_client_factory(resolved_settings) as client:
                installed_models = client.list_models()
        except OllamaError as error:
            raise HTTPException(
                status_code=503,
                detail=str(error),
            ) from error

        return {
            "configured": resolved_settings.ollama_model,
            "models": installed_models,
        }

    @app.post("/api/chat")
    def chat(request_body: ChatRequest) -> StreamingResponse:
        """Envia a conversa ao Ollama e devolve a resposta em streaming."""

        messages = prepare_messages(
            request_body,
            resolved_settings.ollama_model,
        )

        last_user_message = ""

        for message in reversed(request_body.messages):
            if message.role == "user":
                last_user_message = message.content
                break

        runtime_answer = answer_runtime_question(
            last_user_message,
            model_name=resolved_settings.ollama_model,
        )

        if runtime_answer is not None:
            return StreamingResponse(
                iter([runtime_answer]),
                media_type="text/plain; charset=utf-8",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Content-Type-Options": "nosniff",
                },
            )

        def generate_response() -> Iterator[str]:
            try:
                with resolved_client_factory(resolved_settings) as client:
                    yield from client.chat_stream(messages)
            except OllamaError as error:
                yield f"\n\nErro da MayMay: {error}"

        return StreamingResponse(
            generate_response(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "X-Content-Type-Options": "nosniff",
            },
        )

    return app


app = create_app()
