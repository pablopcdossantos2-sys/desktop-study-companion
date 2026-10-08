from datetime import datetime, timedelta, timezone

from desktop_study_companion.accountability.escalation import (
    LimitedLockdown,
    SessionEscalationPolicy,
)
from desktop_study_companion.accountability.models import (
    Intervention,
    InterventionKind,
)
from desktop_study_companion.desktop.interventions import (
    InterventionPermissions,
)


def _intervention(severity: int) -> Intervention:
    return Intervention(
        InterventionKind.DIRECT_CHALLENGE,
        severity,
        "test",
    )


def test_session_escalation_is_off_by_default() -> None:
    permissions = InterventionPermissions(
        enabled=True,
        allow_minimize=True,
        allow_close=True,
    )
    policy = SessionEscalationPolicy()

    assert policy.response_for(_intervention(4), permissions) == "nag"


def test_severity_three_can_minimize_when_explicitly_enabled() -> None:
    permissions = InterventionPermissions(
        enabled=True,
        allow_minimize=True,
        allow_session_escalation=True,
    )
    policy = SessionEscalationPolicy()

    assert (
        policy.response_for(_intervention(3), permissions)
        == "minimize_and_nag"
    )


def test_severity_four_can_close_when_explicitly_enabled() -> None:
    permissions = InterventionPermissions(
        enabled=True,
        allow_minimize=True,
        allow_close=True,
        allow_session_escalation=True,
    )
    policy = SessionEscalationPolicy()

    assert policy.response_for(_intervention(4), permissions) == "close_and_nag"


def test_lockdown_uses_strongest_permitted_action() -> None:
    policy = SessionEscalationPolicy()
    permissions = InterventionPermissions(
        enabled=True,
        allow_minimize=True,
        allow_session_escalation=True,
    )

    assert (
        policy.response_for(
            _intervention(1),
            permissions,
            lockdown_active=True,
        )
        == "minimize_and_nag"
    )


def test_limited_lockdown_expires_automatically() -> None:
    lockdown = LimitedLockdown()
    now = datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc)

    lockdown.activate(5, now=now)

    assert lockdown.is_active(now=now + timedelta(minutes=4))
    assert not lockdown.is_active(now=now + timedelta(minutes=5))


def test_lockdown_repeated_target_has_cooldown() -> None:
    lockdown = LimitedLockdown(repeat_cooldown_seconds=20)
    now = datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc)
    lockdown.activate(5, now=now)

    assert lockdown.should_act("chrome|youtube", now=now)
    assert not lockdown.should_act(
        "chrome|youtube",
        now=now + timedelta(seconds=10),
    )
    assert lockdown.should_act(
        "chrome|youtube",
        now=now + timedelta(seconds=21),
    )
    assert lockdown.should_act(
        "chrome|reddit",
        now=now + timedelta(seconds=5),
    )
