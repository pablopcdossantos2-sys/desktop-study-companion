from __future__ import annotations

from dataclasses import dataclass

from .models import Intervention, InterventionKind


@dataclass(slots=True)
class AccountabilityPolicy:
    gentle_after_seconds: int = 60
    firm_after_seconds: int = 180
    direct_after_seconds: int = 300
    insistent_after_seconds: int = 600


class AccountabilityEngine:
    def __init__(self, policy: AccountabilityPolicy | None = None) -> None:
        self.policy = policy or AccountabilityPolicy()

    def evaluate_distraction(self, duration_seconds: float) -> Intervention:
        p = self.policy

        if duration_seconds >= p.insistent_after_seconds:
            return Intervention(
                InterventionKind.INSISTENT_CHALLENGE,
                4,
                "distraction exceeded insistent threshold",
            )
        if duration_seconds >= p.direct_after_seconds:
            return Intervention(
                InterventionKind.DIRECT_CHALLENGE,
                3,
                "distraction exceeded direct threshold",
            )
        if duration_seconds >= p.firm_after_seconds:
            return Intervention(
                InterventionKind.FIRM_REMINDER,
                2,
                "distraction exceeded firm threshold",
            )
        if duration_seconds >= p.gentle_after_seconds:
            return Intervention(
                InterventionKind.GENTLE_REMINDER,
                1,
                "distraction exceeded gentle threshold",
            )

        return Intervention(InterventionKind.NONE, 0, "below intervention threshold")
