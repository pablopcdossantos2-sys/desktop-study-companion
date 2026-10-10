from __future__ import annotations

import json
import logging
import time
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
from .writer import brain_transport_security_issue, validate_config

logger = logging.getLogger("desktop_study_companion.config.loader")


def _section(cls, raw):
    if raw is None:
        return cls()
    if not isinstance(raw, dict):
        raise ValueError(f"{cls.__name__} configuration must be an object")
    allowed = {field.name for field in fields(cls)}
    return cls(**{key: value for key, value in raw.items() if key in allowed})


def _clean_string_list(values) -> list[str]:
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


def _clean_activity(config: ActivityConfig) -> ActivityConfig:
    config.productive_keywords = _clean_string_list(
        config.productive_keywords
    )
    config.neutral_keywords = _clean_string_list(config.neutral_keywords)
    config.distraction_keywords = _clean_string_list(
        config.distraction_keywords
    )
    return config


def _clean_proactivity(config: ProactivityConfig) -> ProactivityConfig:
    for name in (
        "activation_phrases",
        "focus_phrases",
        "recovery_phrases",
        "celebration_phrases",
        "reset_phrases",
    ):
        setattr(config, name, _clean_string_list(getattr(config, name)))
    return config


def _read_text_with_retry(
    path: Path,
    *,
    attempts: int = 3,
    delay_seconds: float = 0.05,
) -> str:
    last_error: OSError | None = None
    for attempt in range(max(1, attempts)):
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                raise
            time.sleep(delay_seconds * (attempt + 1))
    if last_error is not None:
        raise last_error
    raise OSError(f"could not read {path}")


def _read_config(config_path: Path) -> AppConfig:
    data = json.loads(_read_text_with_retry(config_path))
    if not isinstance(data, dict):
        raise ValueError("application configuration must be a JSON object")

    config = AppConfig(
        monitor=_section(MonitorConfig, data.get("monitor")),
        activity=_clean_activity(_section(ActivityConfig, data.get("activity"))),
        accountability=_section(AccountabilityConfig, data.get("accountability")),
        personality=_section(PersonalityConfig, data.get("personality")),
        proactivity=_clean_proactivity(
            _section(ProactivityConfig, data.get("proactivity"))
        ),
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
    notices: list[str] = []

    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            config = _read_config(candidate)
        except OSError as exc:
            failures.append(f"{candidate}: {exc}")
            logger.exception(
                "Configuration could not be read after retries path=%s",
                candidate,
            )
            if candidate in recoverable:
                notices.append(
                    f"Não foi possível ler temporariamente {candidate}. "
                    "O arquivo foi mantido intacto e uma configuração de "
                    "fallback foi carregada."
                )
            continue
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            failures.append(f"{candidate}: {exc}")
            logger.exception("Invalid configuration path=%s", candidate)
            if candidate in recoverable:
                backup = quarantine_invalid_json(candidate)
                backup_text = (
                    f" Cópia preservada em {backup}."
                    if backup is not None
                    else ""
                )
                notices.append(
                    f"A configuração em {candidate} estava inválida e foi "
                    "ignorada. O aplicativo carregou uma configuração de "
                    "fallback." + backup_text
                )
            continue

        security_issue = brain_transport_security_issue(config)
        if security_issue:
            config.brain.enabled = False
            notices.append(security_issue)
            logger.warning(security_issue)

        notice = " ".join(notices).strip() or None
        return config, notice

    detail = "; ".join(failures) if failures else "nenhum arquivo encontrado"
    raise RuntimeError(f"no valid application configuration was found: {detail}")


def load_config(path: str | Path | None = None) -> AppConfig:
    config, _notice = load_config_with_recovery(path)
    return config
