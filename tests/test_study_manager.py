import pytest

from desktop_study_companion.activity.models import ActivityKind
from desktop_study_companion.study.manager import StudySessionManager
from desktop_study_companion.study.models import StudyState


def test_distraction_and_return_to_focus() -> None:
    manager = StudySessionManager()
    manager.start("Teste", 30)
    manager.tick(ActivityKind.DISTRACTION, 10)
    assert manager.session is not None
    assert manager.session.state == StudyState.DISTRACTED
    assert manager.distraction_streak_seconds == 10
    manager.tick(ActivityKind.PRODUCTIVE, 2)
    assert manager.session.state == StudyState.FOCUSING
    assert manager.distraction_streak_seconds == 0


def test_auto_complete_after_planned_duration() -> None:
    manager = StudySessionManager()
    manager.start("Teste", 1)
    manager.tick(ActivityKind.PRODUCTIVE, 60)
    assert manager.session is not None
    assert manager.session.state == StudyState.COMPLETED


def test_fractional_ticks_are_accumulated_without_rounding_loss() -> None:
    manager = StudySessionManager()
    manager.start("Teste", 30)
    for _ in range(25):
        manager.tick(ActivityKind.PRODUCTIVE, 0.4)
    assert manager.session is not None
    assert manager.session.focused_seconds == pytest.approx(10.0)


def test_manual_finish_before_planned_duration_is_abandoned() -> None:
    manager = StudySessionManager()
    manager.start("Teste", 60)
    manager.tick(ActivityKind.PRODUCTIVE, 5)
    session = manager.finish()
    assert session.state == StudyState.ABANDONED


def test_brief_unknown_window_does_not_reset_distraction_streak() -> None:
    manager = StudySessionManager()
    manager.start("Teste", 30)
    manager.tick(ActivityKind.DISTRACTION, 5)
    manager.tick(ActivityKind.UNKNOWN, 1)
    assert manager.distraction_streak_seconds == 5
    manager.tick(ActivityKind.UNKNOWN, 3)
    assert manager.distraction_streak_seconds == 0
