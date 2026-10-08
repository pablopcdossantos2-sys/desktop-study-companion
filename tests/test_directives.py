from datetime import datetime, timedelta, timezone

from desktop_study_companion.accountability.directives import DirectiveManager
from desktop_study_companion.accountability.nagging import NaggingPolicy


def test_directive_persists_and_becomes_due(tmp_path) -> None:
    now = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    path = tmp_path / "directives.json"
    manager = DirectiveManager(path)
    directive = manager.add("Estudar", 8, delay_seconds=60, now=now)

    assert manager.due(now=now + timedelta(seconds=59)) == []
    assert manager.due(now=now + timedelta(seconds=60))[0].id == directive.id

    reloaded = DirectiveManager(path)
    assert reloaded.active[0].goal == "Estudar"


def test_record_nag_persists_history_and_schedules_next(tmp_path) -> None:
    now = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    manager = DirectiveManager(tmp_path / "directives.json", NaggingPolicy())
    directive = manager.add("Revisar", 6, delay_seconds=0, now=now)

    decision = manager.policy.decide(directive.urgency, directive.nag_count)
    manager.record_nag(directive, "Volte.", now=now)

    assert directive.nag_count == 1
    assert directive.last_nag_text == "Volte."
    assert directive.last_nag_style == decision.style
    assert datetime.fromisoformat(directive.next_nag_at) > now


def test_complete_stops_future_nags(tmp_path) -> None:
    now = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    manager = DirectiveManager(tmp_path / "directives.json")
    directive = manager.add("Ler", 5, delay_seconds=0, now=now)

    assert manager.complete(directive.id, now=now)
    assert manager.due(now=now + timedelta(hours=1)) == []


def test_directive_can_be_snoozed_only_once(tmp_path) -> None:
    now = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    manager = DirectiveManager(tmp_path / "directives.json")
    directive = manager.add("Estudar", 7, delay_seconds=0, now=now)

    assert manager.snooze(directive.id, minutes=5, now=now)
    assert directive.delayed is True
    assert manager.due(now=now + timedelta(minutes=4)) == []
    assert manager.snooze(directive.id, minutes=5, now=now) is False
