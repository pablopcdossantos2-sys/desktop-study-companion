from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

from desktop_study_companion.runtime_paths import (
    bundled_config_path,
    external_config_path,
    source_default_config_path,
)

from .models import (
    AccountabilityConfig,
    ActivityConfig,
    AppConfig,
    AvatarConfig,
    BrainConfig,
    MonitorConfig,
    PersonalityConfig,
    ProactivityConfig,
    SpeechInputConfig,
    VoiceConfig,
)
from .writer import validate_config


def _default_config_path() -> Path:
    candidates = [
        external_config_path(),
        bundled_config_path(),
        source_default_config_path(),
    ]
    for candidate in candidates:
        if candidate is not None and candidate.exists():
            return candidate
    raise FileNotFoundError("config/default.json was not found.")


def _section(cls, raw):
    if raw is None:
        return cls()
    if not isinstance(raw, dict):
        raise ValueError(f"{cls.__name__} configuration must be an object")
    allowed = {field.name for field in fields(cls)}
    return cls(**{key: value for key, value in raw.items() if key in allowed})


def _clean_activity(config: ActivityConfig) -> ActivityConfig:
    def clean(values) -> list[str]:
        if not isinstance(values, list):
            return []
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if not isinstance(value, str):
                continue
            text = value.strip()
            folded = text.casefold()
            if text and folded not in seen:
                result.append(text)
                seen.add(folded)
        return result

    config.productive_keywords = clean(config.productive_keywords)
    config.neutral_keywords = clean(config.neutral_keywords)
    config.distraction_keywords = clean(config.distraction_keywords)
    return config


def load_config(path: str | Path | None = None) -> AppConfig:
    config_path = Path(path) if path else _default_config_path()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("application configuration must be a JSON object")

    config = AppConfig(
        monitor=_section(MonitorConfig, data.get("monitor")),
        activity=_clean_activity(_section(ActivityConfig, data.get("activity"))),
        accountability=_section(AccountabilityConfig, data.get("accountability")),
        personality=_section(PersonalityConfig, data.get("personality")),
        proactivity=_section(ProactivityConfig, data.get("proactivity")),
        voice=_section(VoiceConfig, data.get("voice")),
        speech_input=_section(SpeechInputConfig, data.get("speech_input")),
        brain=_section(BrainConfig, data.get("brain")),
        avatar=_section(AvatarConfig, data.get("avatar")),
    )
    validate_config(config)
    return config
