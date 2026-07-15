from maymay.core.prompts import build_system_prompt


def test_system_prompt_includes_current_model():
    prompt = build_system_prompt("qwen3.5:4b")

    assert "MayMay" in prompt
    assert "qwen3.5:4b" in prompt
    assert "Ollama" in prompt
    assert "português do Brasil" in prompt


def test_system_prompt_accepts_another_model():
    prompt = build_system_prompt("llama3.2:latest")

    assert "llama3.2:latest" in prompt
    assert "qwen3.5:4b" not in prompt
