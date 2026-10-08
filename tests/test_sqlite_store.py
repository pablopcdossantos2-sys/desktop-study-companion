import sqlite3

from desktop_study_companion.accountability.models import Intervention, InterventionKind
from desktop_study_companion.activity.models import (
    ActiveWindow,
    ActivityKind,
    ClassifiedActivity,
)
from desktop_study_companion.memory.sqlite_store import SQLiteMemoryStore
from desktop_study_companion.study.models import StudySession


def test_sqlite_store_persists_session_activity_and_intervention(tmp_path) -> None:
    db_path = tmp_path / "companion.db"
    store = SQLiteMemoryStore(db_path)

    session = StudySession(goal="Revisar", planned_minutes=30)
    session.start()
    store.save_session(session)

    activity = ClassifiedActivity(
        window=ActiveWindow("chrome.exe", "YouTube", 12),
        kind=ActivityKind.DISTRACTION,
        reason="matched distraction keyword: youtube",
    )
    store.save_activity(session.id, activity)

    intervention = Intervention(
        InterventionKind.GENTLE_REMINDER,
        1,
        "distraction exceeded gentle threshold",
    )
    store.save_intervention(session.id, intervention, {"message": "Volte."})
    store.close()

    connection = sqlite3.connect(db_path)
    try:
        assert connection.execute("SELECT COUNT(*) FROM study_sessions").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM activity_events").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM interventions").fetchone()[0] == 1
    finally:
        connection.close()
