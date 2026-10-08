from __future__ import annotations

"""Deterministic nag escalation inspired by bonziPONY's directive system.

bonziPONY keeps per-directive urgency, nag count, last nag style/text and a
next-nag timestamp. Its LLM may choose timing dynamically. This project keeps
those useful state concepts but makes timing deterministic so safety and study
policy never depend on model output.

Upstream reference:
https://github.com/maresmaremares/bonziPONY/blob/master/core/agent_loop.py
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NagDecision:
    severity: int
    style: str
    delay_seconds: int


class NaggingPolicy:
    """Map urgency + history to a progressively more insistent schedule."""

    _STYLES = ("gentle", "firm", "direct", "insistent")

    def initial_delay_seconds(self, urgency: int) -> int:
        urgency = max(1, min(10, int(urgency)))
        if urgency == 10:
            return 15
        if urgency >= 8:
            return 60
        if urgency >= 5:
            return 180
        return 600

    def decide(self, urgency: int, nag_count: int) -> NagDecision:
        urgency = max(1, min(10, int(urgency)))
        nag_count = max(0, int(nag_count))

        # Urgency gives the starting severity; repeated misses escalate it.
        base_severity = 1
        if urgency >= 8:
            base_severity = 3
        elif urgency >= 5:
            base_severity = 2

        severity = min(4, base_severity + nag_count // 2)
        style = self._STYLES[severity - 1]

        # Repeated misses shorten the interval, but never below the floor.
        if urgency == 10:
            base, floor = 30, 15
        elif urgency >= 8:
            base, floor = 120, 30
        elif urgency >= 5:
            base, floor = 300, 60
        else:
            base, floor = 900, 180

        shrink = 0.80 ** nag_count
        delay = max(floor, int(round(base * shrink)))

        return NagDecision(severity=severity, style=style, delay_seconds=delay)
