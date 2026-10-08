from __future__ import annotations

"""Session-linked intervention escalation.

Inspired by bonziPONY's enforcement/lockdown progression, but intentionally
more constrained:
- no mouse locking;
- no keyboard interference;
- no workstation locking;
- no persistence across restarts;
- only actions already explicitly allowed by the user.

The limited lockdown here is a temporary focus mode for an active study
session. It only reacts to windows already classified as distractions.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from desktop_study_companion.accountability.models import Intervention
from desktop_study_companion.desktop.interventions import (
    InterventionPermissions,
)


@dataclass(slots=True)
class SessionEscalationPolicy:
    minimize_at_severity: int = 3
    close_at_severity: int = 4

    def response_for(
        self,
        intervention: Intervention,
        permissions: InterventionPermissions,
        *,
        lockdown_active: bool = False,
    ) -> str:
        if not permissions.enabled or not permissions.allow_session_escalation:
            return "nag"

        if lockdown_active:
            if permissions.allow_close:
                return "close_and_nag"
            if permissions.allow_minimize:
                return "minimize_and_nag"
            return "nag"

        if (
            intervention.severity >= self.close_at_severity
            and permissions.allow_close
        ):
            return "close_and_nag"

        if (
            intervention.severity >= self.minimize_at_severity
            and permissions.allow_minimize
        ):
            return "minimize_and_nag"

        return "nag"


@dataclass(slots=True)
class LimitedLockdown:
    active_until: datetime | None = None
    last_action_at: datetime | None = None
    last_target_key: str = ""
    repeat_cooldown_seconds: int = 20

    def activate(
        self,
        minutes: int,
        *,
        now: datetime | None = None,
    ) -> None:
        now = now or datetime.now().astimezone()
        self.active_until = now + timedelta(minutes=max(1, int(minutes)))
        self.last_action_at = None
        self.last_target_key = ""

    def clear(self) -> None:
        self.active_until = None
        self.last_action_at = None
        self.last_target_key = ""

    def is_active(self, *, now: datetime | None = None) -> bool:
        if self.active_until is None:
            return False
        now = now or datetime.now().astimezone()
        if now >= self.active_until:
            self.clear()
            return False
        return True

    def remaining_seconds(self, *, now: datetime | None = None) -> int:
        if not self.is_active(now=now):
            return 0
        now = now or datetime.now().astimezone()
        assert self.active_until is not None
        return max(0, int((self.active_until - now).total_seconds()))

    def should_act(
        self,
        target_key: str,
        *,
        now: datetime | None = None,
    ) -> bool:
        if not self.is_active(now=now):
            return False

        now = now or datetime.now().astimezone()
        if (
            self.last_action_at is not None
            and self.last_target_key == target_key
            and (now - self.last_action_at).total_seconds()
            < self.repeat_cooldown_seconds
        ):
            return False

        self.last_action_at = now
        self.last_target_key = target_key
        return True
