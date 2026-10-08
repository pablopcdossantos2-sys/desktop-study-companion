from dataclasses import dataclass
from enum import StrEnum


class ActivityKind(StrEnum):
    PRODUCTIVE = "productive"
    NEUTRAL = "neutral"
    DISTRACTION = "distraction"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ActiveWindow:
    process_name: str
    title: str
    duration_seconds: float = 0.0
    hwnd: int = 0


@dataclass(frozen=True, slots=True)
class ClassifiedActivity:
    window: ActiveWindow
    kind: ActivityKind
    reason: str
