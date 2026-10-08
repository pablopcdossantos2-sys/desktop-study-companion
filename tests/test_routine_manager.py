from datetime import datetime

from desktop_study_companion.routines.manager import RoutineManager
from desktop_study_companion.routines.models import Routine


def test_daily_routine_fires_once_per_day(tmp_path) -> None:
    manager = RoutineManager(tmp_path / "routines.json")
    manager.add(Routine(goal="Estudar", schedule="daily", time="19:00"))

    first = manager.get_due_routines(now=datetime(2026, 10, 8, 19, 1))
    second = manager.get_due_routines(now=datetime(2026, 10, 8, 20, 0))

    assert [r.goal for r in first] == ["Estudar"]
    assert second == []


def test_weekly_routine_only_fires_on_selected_day(tmp_path) -> None:
    manager = RoutineManager(tmp_path / "routines.json")
    manager.add(
        Routine(
            goal="Revisão semanal",
            schedule="weekly",
            day="thursday",
            time="18:00",
        )
    )

    assert manager.get_due_routines(now=datetime(2026, 10, 7, 19, 0)) == []
    due = manager.get_due_routines(now=datetime(2026, 10, 8, 18, 5))
    assert len(due) == 1


def test_interval_routine_persists_last_fire(tmp_path) -> None:
    path = tmp_path / "routines.json"
    manager = RoutineManager(path)
    manager.add(Routine(goal="Água", schedule="interval", interval_hours=2))

    first = manager.get_due_routines(now=datetime(2026, 10, 8, 10, 0))
    assert len(first) == 1

    reloaded = RoutineManager(path)
    assert reloaded.get_due_routines(now=datetime(2026, 10, 8, 11, 0)) == []
    assert len(reloaded.get_due_routines(now=datetime(2026, 10, 8, 12, 1))) == 1
