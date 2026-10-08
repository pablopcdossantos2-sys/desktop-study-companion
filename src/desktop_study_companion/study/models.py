from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import uuid4


class StudyState(StrEnum):
    IDLE = "idle"
    PLANNED = "planned"
    FOCUSING = "focusing"
    DISTRACTED = "distracted"
    BREAK = "break"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass(slots=True)
class StudySession:
    goal: str
    planned_minutes: int
    id: str = field(default_factory=lambda: str(uuid4()))
    state: StudyState = StudyState.PLANNED
    started_at: datetime | None = None
    ended_at: datetime | None = None
    focused_seconds: int = 0
    distracted_seconds: int = 0

    def start(self) -> None:
        self.started_at = datetime.now().astimezone()
        self.state = StudyState.FOCUSING

    def complete(self) -> None:
        self.ended_at = datetime.now().astimezone()
        self.state = StudyState.COMPLETED

    def abandon(self) -> None:
        self.ended_at = datetime.now().astimezone()
        self.state = StudyState.ABANDONED
