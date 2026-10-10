from __future__ import annotations

import json
import logging
from dataclasses import fields
from pathlib import Path

from desktop_study_companion.runtime_paths import (
    bundled_config_path,
    external_config_path,
    source_default_config_path,
)
from desktop_study_companion.safe_json import quarantine_invalid_json

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

logger = logging.getLogger("desktop_study_companion.config.loader")


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


def _read_config(config_path: Path) -> AppConfig:
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


def _candidate_paths(path: str | Path | None) -> tuple[list[Path], set[Path]]:
    recoverable: set[Path] = set()
    if path is not None:
        explicit = Path(path)
        candidates: list[Path | None] = [
            explicit,
            bundled_config_path(),
            source_default_config_path(),
        ]
        recoverable.add(explicit)
    else:
        external = external_config_path()
        candidates = [
            external,
            bundled_config_path(),
            source_default_config_path(),
        ]
        recoverable.add(external)

    unique: list[Path] = []
    for candidate in candidates:
        if candidate is None:
            continue
        resolved = Path(candidate)
        if resolved not in unique:
            unique.append(resolved)
    return unique, recoverable


def load_config_with_recovery(
    path: str | Path | None = None,
) -> tuple[AppConfig, str | None]:
    candidates, recoverable = _candidate_paths(path)
    failures: list[str] = []
    recovered_from: Path | None = None
    backup: Path | None = None

    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            config = _read_config(candidate)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            failures.append(f"{candidate}: {exc}")
            logger.exception("Invalid configuration path=%s", candidate)
            if candidate in recoverable:
                recovered_from = candidate
                backup = quarantine_invalid_json(candidate)
            continue

        notice = None
        if recovered_from is not None:
            backup_text = f" Cópia preservada em {backup}." if backup else ""
            notice = (
                f"A configuração em {recovered_from} estava inválida e foi "
                f"ignorada. O aplicativo carregou a configuração padrão."
                + backup_text
            )
            logger.warning(notice)
        return config, notice

    detail = "; ".join(failures) if failures else "nenhum arquivo encontrado"
    raise RuntimeError(f"no valid application configuration was found: {detail}")


def load_config(path: str | Path | None = None) -> AppConfig:
    config, _notice = load_config_with_recovery(path)
    return config
