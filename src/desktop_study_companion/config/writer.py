from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import AppConfig


def validate_config(config: AppConfig) -> None:
    p = config.accountability
    thresholds = [
        p.gentle_after_seconds,
        p.firm_after_seconds,
        p.direct_after_seconds,
        p.insistent_after_seconds,
    ]
    if any(value < 0 for value in thresholds):
        raise ValueError("accountability thresholds cannot be negative")
    if thresholds != sorted(thresholds):
        raise ValueError(
            "accountability thresholds must be in ascending order"
        )
    if config.monitor.poll_interval_ms < 200:
        raise ValueError("monitor poll interval must be at least 200 ms")

    personality = config.personality
    for name in (
        "warmth",
        "sarcasm",
        "strictness",
        "patience",
        "humor",
        "initiative",
    ):
        value = getattr(personality, name)
        if not 0 <= value <= 100:
            raise ValueError(f"{name} must be between 0 and 100")

    if not -10 <= config.voice.rate <= 10:
        raise ValueError("voice rate must be between -10 and 10")
    if not 0 <= config.voice.volume <= 100:
        raise ValueError("voice volume must be between 0 and 100")

    if not config.speech_input.model.strip():
        raise ValueError("speech input model cannot be empty")
    if not config.speech_input.language.strip():
        raise ValueError("speech input language cannot be empty")
    if config.speech_input.device not in {"cpu", "cuda", "auto"}:
        raise ValueError("speech input device must be cpu, cuda or auto")
    if not 2 <= config.speech_input.max_record_seconds <= 120:
        raise ValueError(
            "speech input max_record_seconds must be between 2 and 120"
        )

    if not 0 <= config.brain.temperature <= 2:
        raise ValueError("brain temperature must be between 0 and 2")
    if not 32 <= config.brain.max_tokens <= 8192:
        raise ValueError("brain max_tokens must be between 32 and 8192")
    if not 3 <= config.brain.timeout_seconds <= 300:
        raise ValueError("brain timeout must be between 3 and 300 seconds")
    if not 2 <= config.brain.history_messages <= 100:
        raise ValueError("brain history_messages must be between 2 and 100")
    if config.brain.enabled:
        if not config.brain.base_url.strip():
            raise ValueError("brain base_url is required when enabled")
        if not config.brain.model.strip():
            raise ValueError("brain model is required when enabled")
        if not config.brain.base_url.startswith(("http://", "https://")):
            raise ValueError("brain base_url must start with http:// or https://")

    if not 220 <= config.avatar.width <= 900:
        raise ValueError("avatar width must be between 220 and 900")
    if not 320 <= config.avatar.height <= 1100:
        raise ValueError("avatar height must be between 320 and 1100")


def save_config(config: AppConfig, path: str | Path) -> Path:
    validate_config(config)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target
