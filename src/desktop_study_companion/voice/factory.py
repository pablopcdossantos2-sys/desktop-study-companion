from __future__ import annotations

from pathlib import Path

from desktop_study_companion.config.models import VoiceConfig

from .piper_tts import PiperNeuralTTS
from .windows_sapi import WindowsSapiTTS


def create_tts_engine(config: VoiceConfig, data_dir: Path):
    if not config.enabled:
        return None

    sapi = WindowsSapiTTS(
        rate=config.rate,
        volume=config.volume,
        voice_token_id=config.voice_id,
    )

    if config.engine == "sapi":
        return sapi

    fallback = sapi if config.fallback_to_sapi else None
    if fallback is None:
        sapi.close()

    return PiperNeuralTTS(
        model_id=config.piper_voice_id,
        model_dir=data_dir / "models" / "piper",
        volume=config.volume,
        length_scale=config.piper_length_scale,
        noise_scale=config.piper_noise_scale,
        noise_w_scale=config.piper_noise_w_scale,
        fallback=fallback,
    )
