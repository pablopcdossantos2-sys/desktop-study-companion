from dataclasses import dataclass
from enum import StrEnum


class InterventionKind(StrEnum):
    NONE = "none"
    GENTLE_REMINDER = "gentle_reminder"
    FIRM_REMINDER = "firm_reminder"
    DIRECT_CHALLENGE = "direct_challenge"
    INSISTENT_CHALLENGE = "insistent_challenge"
    VISUAL_ALERT = "visual_alert"
    MINIMIZE_DISTRACTION = "minimize_distraction"
    CLOSE_DISTRACTION = "close_distraction"


@dataclass(frozen=True, slots=True)
class Intervention:
    kind: InterventionKind
    severity: int
    reason: str
