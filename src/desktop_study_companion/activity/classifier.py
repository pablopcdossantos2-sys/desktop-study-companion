from __future__ import annotations

import re
from dataclasses import dataclass, field

from .models import ActiveWindow, ActivityKind, ClassifiedActivity


_KNOWN_PRODUCTIVE_PROCESSES = {
    "anki.exe",
    "code.exe",
    "devenv.exe",
    "excel.exe",
    "notepad.exe",
    "notepad++.exe",
    "obsidian.exe",
    "onenote.exe",
    "powerpnt.exe",
    "winword.exe",
}


def _normalized_keywords(values: set[str]) -> tuple[str, ...]:
    return tuple(sorted(
        {value.casefold().strip() for value in values if value.strip()},
        key=len,
        reverse=True,
    ))


def _keyword_matches(keyword: str, process_name: str, title: str) -> bool:
    process = process_name.casefold().strip()
    if process == keyword or process.removesuffix(".exe") == keyword.removesuffix(".exe"):
        return True
    return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", title.casefold()) is not None


@dataclass(slots=True)
class ActivityClassifier:
    productive_keywords: set[str] = field(default_factory=set)
    neutral_keywords: set[str] = field(default_factory=set)
    distraction_keywords: set[str] = field(default_factory=set)

    def classify(self, window: ActiveWindow) -> ClassifiedActivity:
        process = window.process_name.casefold().strip()
        if process in _KNOWN_PRODUCTIVE_PROCESSES:
            return ClassifiedActivity(
                window=window,
                kind=ActivityKind.PRODUCTIVE,
                reason=f"known productive process: {window.process_name}",
            )

        for keyword in _normalized_keywords(self.distraction_keywords):
            if _keyword_matches(keyword, window.process_name, window.title):
                return ClassifiedActivity(window, ActivityKind.DISTRACTION, f"matched distraction keyword: {keyword}")

        for keyword in _normalized_keywords(self.productive_keywords):
            if _keyword_matches(keyword, window.process_name, window.title):
                return ClassifiedActivity(window, ActivityKind.PRODUCTIVE, f"matched productive keyword: {keyword}")

        for keyword in _normalized_keywords(self.neutral_keywords):
            if _keyword_matches(keyword, window.process_name, window.title):
                return ClassifiedActivity(window, ActivityKind.NEUTRAL, f"matched neutral keyword: {keyword}")

        return ClassifiedActivity(window, ActivityKind.UNKNOWN, "no classification rule matched")
