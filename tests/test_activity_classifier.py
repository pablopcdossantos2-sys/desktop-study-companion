from desktop_study_companion.activity.classifier import ActivityClassifier
from desktop_study_companion.activity.models import ActiveWindow, ActivityKind


def test_distraction_has_priority() -> None:
    classifier = ActivityClassifier(
        productive_keywords={"chrome"},
        neutral_keywords=set(),
        distraction_keywords={"youtube"},
    )
    result = classifier.classify(ActiveWindow("chrome.exe", "YouTube - aula"))
    assert result.kind == ActivityKind.DISTRACTION


def test_productive_match() -> None:
    classifier = ActivityClassifier(productive_keywords={"anki"})
    result = classifier.classify(ActiveWindow("anki.exe", "Deck"))
    assert result.kind == ActivityKind.PRODUCTIVE
