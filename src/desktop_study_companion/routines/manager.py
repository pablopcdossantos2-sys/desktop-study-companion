"""Persistent routine scheduler adapted from bonziPONY core/routines.py."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from desktop_study_companion.safe_json import atomic_write_json, load_json_list

from .models import Routine


class RoutineManager:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.routines: list[Routine] = []
        self.load()

    def load(self) -> None:
        self.routines = load_json_list(self.path, Routine.from_dict)

    def save(self) -> None:
        atomic_write_json(self.path, [routine.to_dict() for routine in self.routines])

    def add(self, routine: Routine) -> Routine:
        self.routines.append(routine)
        self.save()
        return routine

    def add_if_unique(self, routine: Routine) -> bool:
        normalized = routine.goal.casefold().strip()
        for existing in self.routines:
            if existing.goal.casefold().strip() == normalized:
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

    def get_due_routines(
        self,
        *,
        now: datetime | None = None,
        wake_event: bool = False,
    ) -> list[Routine]:
        now = now or datetime.now()
        today = now.strftime("%Y-%m-%d")
        now_hhmm = now.strftime("%H:%M")
        now_day = now.strftime("%A").casefold()
        due: list[Routine] = []

        for routine in self.routines:
            if not routine.enabled:
                continue

            fired = False
            if routine.schedule == "on_wake":
                fired = wake_event and routine.last_fired_date != today
            elif routine.schedule == "daily":
                fired = bool(
                    routine.time
                    and routine.time <= now_hhmm
                    and routine.last_fired_date != today
                )
            elif routine.schedule == "weekly":
                fired = bool(
                    routine.day
                    and routine.day.casefold() == now_day
                    and routine.time
                    and routine.time <= now_hhmm
                    and routine.last_fired_date != today
                )
            elif routine.schedule == "interval" and routine.interval_hours:
                if not routine.last_fired_ts:
                    fired = True
                else:
                    try:
                        last = datetime.fromisoformat(routine.last_fired_ts)
                        fired = (now - last).total_seconds() / 3600 >= routine.interval_hours
                    except ValueError:
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
