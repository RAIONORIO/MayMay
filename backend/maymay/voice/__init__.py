"""Recursos de voz da MayMay."""

from maymay.voice.tts import (
    SherpaTtsService,
    TtsError,
    VoiceModelError,
    encode_pcm16_wav,
)


__all__ = [
    "SherpaTtsService",
    "TtsError",
    "VoiceModelError",
    "encode_pcm16_wav",
]
