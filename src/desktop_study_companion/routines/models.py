from __future__ import annotations

"""Routine data structures adapted from bonziPONY core/routines.py.

Upstream: https://github.com/maresmaremares/bonziPONY/blob/master/core/routines.py
Adapted with permission; see THIRD-PARTY-NOTICES.md.
"""

from dataclasses import asdict, dataclass
from typing import Literal
from uuid import uuid4


RoutineSchedule = Literal["daily", "weekly", "interval", "on_wake"]


@dataclass(slots=True)
class Routine:
    goal: str
    schedule: RoutineSchedule
    urgency: int = 5
    id: str = ""
    time: str | None = None
    day: str | None = None
    interval_hours: float | None = None
    enabled: bool = True
    last_fired_date: str | None = None
    last_fired_ts: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())[:8]
        self.urgency = max(1, min(10, int(self.urgency)))
        if self.day:
            self.day = self.day.casefold()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Routine":
        return cls(
            id=data.get("id", ""),
            goal=data.get("goal", ""),
            urgency=data.get("urgency", 5),
            schedule=data.get("schedule", "daily"),
            time=data.get("time"),
            day=data.get("day"),
            interval_hours=data.get("interval_hours"),
            enabled=data.get("enabled", True),
            last_fired_date=data.get("last_fired_date"),
            last_fired_ts=data.get("last_fired_ts"),
        )
