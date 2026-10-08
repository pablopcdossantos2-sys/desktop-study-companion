from __future__ import annotations

from typing import Protocol

from desktop_study_companion.study.models import StudySession


class MemoryStore(Protocol):
    def save_session(self, session: StudySession) -> None: ...

    def close(self) -> None: ...
