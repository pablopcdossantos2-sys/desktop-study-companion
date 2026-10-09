from __future__ import annotations

import json
from pathlib import Path

from desktop_study_companion.runtime_paths import (
    bundled_config_path,
    external_config_path,
)

from .models import (
    AccountabilityConfig,
    ActivityConfig,
    AppConfig,
    AvatarConfig,
    MonitorConfig,
    PersonalityConfig,
    VoiceConfig,
)


def _default_config_path() -> Path:
    candidates = [
        external_config_path(),
        bundled_config_path(),
        Path(__file__).resolve().parents[3] / "config" / "default.json",
    ]
    for candidate in candidates:
        if candidate is not None and candidate.exists():
            return candidate
    raise FileNotFoundError(
        "config/default.json was not found. Run the app from the project folder "
        "or provide an explicit config path."
    )


def load_config(path: str | Path | None = None) -> AppConfig:
    config_path = Path(path) if path else _default_config_path()
    data = json.loads(config_path.read_text(encoding="utf-8"))

    return AppConfig(
        monitor=MonitorConfig(**data.get("monitor", {})),
        activity=ActivityConfig(**data.get("activity", {})),
        accountability=AccountabilityConfig(**data.get("accountability", {})),
        personality=PersonalityConfig(**data.get("personality", {})),
        voice=VoiceConfig(**data.get("voice", {})),
        avatar=AvatarConfig(**data.get("avatar", {})),
    )
