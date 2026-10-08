from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class MonitorConfig:
    poll_interval_ms: int = 1000


@dataclass(slots=True)
class ActivityConfig:
    productive_keywords: list[str] = field(default_factory=list)
    neutral_keywords: list[str] = field(default_factory=list)
    distraction_keywords: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AccountabilityConfig:
    gentle_after_seconds: int = 60
    firm_after_seconds: int = 180
    direct_after_seconds: int = 300
    insistent_after_seconds: int = 600
    cooldown_seconds: int = 45


@dataclass(slots=True)
class PersonalityConfig:
    name: str = "Companion"
    warmth: int = 60
    sarcasm: int = 55
    strictness: int = 80
    patience: int = 40
    humor: int = 50
    initiative: int = 75


@dataclass(slots=True)
class AppConfig:
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    activity: ActivityConfig = field(default_factory=ActivityConfig)
    accountability: AccountabilityConfig = field(default_factory=AccountabilityConfig)
    personality: PersonalityConfig = field(default_factory=PersonalityConfig)
