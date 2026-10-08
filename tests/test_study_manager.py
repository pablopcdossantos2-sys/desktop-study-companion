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
