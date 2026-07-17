from __future__ import annotations

import wave
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pytest

from maymay.voice import (
    SherpaTtsService,
    VoiceModelError,
    encode_pcm16_wav,
)


@dataclass
class FakeAudio:
    """Áudio falso retornado pelo mecanismo de teste."""

    samples: list[float]
    sample_rate: int


class FakeTtsEngine:
    """Mecanismo falso para testar sem carregar o modelo real."""

    def __init__(self) -> None:
        self.received_texts: list[str] = []

    def generate(
        self,
        text: str,
        config: object,
    ) -> FakeAudio:
        self.received_texts.append(text)

        return FakeAudio(
            samples=[
                0.0,
                0.5,
                -0.5,
                1.0,
                -1.0,
            ],
            sample_rate=22050,
        )


def test_synthesize_wav_uses_engine_once(
    tmp_path: Path,
):
    engine = FakeTtsEngine()
    factory_calls = 0

    def create_engine() -> FakeTtsEngine:
        nonlocal factory_calls

        factory_calls += 1

        return engine

    service = SherpaTtsService(
        model_dir=tmp_path,
        engine_factory=create_engine,
    )

    first_audio = service.synthesize_wav(
        "  Olá, Rai.  "
    )

    second_audio = service.synthesize_wav(
        "Eu sou a MayMay."
    )

    assert factory_calls == 1

    assert engine.received_texts == [
        "Olá, Rai.",
        "Eu sou a MayMay.",
    ]

    assert first_audio.startswith(b"RIFF")
    assert second_audio.startswith(b"RIFF")

    with wave.open(
        BytesIO(first_audio),
        "rb",
    ) as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 22050
        assert wav_file.getnframes() == 5


def test_synthesize_rejects_empty_text(
    tmp_path: Path,
):
    service = SherpaTtsService(
        model_dir=tmp_path,
        engine_factory=FakeTtsEngine,
    )

    with pytest.raises(
        ValueError,
        match="não pode estar vazio",
    ):
        service.synthesize_wav("   ")


def test_missing_voice_model_is_reported(
    tmp_path: Path,
):
    service = SherpaTtsService(
        model_dir=tmp_path,
    )

    with pytest.raises(
        VoiceModelError,
        match="modelo de voz local está incompleto",
    ):
        service.synthesize_wav(
            "Olá, Rai."
        )


def test_encode_pcm16_wav_rejects_invalid_rate():
    with pytest.raises(
        ValueError,
        match="precisa ser positiva",
    ):
        encode_pcm16_wav(
            samples=[0.0],
            sample_rate=0,
        )