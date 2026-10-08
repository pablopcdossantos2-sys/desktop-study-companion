from __future__ import annotations

"""Local behavioral analytics derived from the companion's SQLite history.

No cloud service or LLM is required. The goal is to turn raw study history
into stable facts the companion can later use as context.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SessionRecord:
    id: str
    goal: str
    planned_minutes: int
    state: str
    started_at: str | None
    ended_at: str | None
    focused_seconds: int
    distracted_seconds: int

    @property
    def accounted_seconds(self) -> int:
        return self.focused_seconds + self.distracted_seconds

    @property
    def focus_rate(self) -> float:
        total = self.accounted_seconds
        return self.focused_seconds / total if total > 0 else 0.0


@dataclass(frozen=True, slots=True)
class BehavioralOverview:
    session_count: int
    completed_count: int
    abandoned_count: int
    total_focused_seconds: int
    total_distracted_seconds: int
    average_focus_rate: float
    completion_rate: float
    intervention_count: int
    return_after_intervention_rate: float | None
    top_distraction_process: str | None
    top_intervention_kind: str | None
    best_focus_hour: int | None
    recent_trend: str
    insights: tuple[str, ...]


class StudyAnalytics:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def sessions(self, limit: int = 50) -> list[SessionRecord]:
        if not self.db_path.exists():
            return []

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id, goal, planned_minutes, state, started_at, ended_at,
                    focused_seconds, distracted_seconds
                FROM study_sessions
                ORDER BY COALESCE(started_at, ended_at, '') DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()

        return [
            SessionRecord(
                id=row["id"],
                goal=row["goal"],
                planned_minutes=row["planned_minutes"],
                state=row["state"],
                started_at=row["started_at"],
                ended_at=row["ended_at"],
                focused_seconds=row["focused_seconds"],
                distracted_seconds=row["distracted_seconds"],
            )
            for row in rows
        ]

    def overview(self, days: int = 30) -> BehavioralOverview:
        sessions = self._sessions_since(days)
        completed = sum(1 for s in sessions if s.state == "completed")
        abandoned = sum(1 for s in sessions if s.state == "abandoned")
        focused = sum(s.focused_seconds for s in sessions)
        distracted = sum(s.distracted_seconds for s in sessions)
        accounted = focused + distracted
        average_focus_rate = focused / accounted if accounted else 0.0
        completion_rate = completed / len(sessions) if sessions else 0.0

        intervention_count, top_intervention = self._intervention_stats(days)
        top_distraction = self._top_distraction_process(days)
        return_rate = self._return_after_intervention_rate(days)
        best_hour = self._best_focus_hour(sessions)
        recent_trend = self._recent_trend(sessions)

        insights = self._build_insights(
            sessions=sessions,
            average_focus_rate=average_focus_rate,
            completion_rate=completion_rate,
            top_distraction=top_distraction,
            return_rate=return_rate,
            best_hour=best_hour,
            recent_trend=recent_trend,
        )

        return BehavioralOverview(
            session_count=len(sessions),
            completed_count=completed,
            abandoned_count=abandoned,
            total_focused_seconds=focused,
            total_distracted_seconds=distracted,
            average_focus_rate=average_focus_rate,
            completion_rate=completion_rate,
            intervention_count=intervention_count,
            return_after_intervention_rate=return_rate,
            top_distraction_process=top_distraction,
            top_intervention_kind=top_intervention,
            best_focus_hour=best_hour,
            recent_trend=recent_trend,
            insights=tuple(insights),
        )

    def _sessions_since(self, days: int) -> list[SessionRecord]:
        all_sessions = self.sessions(limit=1000)
        cutoff = datetime.now().astimezone() - timedelta(days=max(1, days))
        result: list[SessionRecord] = []

        for session in all_sessions:
            if not session.started_at:
                continue
            try:
                started = datetime.fromisoformat(session.started_at)
                if started.tzinfo is None:
                    started = started.astimezone()
            except ValueError:
                continue
            if started >= cutoff:
                result.append(session)

        return result

    def _cutoff_sql(self, days: int) -> str:
        days = max(1, int(days))
        return f"-{days} days"

    def _intervention_stats(self, days: int) -> tuple[int, str | None]:
        if not self.db_path.exists():
            return 0, None

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT kind, COUNT(*) AS n
                FROM interventions
                WHERE datetime(created_at) >= datetime('now', ?)
                GROUP BY kind
                ORDER BY n DESC, kind ASC
                """,
                (self._cutoff_sql(days),),
            ).fetchall()

        if not rows:
            return 0, None
        total = sum(int(row["n"]) for row in rows)
        return total, str(rows[0]["kind"])

    def _top_distraction_process(self, days: int) -> str | None:
        if not self.db_path.exists():
            return None

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT process_name, COUNT(*) AS n
                FROM activity_events
                WHERE kind = 'distraction'
                  AND datetime(captured_at) >= datetime('now', ?)
                GROUP BY process_name
                ORDER BY n DESC, process_name ASC
                LIMIT 1
                """,
                (self._cutoff_sql(days),),
            ).fetchone()

        return str(row["process_name"]) if row else None

    def _return_after_intervention_rate(self, days: int) -> float | None:
        """Estimate whether interventions are followed by productive activity.

        We count an intervention as successful when the same session records a
        productive activity event within five minutes after the intervention.
        """
        if not self.db_path.exists():
            return None

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, created_at
                FROM interventions
                WHERE session_id IS NOT NULL
                  AND datetime(created_at) >= datetime('now', ?)
                """,
                (self._cutoff_sql(days),),
            ).fetchall()

            if not rows:
                return None

            successes = 0
            for row in rows:
                found = connection.execute(
                    """
                    SELECT 1
                    FROM activity_events
                    WHERE session_id = ?
                      AND kind = 'productive'
                      AND datetime(captured_at) > datetime(?)
                      AND datetime(captured_at) <= datetime(?, '+5 minutes')
                    LIMIT 1
                    """,
                    (row["session_id"], row["created_at"], row["created_at"]),
                ).fetchone()
                if found:
                    successes += 1

        return successes / len(rows)

    def _best_focus_hour(self, sessions: list[SessionRecord]) -> int | None:
        buckets: dict[int, list[float]] = {}
        for session in sessions:
            if not session.started_at or session.accounted_seconds <= 0:
                continue
            try:
                hour = datetime.fromisoformat(session.started_at).hour
            except ValueError:
                continue
            buckets.setdefault(hour, []).append(session.focus_rate)

        eligible = {
            hour: rates
            for hour, rates in buckets.items()
            if len(rates) >= 2
        }
        if not eligible:
            return None

        return max(
            eligible,
            key=lambda hour: sum(eligible[hour]) / len(eligible[hour]),
        )

    def _recent_trend(self, sessions: list[SessionRecord]) -> str:
        usable = [s for s in sessions if s.accounted_seconds > 0]
        if len(usable) < 6:
            return "insufficient_data"

        # sessions() is newest first.
        recent = usable[:3]
        previous = usable[3:6]
        recent_rate = sum(s.focus_rate for s in recent) / len(recent)
        previous_rate = sum(s.focus_rate for s in previous) / len(previous)
        delta = recent_rate - previous_rate

        if delta >= 0.08:
            return "improving"
        if delta <= -0.08:
            return "declining"
        return "stable"

    def _build_insights(
        self,
        *,
        sessions: list[SessionRecord],
        average_focus_rate: float,
        completion_rate: float,
        top_distraction: str | None,
        return_rate: float | None,
        best_hour: int | None,
        recent_trend: str,
    ) -> list[str]:
        if not sessions:
            return ["Ainda não há sessões suficientes para formar um padrão."]

        insights = [
            (
                f"Nos últimos registros, {average_focus_rate:.0%} do tempo "
                "classificado foi produtivo."
            ),
            f"Taxa de conclusão das sessões: {completion_rate:.0%}.",
        ]

        if top_distraction:
            insights.append(
                f"O processo mais recorrente entre as distrações foi "
                f"{top_distraction}."
            )

        if return_rate is not None:
            insights.append(
                f"Após uma intervenção, houve retorno a atividade produtiva "
                f"em até cinco minutos em {return_rate:.0%} dos casos."
            )

        if best_hour is not None:
            insights.append(
                f"As sessões iniciadas por volta das {best_hour:02d}:00 "
                "tiveram a melhor taxa média de foco entre horários com "
                "pelo menos duas sessões."
            )

        if recent_trend == "improving":
            insights.append(
                "As três sessões mais recentes mostram melhora de foco em "
                "relação às três anteriores."
            )
        elif recent_trend == "declining":
            insights.append(
                "As três sessões mais recentes mostram queda de foco em "
                "relação às três anteriores."
            )

        return insights

    def to_context_dict(self, days: int = 30) -> dict:
        """Structured future context for a local/remote LLM."""
        overview = self.overview(days)
        return {
            "period_days": days,
            "session_count": overview.session_count,
            "completion_rate": overview.completion_rate,
            "average_focus_rate": overview.average_focus_rate,
            "top_distraction_process": overview.top_distraction_process,
            "return_after_intervention_rate": (
                overview.return_after_intervention_rate
            ),
            "best_focus_hour": overview.best_focus_hour,
            "recent_trend": overview.recent_trend,
            "insights": list(overview.insights),
        }

    def context_json(self, days: int = 30) -> str:
        return json.dumps(
            self.to_context_dict(days),
            ensure_ascii=False,
            indent=2,
        )
