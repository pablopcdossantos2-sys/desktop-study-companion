import json
from datetime import datetime, timedelta, timezone

import pytest

from desktop_study_companion.accountability.directives import DirectiveManager
from desktop_study_companion.accountability.standing_rules import (
    StandingRule,
    StandingRuleManager,
)
from desktop_study_companion.activity.models import ActiveWindow, ActivityKind
from desktop_study_companion.config.loader import load_config
from desktop_study_companion.config.models import AppConfig
from desktop_study_companion.config.writer import validate_config
from desktop_study_companion.memory.analytics import StudyAnalytics
from desktop_study_companion.memory.exporter import _csv_safe
from desktop_study_companion.memory.sqlite_store import SQLiteMemoryStore
from desktop_study_companion.routines.manager import RoutineManager
from desktop_study_companion.routines.models import Routine
from desktop_study_companion.study.manager import StudySessionManager
from desktop_study_companion.study.models import StudySession, StudyState
from desktop_study_companion.ui.chat_dialog import ChatDialog
from desktop_study_companion.voice.faster_whisper_stt import FasterWhisperSTT


def test_invalid_explicit_config_is_quarantined_and_falls_back(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text('{"monitor":', encoding="utf-8")

    config = load_config(path)

    assert isinstance(config, AppConfig)
    assert not path.exists()
    assert list(tmp_path.glob("config.json.bak*"))


def test_lan_brain_http_without_api_key_is_allowed(monkeypatch) -> None:
    config = AppConfig()
    config.brain.enabled = True
    config.brain.model = "qwen"
    config.brain.base_url = "http://192.168.1.10:11434/v1"
    monkeypatch.delenv(config.brain.api_key_env, raising=False)

    validate_config(config)


def test_lan_brain_http_with_api_key_is_rejected(monkeypatch) -> None:
    config = AppConfig()
    config.brain.enabled = True
    config.brain.model = "qwen"
    config.brain.base_url = "http://192.168.1.10:11434/v1"
    monkeypatch.setenv(config.brain.api_key_env, "secret")

    with pytest.raises(ValueError, match="API key"):
        validate_config(config)


def test_malformed_item_creates_snapshot_before_future_save(tmp_path) -> None:
    path = tmp_path / "directives.json"
    path.write_text(
        json.dumps(
            [
                {"goal": "válido", "urgency": 5},
                {"goal": "inválido", "urgency": "alta"},
            ]
        ),
        encoding="utf-8",
    )

    manager = DirectiveManager(path)

    assert [item.goal for item in manager.directives] == ["válido"]
    backups = list(tmp_path.glob("directives.json.bak*"))
    assert backups
    assert "inválido" in backups[0].read_text(encoding="utf-8")


def test_naive_directive_timestamp_does_not_break_due_check(tmp_path) -> None:
    manager = DirectiveManager(tmp_path / "directives.json")
    directive = manager.add(
        "teste",
        5,
        delay_seconds=0,
        now=datetime(2026, 10, 10, 9, 0, tzinfo=timezone.utc),
    )
    directive.next_nag_at = "2026-10-10T09:00:00"

    due = manager.due(
        datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc)
    )

    assert directive in due


def test_sqlite_session_seconds_are_persisted_as_integer(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    try:
        session = StudySession("Teste", 10)
        session.start()
        session.focused_seconds = 12.3456
        session.distracted_seconds = 1.9
        store.save_session(session)
        row = store.connection.execute(
            """
            SELECT focused_seconds, distracted_seconds,
                   typeof(focused_seconds), typeof(distracted_seconds)
            FROM study_sessions WHERE id = ?
            """,
            (session.id,),
        ).fetchone()
        assert row == (12, 2, "integer", "integer")
    finally:
        store.close()


def test_chat_escape_preserves_line_breaks() -> None:
    escaped = ChatDialog._escape("Linha 1\nLinha 2\n\n- item")
    assert escaped == "Linha 1<br>Linha 2<br><br>- item"


def test_standing_rule_does_not_match_keyword_only_in_word_title(tmp_path) -> None:
    manager = StandingRuleManager(tmp_path / "rules.json")
    manager.add(
        StandingRule(
            description="Evitar YouTube",
            patterns=["youtube"],
        )
    )

    assert manager.check(
        ActiveWindow("winword.exe", "YouTube strategy.docx - Word")
    ) == []


def test_standing_rule_can_explicitly_target_productive_process(tmp_path) -> None:
    manager = StandingRuleManager(tmp_path / "rules.json")
    manager.add(
        StandingRule(
            description="Bloquear Word",
            patterns=["winword.exe"],
        )
    )

    assert manager.check(ActiveWindow("winword.exe", "Documento"))


def test_finish_near_planned_duration_is_completed() -> None:
    manager = StudySessionManager()
    manager.start("Teste", 60)
    manager.tick(ActivityKind.PRODUCTIVE, 59 * 60 + 59)

    assert manager.finish().state == StudyState.COMPLETED


def test_finish_far_before_planned_duration_is_abandoned() -> None:
    manager = StudySessionManager()
    manager.start("Teste", 60)
    manager.tick(ActivityKind.PRODUCTIVE, 30 * 60)

    assert manager.finish().state == StudyState.ABANDONED


def test_old_daily_routine_does_not_fire_hours_late(tmp_path) -> None:
    manager = RoutineManager(tmp_path / "routines.json")
    manager.add(Routine(goal="Café", schedule="daily", time="08:00"))

    assert manager.get_due_routines(
        now=datetime(2026, 10, 10, 15, 0)
    ) == []


def test_daily_routine_has_short_late_grace(tmp_path) -> None:
    manager = RoutineManager(tmp_path / "routines.json")
    manager.add(Routine(goal="Café", schedule="daily", time="08:00"))

    assert manager.get_due_routines(
        now=datetime(2026, 10, 10, 8, 10)
    )


def test_same_routine_description_can_have_two_times(tmp_path) -> None:
    manager = RoutineManager(tmp_path / "routines.json")

    assert manager.add_if_unique(
        Routine(goal="Revisar inglês", schedule="daily", time="08:00")
    )
    assert manager.add_if_unique(
        Routine(goal="Revisar inglês", schedule="daily", time="20:00")
    )
    assert len(manager.routines) == 2


def test_on_wake_only_fires_for_explicit_wake_event(tmp_path) -> None:
    manager = RoutineManager(tmp_path / "routines.json")
    manager.add(Routine(goal="Voltou", schedule="on_wake"))

    assert manager.get_due_routines(
        now=datetime(2026, 10, 10, 8, 0),
        wake_event=False,
    ) == []
    assert manager.get_due_routines(
        now=datetime(2026, 10, 10, 8, 1),
        wake_event=True,
    )


def test_csv_formula_guard_covers_tab_and_carriage_return() -> None:
    assert _csv_safe("\t=1+1").startswith("'\t")
    assert _csv_safe("\r=1+1").startswith("'\r")


def test_active_session_is_excluded_from_completion_analytics(tmp_path) -> None:
    db = tmp_path / "memory.db"
    store = SQLiteMemoryStore(db)
    try:
        completed = StudySession("Concluída", 10)
        completed.start()
        completed.focused_seconds = 600
        completed.complete()
        store.save_session(completed)

        active = StudySession("Ativa", 10)
        active.start()
        active.focused_seconds = 120
        store.save_session(active)
    finally:
        store.close()

    overview = StudyAnalytics(db).overview(30)

    assert overview.session_count == 1
    assert overview.completed_count == 1
    assert overview.completion_rate == 1.0


class _AutoLanguageModel:
    def transcribe(self, _path, **kwargs):
        assert kwargs["language"] is None

        class Segment:
            text = " Olá "

        return [Segment()], object()


def test_stt_auto_language_maps_to_none(tmp_path, monkeypatch) -> None:
    provider = FasterWhisperSTT(language="auto")
    monkeypatch.setattr(provider, "_load_model", lambda: _AutoLanguageModel())
    path = tmp_path / "sample.wav"
    path.write_bytes(b"fake")

    assert provider.transcribe_file(path) == "Olá"
