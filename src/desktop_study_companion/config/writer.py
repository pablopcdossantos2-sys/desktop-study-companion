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
