from datetime import datetime, timedelta, timezone

from desktop_study_companion.accountability.standing_rules import (
    StandingRule,
    StandingRuleManager,
)
from desktop_study_companion.activity.models import ActiveWindow


def test_rule_matches_process_or_window_title(tmp_path) -> None:
    manager = StandingRuleManager(tmp_path / "rules.json")
    rule = manager.add(
        StandingRule(
            description="Evitar YouTube",
            patterns=["youtube"],
            cooldown_s=30,
        )
    )

    window = ActiveWindow("msedge.exe", "Vídeo - YouTube")
    violations = manager.check(window)
    assert violations[0].rule.id == rule.id


def test_rule_cooldown_prevents_retrigger(tmp_path) -> None:
    manager = StandingRuleManager(tmp_path / "rules.json")
    rule = manager.add(
        StandingRule(
            description="Evitar Reddit",
            patterns=["reddit"],
            cooldown_s=60,
        )
    )
    window = ActiveWindow("chrome.exe", "Reddit")
    now = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)

    assert manager.check(window, now=now)
    manager.record_trigger(rule, now=now)
    assert manager.check(window, now=now + timedelta(seconds=30)) == []
    assert manager.check(window, now=now + timedelta(seconds=61))


def test_rule_state_persists(tmp_path) -> None:
    path = tmp_path / "rules.json"
    manager = StandingRuleManager(path)
    rule = manager.add(
        StandingRule(description="Sem Netflix", patterns=["netflix"])
    )
    manager.record_trigger(rule)

    reloaded = StandingRuleManager(path)
    assert reloaded.rules[0].catch_count == 1
