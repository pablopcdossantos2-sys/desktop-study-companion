"""Persistent routine scheduler adapted from bonziPONY core/routines.py."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from desktop_study_companion.safe_json import atomic_write_json, load_json_list

from .models import Routine


_WEEKDAYS = {
    0: {"monday", "segunda", "segunda-feira"},
    1: {"tuesday", "terça", "terca", "terça-feira", "terca-feira"},
    2: {"wednesday", "quarta", "quarta-feira"},
    3: {"thursday", "quinta", "quinta-feira"},
    4: {"friday", "sexta", "sexta-feira"},
    5: {"saturday", "sábado", "sabado"},
    6: {"sunday", "domingo"},
}


class RoutineManager:
    SCHEDULE_GRACE_MINUTES = 15

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.routines: list[Routine] = []
        self.load()

    def load(self) -> None:
        self.routines = load_json_list(self.path, Routine.from_dict)

    def save(self) -> None:
        atomic_write_json(
            self.path,
            [routine.to_dict() for routine in self.routines],
        )

    def add(self, routine: Routine) -> Routine:
        self.routines.append(routine)
        self.save()
        return routine

    @staticmethod
    def _identity(routine: Routine) -> tuple:
        return (
            routine.goal.casefold().strip(),
            routine.schedule,
            (routine.time or "").strip(),
            (routine.day or "").casefold().strip(),
            round(float(routine.interval_hours or 0.0), 6),
        )

    def add_if_unique(self, routine: Routine) -> bool:
        identity = self._identity(routine)
        for existing in self.routines:
            if self._identity(existing) == identity:
                return False
        self.add(routine)
        return True

    def remove(self, routine_id: str) -> bool:
        before = len(self.routines)
        self.routines = [r for r in self.routines if r.id != routine_id]
        changed = len(self.routines) != before
        if changed:
            self.save()
        return changed

    def toggle(self, routine_id: str) -> bool:
        for routine in self.routines:
            if routine.id == routine_id:
                routine.enabled = not routine.enabled
                self.save()
                return True
        return False

    def _time_is_due(self, value: str | None, now: datetime) -> bool:
        if not value:
            return False
        try:
            hour_text, minute_text = value.split(":", 1)
            scheduled = now.replace(
                hour=int(hour_text),
                minute=int(minute_text),
                second=0,
                microsecond=0,
            )
        except (TypeError, ValueError):
            return False

        lateness = (now - scheduled).total_seconds()
        return 0 <= lateness <= self.SCHEDULE_GRACE_MINUTES * 60

    @staticmethod
    def _day_matches(day: str | None, now: datetime) -> bool:
        if not day:
            return False
        normalized = day.casefold().strip()
        return normalized in _WEEKDAYS.get(now.weekday(), set())

    def get_due_routines(
        self,
        *,
        now: datetime | None = None,
        wake_event: bool = False,
    ) -> list[Routine]:
        now = now or datetime.now().astimezone()
        today = now.strftime("%Y-%m-%d")
        due: list[Routine] = []

        for routine in self.routines:
            if not routine.enabled:
                continue

            fired = False
            if routine.schedule == "on_wake":
                fired = wake_event and routine.last_fired_date != today
            elif routine.schedule == "daily":
                fired = (
                    routine.last_fired_date != today
                    and self._time_is_due(routine.time, now)
                )
            elif routine.schedule == "weekly":
                fired = (
                    routine.last_fired_date != today
                    and self._day_matches(routine.day, now)
                    and self._time_is_due(routine.time, now)
                )
            elif routine.schedule == "interval" and routine.interval_hours:
                if not routine.last_fired_ts:
                    fired = True
                else:
                    try:
                        last = datetime.fromisoformat(routine.last_fired_ts)
                        compare_now = now
                        if last.tzinfo is None and compare_now.tzinfo is not None:
                            last = last.astimezone()
                        elif last.tzinfo is not None and compare_now.tzinfo is None:
                            compare_now = compare_now.astimezone()
                        fired = (
                            compare_now - last
                        ).total_seconds() / 3600 >= routine.interval_hours
                    except (TypeError, ValueError):
                        fired = True

            if fired:
                routine.last_fired_date = today
                routine.last_fired_ts = now.isoformat()
                due.append(routine)

        if due:
            self.save()
        return due

    def describe(self, routine: Routine) -> str:
        if routine.schedule == "daily":
            return f"Todos os dias às {routine.time or '?'}"
        if routine.schedule == "weekly":
            return f"{(routine.day or '?').title()} às {routine.time or '?'}"
        if routine.schedule == "interval":
            return f"A cada {routine.interval_hours:g} h"
        if routine.schedule == "on_wake":
            return "Ao voltar após um longo período ausente"
        return routine.schedule
