from __future__ import annotations

from dataclasses import dataclass, field

from .matching import (
    is_known_productive_process,
    keyword_matches,
    normalized_keywords,
)
from .models import ActiveWindow, ActivityKind, ClassifiedActivity


@dataclass(slots=True)
class ActivityClassifier:
    productive_keywords: set[str] = field(default_factory=set)
    neutral_keywords: set[str] = field(default_factory=set)
    distraction_keywords: set[str] = field(default_factory=set)

    def classify(self, window: ActiveWindow) -> ClassifiedActivity:
        # Explicit user distraction rules override the safe default only when
        # they match the process itself. Merely mentioning "YouTube" in a Word
        # or VS Code title does not turn that productive application into a
        # distraction.
        for keyword in normalized_keywords(self.distraction_keywords):
            if keyword_matches(keyword, window.process_name, window.title):
                return ClassifiedActivity(
                    window,
                    ActivityKind.DISTRACTION,
                    f"matched distraction keyword: {keyword}",
                )

        for keyword in normalized_keywords(self.productive_keywords):
            if keyword_matches(
                keyword,
                window.process_name,
                window.title,
                protect_productive_titles=False,
            ):
                return ClassifiedActivity(
                    window,
                    ActivityKind.PRODUCTIVE,
                    f"matched productive keyword: {keyword}",
                )

        for keyword in normalized_keywords(self.neutral_keywords):
            if keyword_matches(
                keyword,
                window.process_name,
                window.title,
                protect_productive_titles=False,
            ):
                return ClassifiedActivity(
                    window,
                    ActivityKind.NEUTRAL,
                    f"matched neutral keyword: {keyword}",
                )

        if is_known_productive_process(window.process_name):
            return ClassifiedActivity(
                window=window,
                kind=ActivityKind.PRODUCTIVE,
                reason=f"known productive process: {window.process_name}",
            )

        return ClassifiedActivity(
            window,
            ActivityKind.UNKNOWN,
            "no classification rule matched",
        )
