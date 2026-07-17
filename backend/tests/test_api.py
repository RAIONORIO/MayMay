from collections.abc import Iterator
from typing import Any

from fastapi.testclient import TestClient

from maymay.api.app import create_app
from maymay.core.config import Settings
from maymay.voice import TtsError


class FakeOllamaClient:
    """Cliente falso usado para testar a API sem chamar o Ollama."""

    def __init__(self) -> None:
        self._tool_round = 0

    def __enter__(self) -> "FakeOllamaClient":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def health(self) -> dict[str, str]:
        return {
            "version": "0.32.0",
        }

    def list_models(self) -> list[str]:
        return [
            "qwen3.5:4b",
        ]

    def chat_stream(
        self,
        messages: list[dict[str, str]],
    ) -> Iterator[str]:
        assert messages[0]["role"] == "system"
        assert messages[-1] == {
            "role": "user",
            "content": "Olá, MayMay.",
        }

        yield "MayMay "
        yield "pronta."

    def chat_message(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        assert tools

        if self._tool_round == 0:
            self._tool_round += 1

            return {
                "role": "assistant",
                "content": (
                    "Não tenho acesso ao horário."
                ),
            }

        assert any(
            message.get("role") == "tool"
            for message in messages
        )

        return {
            "role": "assistant",
            "content": "Agora são 09:53 no horário local.",
        }


class FakeVoiceService:
    """Serviço falso que evita carregar o modelo ONNX nos testes."""

    def __init__(
        self,
        *,
        audio: bytes = b"RIFFfake-wav",
        error: TtsError | None = None,
    ) -> None:
        self.audio = audio
        self.error = error
        self.received_texts: list[str] = []

    def synthesize_wav(
        self,
        text: str,
    ) -> bytes:
        self.received_texts.append(text)

        if self.error is not None:
            raise self.error

        return self.audio


def fake_client_factory(
    _: Settings,
) -> FakeOllamaClient:
    return FakeOllamaClient()


def create_test_client(
    voice_service: FakeVoiceService | None = None,
) -> TestClient:
    settings = Settings(
        ollama_base_url="http://ollama.test",
        ollama_model="qwen3.5:4b",
        request_timeout_seconds=30,
        api_host="127.0.0.1",
        api_port=8765,
    )

    resolved_voice_service = (
        voice_service
        or FakeVoiceService()
    )

    def fake_voice_service_factory(
        _: Settings,
    ) -> FakeVoiceService:
        return resolved_voice_service

    app = create_app(
        settings=settings,
        client_factory=fake_client_factory,
        voice_service_factory=(
            fake_voice_service_factory
        ),
    )

    return TestClient(app)


def test_root():
    with create_test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "assistant": "MayMay",
        "status": "online",
    }


def test_health():
    with create_test_client() as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "online",
        "assistant": "MayMay",
        "model": "qwen3.5:4b",
        "model_available": True,
        "ollama_version": "0.32.0",
    }


def test_models():
    with create_test_client() as client:
        response = client.get("/api/models")

    assert response.status_code == 200
    assert response.json() == {
        "configured": "qwen3.5:4b",
        "models": [
            "qwen3.5:4b",
        ],
    }


def test_tools():
    with create_test_client() as client:
        response = client.get("/api/tools")

    assert response.status_code == 200
    assert response.json() == {
        "tools": [
            "get_current_datetime",
            "get_system_info",
        ],
    }


def test_voice_synthesis():
    voice_service = FakeVoiceService(
        audio=b"RIFFmaymay-test",
    )

    with create_test_client(
        voice_service
    ) as client:
        response = client.post(
            "/api/voice/synthesize",
            json={
                "text": "  Olá, Rai.  ",
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "audio/wav"
    )
    assert response.headers["cache-control"] == (
        "no-store"
    )
    assert response.content == b"RIFFmaymay-test"
    assert voice_service.received_texts == [
        "Olá, Rai.",
    ]


def test_voice_synthesis_error():
    voice_service = FakeVoiceService(
        error=TtsError(
            "Não foi possível gerar o áudio."
        ),
    )

    with create_test_client(
        voice_service
    ) as client:
        response = client.post(
            "/api/voice/synthesize",
            json={
                "text": "Olá, MayMay.",
            },
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "Não foi possível gerar o áudio."
        ),
    }


def test_voice_synthesis_rejects_empty_text():
    with create_test_client() as client:
        response = client.post(
            "/api/voice/synthesize",
            json={
                "text": "   ",
            },
        )

    assert response.status_code == 422


def test_chat_stream():
    with create_test_client() as client:
        response = client.post(
            "/api/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Olá, MayMay.",
                    },
                ],
            },
        )

    assert response.status_code == 200
    assert response.text == "MayMay pronta."


def test_chat_answers_runtime_model_information():
    with create_test_client() as client:
        response = client.post(
            "/api/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Qual modelo local você está usando?"
                        ),
                    },
                ],
            },
        )

    assert response.status_code == 200
    assert response.text == (
        "Sou MayMay e utilizo o modelo local qwen3.5:4b, "
        "executado pelo Ollama no seu computador."
    )


def test_chat_uses_local_tool():
    with create_test_client() as client:
        response = client.post(
            "/api/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Que horas são agora?",
                    },
                ],
            },
        )

    assert response.status_code == 200
    assert response.text.startswith("Agora são ")
    assert " do dia " in response.text