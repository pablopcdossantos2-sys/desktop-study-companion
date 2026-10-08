from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from desktop_study_companion.accountability.models import Intervention
from desktop_study_companion.activity.models import ClassifiedActivity
from desktop_study_companion.study.models import StudySession


class SQLiteMemoryStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self._migrate()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS study_sessions (
                id TEXT PRIMARY KEY,
                goal TEXT NOT NULL,
                planned_minutes INTEGER NOT NULL,
                state TEXT NOT NULL,
                started_at TEXT,
                ended_at TEXT,
                focused_seconds INTEGER NOT NULL,
                distracted_seconds INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS activity_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                process_name TEXT NOT NULL,
                window_title TEXT NOT NULL,
                kind TEXT NOT NULL,
                reason TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS interventions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                kind TEXT NOT NULL,
                severity INTEGER NOT NULL,
                reason TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}'
            );
            """
        )
        self.connection.commit()

    def save_session(self, session: StudySession) -> None:
        self.connection.execute(
            """
            INSERT INTO study_sessions (
                id, goal, planned_minutes, state, started_at, ended_at,
                focused_seconds, distracted_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                goal=excluded.goal,
                planned_minutes=excluded.planned_minutes,
                state=excluded.state,
                started_at=excluded.started_at,
                ended_at=excluded.ended_at,
                focused_seconds=excluded.focused_seconds,
                distracted_seconds=excluded.distracted_seconds
            """,
            (
                session.id,
                session.goal,
                session.planned_minutes,
                session.state.value,
                session.started_at.isoformat() if session.started_at else None,
                session.ended_at.isoformat() if session.ended_at else None,
                session.focused_seconds,
                session.distracted_seconds,
            ),
        )
        self.connection.commit()

    def save_activity(self, session_id: str | None, activity: ClassifiedActivity) -> None:
        self.connection.execute(
            """
            INSERT INTO activity_events (
                session_id, process_name, window_title, kind, reason
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                activity.window.process_name,
                activity.window.title,
                activity.kind.value,
                activity.reason,
            ),
        )
        self.connection.commit()

    def save_intervention(
        self,
        session_id: str | None,
        intervention: Intervention,
        payload: dict | None = None,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO interventions (
                session_id, kind, severity, reason, payload_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                intervention.kind.value,
                intervention.severity,
                intervention.reason,
                json.dumps(payload or {}, ensure_ascii=False),
            ),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
