from __future__ import annotations

from dataclasses import dataclass

from desktop_study_companion.activity.models import ActivityKind

from .models import StudySession, StudyState


@dataclass(frozen=True, slots=True)
class StudyTick:
    state: StudyState
    distraction_streak_seconds: float
    elapsed_seconds: float


class StudySessionManager:
    def __init__(self) -> None:
        self.session: StudySession | None = None
        self._elapsed_seconds = 0.0
        self._distraction_streak_seconds = 0.0

    @property
    def active(self) -> bool:
        return self.session is not None and self.session.state not in {
            StudyState.COMPLETED,
            StudyState.ABANDONED,
        }

    @property
    def distraction_streak_seconds(self) -> float:
        return self._distraction_streak_seconds

    def start(self, goal: str, planned_minutes: int) -> StudySession:
        if planned_minutes <= 0:
            raise ValueError("planned_minutes must be greater than zero")
        if self.active:
            raise RuntimeError("a study session is already active")

        self.session = StudySession(goal=goal.strip() or "Estudar", planned_minutes=planned_minutes)
        self.session.start()
        self._elapsed_seconds = 0.0
        self._distraction_streak_seconds = 0.0
        return self.session

    def tick(self, kind: ActivityKind, seconds: float) -> StudyTick | None:
        if not self.active or self.session is None:
            return None

        seconds = max(0.0, seconds)
        self._elapsed_seconds += seconds

        if kind == ActivityKind.DISTRACTION:
            self.session.state = StudyState.DISTRACTED
            self.session.distracted_seconds += int(round(seconds))
            self._distraction_streak_seconds += seconds
        else:
            if self.session.state != StudyState.BREAK:
                self.session.state = StudyState.FOCUSING
            if kind == ActivityKind.PRODUCTIVE:
                self.session.focused_seconds += int(round(seconds))
            self._distraction_streak_seconds = 0.0

        if self._elapsed_seconds >= self.session.planned_minutes * 60:
            self.session.complete()

        return StudyTick(
            state=self.session.state,
            distraction_streak_seconds=self._distraction_streak_seconds,
            elapsed_seconds=self._elapsed_seconds,
        )

    def finish(self) -> StudySession:
        if self.session is None:
            raise RuntimeError("there is no session to finish")
        if self.active:
            self.session.complete()
        return self.session

    def abandon(self) -> StudySession:
        if self.session is None:
            raise RuntimeError("there is no session to abandon")
        if self.active:
            self.session.abandon()
        return self.session
