from __future__ import annotations

from dataclasses import dataclass, field

from .models import ActiveWindow, ActivityKind, ClassifiedActivity


@dataclass(slots=True)
class ActivityClassifier:
    productive_keywords: set[str] = field(default_factory=set)
    distraction_keywords: set[str] = field(default_factory=set)

    def classify(self, window: ActiveWindow) -> ClassifiedActivity:
        haystack = f"{window.process_name} {window.title}".casefold()

        for keyword in self.distraction_keywords:
            if keyword.casefold() in haystack:
                return ClassifiedActivity(
                    window=window,
                    kind=ActivityKind.DISTRACTION,
                    reason=f"matched distraction keyword: {keyword}",
                )

        for keyword in self.productive_keywords:
            if keyword.casefold() in haystack:
                return ClassifiedActivity(
                    window=window,
                    kind=ActivityKind.PRODUCTIVE,
                    reason=f"matched productive keyword: {keyword}",
                )

        return ClassifiedActivity(
            window=window,
            kind=ActivityKind.UNKNOWN,
            reason="no classification rule matched",
        )
