"""Persistent directives adapted from bonziPONY's AgentLoop directive model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from desktop_study_companion.safe_json import atomic_write_json, load_json_list

from .nagging import NagDecision, NaggingPolicy


@dataclass(slots=True)
class Directive:
    goal: str
    urgency: int
    id: str = ""
    source: str = "user"
    created_at: str = ""
    next_nag_at: str = ""
    delayed: bool = False
    nag_count: int = 0
    last_nag_style: str = ""
    last_nag_text: str = ""
    active: bool = True
    completed_at: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())[:8]
        self.urgency = max(1, min(10, int(self.urgency)))
        if not self.created_at:
            self.created_at = datetime.now().astimezone().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Directive":
        return cls(
            id=data.get("id", ""),
            goal=data.get("goal", ""),
            urgency=data.get("urgency", 5),
            source=data.get("source", "user"),
            created_at=data.get("created_at", ""),
            next_nag_at=data.get("next_nag_at", ""),
            delayed=data.get("delayed", False),
            nag_count=data.get("nag_count", 0),
            last_nag_style=data.get("last_nag_style", ""),
            last_nag_text=data.get("last_nag_text", ""),
            active=data.get("active", True),
            completed_at=data.get("completed_at"),
        )


class DirectiveManager:
    def __init__(self, path: str | Path, policy: NaggingPolicy | None = None) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.policy = policy or NaggingPolicy()
        self.directives: list[Directive] = []
        self.load()

    def load(self) -> None:
        self.directives = load_json_list(self.path, Directive.from_dict)

    def save(self) -> None:
        atomic_write_json(
            self.path,
            [directive.to_dict() for directive in self.directives],
        )

    @property
    def active(self) -> list[Directive]:
        return [d for d in self.directives if d.active]

    def add(
        self,
        goal: str,
        urgency: int,
        *,
        source: str = "user",
        delay_seconds: int | None = None,
        now: datetime | None = None,
    ) -> Directive:
        goal = goal.strip()
        if not goal:
            raise ValueError("directive goal cannot be empty")

        normalized = goal.casefold()
        for existing in self.active:
            if existing.goal.casefold().strip() == normalized:
                if urgency > existing.urgency:
                    existing.urgency = max(1, min(10, int(urgency)))
                    self.save()
                return existing

        now = now or datetime.now().astimezone()
        if delay_seconds is None:
            delay_seconds = self.policy.initial_delay_seconds(urgency)

        directive = Directive(
            goal=goal,
            urgency=urgency,
            source=source,
            created_at=now.isoformat(),
            next_nag_at=(now + timedelta(seconds=max(0, delay_seconds))).isoformat(),
            delayed=False,
        )
        self.directives.append(directive)
        self.save()
        return directive

    def due(self, now: datetime | None = None) -> list[Directive]:
        now = now or datetime.now().astimezone()
        result: list[Directive] = []
        for directive in self.active:
            if not directive.next_nag_at:
                result.append(directive)
                continue
            try:
                next_at = datetime.fromisoformat(directive.next_nag_at)
            except ValueError:
                result.append(directive)
                continue
            if next_at <= now:
                result.append(directive)
        return result

    def record_nag(
        self,
        directive: Directive,
        text: str,
        *,
        now: datetime | None = None,
    ) -> NagDecision:
        now = now or datetime.now().astimezone()
        decision = self.policy.decide(directive.urgency, directive.nag_count)
        directive.nag_count += 1
        directive.last_nag_style = decision.style
        directive.last_nag_text = text
        directive.next_nag_at = (
            now + timedelta(seconds=decision.delay_seconds)
        ).isoformat()
        self.save()
        return decision

    def snooze(
        self,
        directive_id: str,
        *,
        minutes: int = 5,
        now: datetime | None = None,
    ) -> bool:
        """Allow exactly one negotiated delay for each directive."""
        now = now or datetime.now().astimezone()
        for directive in self.directives:
            if directive.id != directive_id or not directive.active:
                continue
            if directive.delayed:
                return False
            directive.delayed = True
            directive.next_nag_at = (
                now + timedelta(minutes=max(1, int(minutes)))
            ).isoformat()
            self.save()
            return True
        return False

    def complete(self, directive_id: str, now: datetime | None = None) -> bool:
        now = now or datetime.now().astimezone()
        for directive in self.directives:
            if directive.id == directive_id and directive.active:
                directive.active = False
                directive.completed_at = now.isoformat()
                self.save()
                return True
        return False

    def remove(self, directive_id: str) -> bool:
        before = len(self.directives)
        self.directives = [d for d in self.directives if d.id != directive_id]
        changed = len(self.directives) != before
        if changed:
            self.save()
        return changed
