from __future__ import annotations

"""Persistent standing rules adapted from bonziPONY's StandingRule concept.

bonziPONY uses permanent rules with generated detection patterns, response
modes, a catch counter, last-trigger time and cooldown. This implementation
keeps the same useful state model but matches process/window metadata locally.

Upstream reference:
https://github.com/maresmaremares/bonziPONY/blob/master/core/agent_loop.py
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from desktop_study_companion.activity.models import ActiveWindow


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
        self.patterns = [p.strip() for p in self.patterns if p.strip()]
        self.cooldown_s = max(0.0, float(self.cooldown_s))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StandingRule":
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            patterns=list(data.get("patterns", [])),
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


class StandingRuleManager:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.rules: list[StandingRule] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.rules = []
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.rules = [StandingRule.from_dict(item) for item in raw]
        except (OSError, json.JSONDecodeError, TypeError):
            self.rules = []

    def save(self) -> None:
        self.path.write_text(
            json.dumps(
                [rule.to_dict() for rule in self.rules],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

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

    def check(
        self,
        window: ActiveWindow,
        *,
        now: datetime | None = None,
    ) -> list[RuleViolation]:
        now = now or datetime.now().astimezone()
        haystack = f"{window.process_name} {window.title}".casefold()
        violations: list[RuleViolation] = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            if rule.last_triggered_at:
                try:
                    last = datetime.fromisoformat(rule.last_triggered_at)
                    if (now - last).total_seconds() < rule.cooldown_s:
                        continue
                except ValueError:
                    pass

            for pattern in rule.patterns:
                if pattern.casefold() in haystack:
                    violations.append(
                        RuleViolation(
                            rule=rule,
                            matched_pattern=pattern,
                            window=window,
                        )
                    )
                    break

        return violations

    def record_trigger(
        self,
        rule: StandingRule,
        *,
        now: datetime | None = None,
    ) -> None:
        now = now or datetime.now().astimezone()
        rule.catch_count += 1
        rule.last_triggered_at = now.isoformat()
        self.save()
