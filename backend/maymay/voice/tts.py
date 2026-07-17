"""Síntese de voz local da MayMay com sherpa-onnx."""

from __future__ import annotations

import sys
import wave
from array import array
from collections.abc import Callable, Sequence
from io import BytesIO
from pathlib import Path
from typing import Protocol, cast

import sherpa_onnx


class TtsError(RuntimeError):
    """Erro base da síntese de voz da MayMay."""


class VoiceModelError(TtsError):
    """Indica que o modelo local de voz está ausente ou incompleto."""


class GeneratedAudio(Protocol):
    """Estrutura mínima de áudio retornada pelo sherpa-onnx."""

    samples: Sequence[float]
    sample_rate: int


class TtsEngine(Protocol):
    """Contrato mínimo usado pelo serviço de síntese."""

    def generate(
        self,
        text: str,
        config: object,
    ) -> GeneratedAudio:
        """Gera amostras de áudio para um texto."""


EngineFactory = Callable[[], TtsEngine]


class SherpaTtsService:
    """Gera áudio WAV usando um modelo VITS/Piper local."""

    MODEL_FILENAME = "pt_BR-dii-high.onnx"
    TOKENS_FILENAME = "tokens.txt"
    DATA_DIRNAME = "espeak-ng-data"

    def __init__(
        self,
        model_dir: Path,
        *,
        speed: float = 1.0,
        num_threads: int = 2,
        engine_factory: EngineFactory | None = None,
    ) -> None:
        if not 0.5 <= speed <= 2.0:
            raise ValueError(
                "A velocidade da voz precisa estar entre 0.5 e 2.0."
            )

        if not 1 <= num_threads <= 16:
            raise ValueError(
                "A quantidade de threads precisa estar entre 1 e 16."
            )

        self.model_dir = model_dir.expanduser().resolve()
        self.speed = speed
        self.num_threads = num_threads

        self._engine_factory = engine_factory
        self._engine: TtsEngine | None = None

    @property
    def model_path(self) -> Path:
        """Retorna o caminho do modelo ONNX."""

        return self.model_dir / self.MODEL_FILENAME

    @property
    def tokens_path(self) -> Path:
        """Retorna o caminho do arquivo de tokens."""

        return self.model_dir / self.TOKENS_FILENAME

    @property
    def data_dir(self) -> Path:
        """Retorna a pasta com os dados do eSpeak NG."""

        return self.model_dir / self.DATA_DIRNAME

    def synthesize_wav(self, text: str) -> bytes:
        """Converte texto em um arquivo WAV mantido em memória."""

        content = text.strip()

        if not content:
            raise ValueError(
                "O texto para síntese não pode estar vazio."
            )

        engine = self._get_engine()
        generation_config = sherpa_onnx.GenerationConfig()

        generation_config.sid = 0
        generation_config.speed = self.speed
        generation_config.silence_scale = 0.2

        audio = engine.generate(
            content,
            generation_config,
        )

        if len(audio.samples) == 0:
            raise TtsError(
                "O mecanismo de voz não gerou amostras de áudio."
            )

        return encode_pcm16_wav(
            samples=audio.samples,
            sample_rate=audio.sample_rate,
        )

    def synthesize_to_file(
        self,
        text: str,
        output_path: Path,
    ) -> Path:
        """Converte texto em voz e salva o resultado em um arquivo WAV."""

        resolved_output = output_path.expanduser().resolve()

        resolved_output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        resolved_output.write_bytes(
            self.synthesize_wav(text)
        )

        return resolved_output

    def _get_engine(self) -> TtsEngine:
        """Carrega o mecanismo apenas na primeira utilização."""

        if self._engine is None:
            factory = (
                self._engine_factory
                if self._engine_factory is not None
                else self._build_engine
            )

            self._engine = factory()

        return self._engine

    def _build_engine(self) -> TtsEngine:
        """Cria o mecanismo sherpa-onnx com o modelo Dii."""

        self._validate_model_files()

        config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=str(self.model_path),
                    tokens=str(self.tokens_path),
                    data_dir=str(self.data_dir),
                ),
                provider="cpu",
                debug=False,
                num_threads=self.num_threads,
            ),
            max_num_sentences=1,
        )

        if not config.validate():
            raise VoiceModelError(
                "A configuração do modelo de voz é inválida."
            )

        return cast(
            TtsEngine,
            sherpa_onnx.OfflineTts(config),
        )

    def _validate_model_files(self) -> None:
        """Confirma que os arquivos necessários estão disponíveis."""

        missing_paths: list[Path] = []

        if not self.model_path.is_file():
            missing_paths.append(self.model_path)

        if not self.tokens_path.is_file():
            missing_paths.append(self.tokens_path)

        if not self.data_dir.is_dir():
            missing_paths.append(self.data_dir)

        if missing_paths:
            missing_text = ", ".join(
                str(path)
                for path in missing_paths
            )

            raise VoiceModelError(
                "O modelo de voz local está incompleto. "
                f"Caminhos ausentes: {missing_text}"
            )


def encode_pcm16_wav(
    samples: Sequence[float],
    sample_rate: int,
) -> bytes:
    """Converte amostras normalizadas em WAV mono PCM de 16 bits."""

    if sample_rate <= 0:
        raise ValueError(
            "A taxa de amostragem precisa ser positiva."
        )

    pcm_samples = array(
        "h",
        (
            max(
                -32768,
                min(
                    32767,
                    round(float(sample) * 32767),
                ),
            )
            for sample in samples
        ),
    )

    if sys.byteorder != "little":
        pcm_samples.byteswap()

    output = BytesIO()

    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_samples.tobytes())

    return output.getvalue()