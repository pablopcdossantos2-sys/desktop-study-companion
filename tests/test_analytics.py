from datetime import datetime, timedelta

from desktop_study_companion.accountability.models import (
    Intervention,
    InterventionKind,
)
from desktop_study_companion.activity.models import (
    ActiveWindow,
    ActivityKind,
    ClassifiedActivity,
)
from desktop_study_companion.memory.analytics import StudyAnalytics
from desktop_study_companion.memory.sqlite_store import SQLiteMemoryStore
from desktop_study_companion.study.models import StudySession


def _save_session(
    store: SQLiteMemoryStore,
    *,
    goal: str,
    focus: int,
    distracted: int,
    hours_ago: int,
) -> StudySession:
    session = StudySession(goal=goal, planned_minutes=30)
    session.start()
    session.started_at = datetime.now().astimezone() - timedelta(hours=hours_ago)
    session.focused_seconds = focus
    session.distracted_seconds = distracted
    session.complete()
    store.save_session(session)
    return session


def test_analytics_computes_focus_and_common_distraction(tmp_path) -> None:
    db = tmp_path / "companion.db"
    store = SQLiteMemoryStore(db)
    first = _save_session(
        store,
        goal="A",
        focus=1200,
        distracted=300,
        hours_ago=2,
    )
    _save_session(
        store,
        goal="B",
        focus=900,
        distracted=600,
        hours_ago=1,
    )

    activity = ClassifiedActivity(
        ActiveWindow("chrome.exe", "YouTube"),
        ActivityKind.DISTRACTION,
        "test",
    )
    store.save_activity(first.id, activity)
    store.save_activity(first.id, activity)
    store.close()

    overview = StudyAnalytics(db).overview(30)

    assert overview.session_count == 2
    assert overview.completed_count == 2
    assert overview.average_focus_rate == 2100 / 3000
    assert overview.top_distraction_process == "chrome.exe"


def test_analytics_returns_empty_insight_without_history(tmp_path) -> None:
    db = tmp_path / "companion.db"
    store = SQLiteMemoryStore(db)
    store.close()

    overview = StudyAnalytics(db).overview(30)

    assert overview.session_count == 0
    assert overview.insights
