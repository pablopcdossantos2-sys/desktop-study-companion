"""Persistent standing rules adapted from bonziPONY's StandingRule concept."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from desktop_study_companion.activity.models import ActiveWindow
from desktop_study_companion.safe_json import atomic_write_json, load_json_list


@dataclass(slots=True)
class StandingRule:
    description: str
    patterns: list[str] = field(default_factory=list)
    response: str = "nag"
    id: str = ""
    catch_count: int = 0
    last_triggered_at: str | None = None
    cooldown_s: float = 30.0
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())[:8]
        self.patterns = [p.strip() for p in self.patterns if isinstance(p, str) and p.strip()]
        self.cooldown_s = max(0.0, float(self.cooldown_s))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StandingRule":
        patterns = data.get("patterns", [])
        if not isinstance(patterns, list):
            raise TypeError("patterns must be a list")
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            patterns=patterns,
            response=data.get("response", "nag"),
            catch_count=data.get("catch_count", 0),
            last_triggered_at=data.get("last_triggered_at"),
            cooldown_s=data.get("cooldown_s", 30.0),
            enabled=data.get("enabled", True),
        )


@dataclass(frozen=True, slots=True)
class RuleViolation:
    rule: StandingRule
    matched_pattern: str
    window: ActiveWindow
    action_due: bool


class StandingRuleManager:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.rules: list[StandingRule] = []
        self.load()

    def load(self) -> None:
        self.rules = load_json_list(self.path, StandingRule.from_dict)

    def save(self) -> None:
        atomic_write_json(self.path, [rule.to_dict() for rule in self.rules])

    def add(self, rule: StandingRule) -> StandingRule:
        if not rule.description.strip():
            raise ValueError("standing rule description cannot be empty")
        if not rule.patterns:
            raise ValueError("standing rule needs at least one pattern")

        normalized = rule.description.casefold().strip()
        for existing in self.rules:
            if existing.description.casefold().strip() == normalized:
                return existing

        self.rules.append(rule)
        self.save()
        return rule

    def remove(self, rule_id: str) -> bool:
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]
        changed = len(self.rules) != before
        if changed:
            self.save()
        return changed

    def toggle(self, rule_id: str) -> bool:
        for rule in self.rules:
            if rule.id == rule_id:
                rule.enabled = not rule.enabled
                self.save()
                return True
        return False

    def check(self, window: ActiveWindow, *, now: datetime | None = None) -> list[RuleViolation]:
        now = now or datetime.now().astimezone()
        haystack = f"{window.process_name} {window.title}".casefold()
        violations: list[RuleViolation] = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            action_due = True
            if rule.last_triggered_at:
                try:
                    last = datetime.fromisoformat(rule.last_triggered_at)
                    action_due = (now - last).total_seconds() >= rule.cooldown_s
                except ValueError:
                    action_due = True

            for pattern in rule.patterns:
                if pattern.casefold() in haystack:
                    violations.append(
                        RuleViolation(
                            rule=rule,
                            matched_pattern=pattern,
                            window=window,
                            action_due=action_due,
                        )
                    )
                    break

        return violations

    def record_trigger(self, rule: StandingRule, *, now: datetime | None = None) -> None:
        now = now or datetime.now().astimezone()
        rule.catch_count += 1
        rule.last_triggered_at = now.isoformat()
        self.save()
