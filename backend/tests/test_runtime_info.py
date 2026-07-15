from maymay.core.runtime_info import answer_runtime_question


def test_answers_model_question():
    answer = answer_runtime_question(
        "Qual modelo local você está usando?",
        model_name="qwen3.5:4b",
    )

    assert answer == (
        "Sou MayMay e utilizo o modelo local qwen3.5:4b, "
        "executado pelo Ollama no seu computador."
    )


def test_answers_llm_question():
    answer = answer_runtime_question(
        "Qual LLM você usa?",
        model_name="llama3.2:latest",
    )

    assert answer is not None
    assert "llama3.2:latest" in answer
    assert "Ollama" in answer


def test_ignores_unrelated_question():
    answer = answer_runtime_question(
        "Como está o clima hoje?",
        model_name="qwen3.5:4b",
    )

    assert answer is None
