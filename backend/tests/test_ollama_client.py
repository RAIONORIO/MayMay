import httpx

from maymay.llm.ollama_client import OllamaClient


def test_health_and_model_listing():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.32.0"})

        if request.url.path == "/api/tags":
            return httpx.Response(
                200,
                json={"models": [{"name": "qwen3.5:4b"}]},
            )

        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    with OllamaClient(
        base_url="http://ollama.test",
        model="qwen3.5:4b",
        transport=transport,
    ) as client:
        assert client.health() == {"version": "0.32.0"}
        assert client.list_models() == ["qwen3.5:4b"]


def test_chat_returns_only_final_content():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "thinking": "Este conteúdo não deve aparecer.",
                    "content": "MayMay pronta.",
                },
                "done": True,
            },
        )

    transport = httpx.MockTransport(handler)

    with OllamaClient(
        base_url="http://ollama.test",
        model="qwen3.5:4b",
        transport=transport,
    ) as client:
        assert client.chat(
            [{"role": "user", "content": "Teste"}],
        ) == "MayMay pronta."


def test_stream_ignores_internal_reasoning():
    response_body = "\n".join(
        [
            '{"message":{"thinking":"segredo","content":"May"}}',
            '{"message":{"thinking":"privado","content":"May pronta."}}',
            '{"done":true}',
        ]
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=response_body)

    transport = httpx.MockTransport(handler)

    with OllamaClient(
        base_url="http://ollama.test",
        model="qwen3.5:4b",
        transport=transport,
    ) as client:
        result = "".join(
            client.chat_stream(
                [{"role": "user", "content": "Teste"}],
            )
        )

    assert result == "MayMay pronta."
    assert "segredo" not in result
    assert "privado" not in result
