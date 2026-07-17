"""Servidor HTTP local da MayMay."""

from __future__ import annotations

from collections.abc import Callable, Iterator

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from maymay.agents import ToolAgent, select_tool_for_request
from maymay.api.models import (
    ChatRequest,
    HealthResponse,
    VoiceSynthesisRequest,
)
from maymay.core.config import Settings
from maymay.core.prompts import build_system_prompt
from maymay.core.runtime_info import answer_runtime_question
from maymay.llm.ollama_client import OllamaClient, OllamaError
from maymay.tools import (
    ToolRegistry,
    create_default_tool_registry,
)
from maymay.voice import SherpaTtsService, TtsError


ClientFactory = Callable[[Settings], OllamaClient]

VoiceServiceFactory = Callable[
    [Settings],
    SherpaTtsService,
]


CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
]


def create_ollama_client(
    settings: Settings,
) -> OllamaClient:
    """Cria o cliente Ollama usado pela API."""

    return OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout=settings.request_timeout_seconds,
    )


def create_voice_service(
    settings: Settings,
) -> SherpaTtsService:
    """Cria o serviço local de síntese de voz."""

    return SherpaTtsService(
        model_dir=settings.voice_model_dir,
        speed=settings.voice_speed,
        num_threads=settings.voice_num_threads,
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
                "content": build_system_prompt(
                    model_name
                ),
            },
        )

    return messages


def create_app(
    settings: Settings | None = None,
    client_factory: ClientFactory | None = None,
    tool_registry: ToolRegistry | None = None,
    voice_service_factory: VoiceServiceFactory | None = None,
) -> FastAPI:
    """Cria e configura a aplicação FastAPI da MayMay."""

    resolved_settings = (
        settings
        or Settings.from_environment()
    )

    resolved_client_factory = (
        client_factory
        or create_ollama_client
    )

    resolved_voice_service_factory = (
        voice_service_factory
        or create_voice_service
    )

    resolved_voice_service = (
        resolved_voice_service_factory(
            resolved_settings
        )
    )

    resolved_tool_registry = (
        tool_registry
        if tool_registry is not None
        else create_default_tool_registry()
    )

    app = FastAPI(
        title="MayMay API",
        description=(
            "API local da assistente pessoal MayMay"
        ),
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
    app.state.client_factory = (
        resolved_client_factory
    )
    app.state.tool_registry = (
        resolved_tool_registry
    )
    app.state.voice_service = (
        resolved_voice_service
    )

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
            with resolved_client_factory(
                resolved_settings
            ) as client:
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
            model_available=(
                resolved_settings.ollama_model
                in models
            ),
            ollama_version=version,
        )

    @app.get("/api/models")
    def models() -> dict[str, object]:
        """Lista os modelos instalados no Ollama."""

        try:
            with resolved_client_factory(
                resolved_settings
            ) as client:
                installed_models = (
                    client.list_models()
                )
        except OllamaError as error:
            raise HTTPException(
                status_code=503,
                detail=str(error),
            ) from error

        return {
            "configured": (
                resolved_settings.ollama_model
            ),
            "models": installed_models,
        }

    @app.get("/api/tools")
    def tools() -> dict[str, list[str]]:
        """Lista as ferramentas atualmente disponíveis."""

        return {
            "tools": (
                resolved_tool_registry.names()
            ),
        }

    @app.post("/api/voice/synthesize")
    def synthesize_voice(
        request_body: VoiceSynthesisRequest,
    ) -> Response:
        """Converte texto em áudio WAV local."""

        try:
            audio = (
                resolved_voice_service
                .synthesize_wav(
                    request_body.text
                )
            )
        except TtsError as error:
            raise HTTPException(
                status_code=503,
                detail=str(error),
            ) from error

        return Response(
            content=audio,
            media_type="audio/wav",
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": (
                    "nosniff"
                ),
            },
        )

    @app.post("/api/chat")
    def chat(
        request_body: ChatRequest,
    ) -> StreamingResponse:
        """Processa conversa, fatos e ferramentas."""

        messages = prepare_messages(
            request_body,
            resolved_settings.ollama_model,
        )

        last_user_message = ""

        for message in reversed(
            request_body.messages
        ):
            if message.role == "user":
                last_user_message = (
                    message.content
                )
                break

        runtime_answer = (
            answer_runtime_question(
                last_user_message,
                model_name=(
                    resolved_settings
                    .ollama_model
                ),
            )
        )

        if runtime_answer is not None:
            return StreamingResponse(
                iter([runtime_answer]),
                media_type=(
                    "text/plain; charset=utf-8"
                ),
                headers={
                    "Cache-Control": "no-cache",
                    "X-Content-Type-Options": (
                        "nosniff"
                    ),
                },
            )

        preferred_tool = (
            select_tool_for_request(
                last_user_message
            )
        )

        if preferred_tool is not None:

            def generate_tool_response() -> Iterator[str]:
                try:
                    with resolved_client_factory(
                        resolved_settings
                    ) as client:
                        agent = ToolAgent(
                            client=client,
                            registry=(
                                resolved_tool_registry
                            ),
                        )

                        yield agent.run(
                            messages,
                            preferred_tool=(
                                preferred_tool
                            ),
                        )
                except OllamaError as error:
                    yield (
                        f"Erro da MayMay: {error}"
                    )

            return StreamingResponse(
                generate_tool_response(),
                media_type=(
                    "text/plain; charset=utf-8"
                ),
                headers={
                    "Cache-Control": "no-cache",
                    "X-Content-Type-Options": (
                        "nosniff"
                    ),
                },
            )

        def generate_response() -> Iterator[str]:
            try:
                with resolved_client_factory(
                    resolved_settings
                ) as client:
                    yield from client.chat_stream(
                        messages
                    )
            except OllamaError as error:
                yield (
                    "\n\nErro da MayMay: "
                    f"{error}"
                )

        return StreamingResponse(
            generate_response(),
            media_type=(
                "text/plain; charset=utf-8"
            ),
            headers={
                "Cache-Control": "no-cache",
                "X-Content-Type-Options": (
                    "nosniff"
                ),
            },
        )

    return app


app = create_app()