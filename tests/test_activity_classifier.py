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


def test_neutral_match() -> None:
    classifier = ActivityClassifier(neutral_keywords={"explorer.exe"})
    result = classifier.classify(ActiveWindow("explorer.exe", "Documentos"))
    assert result.kind == ActivityKind.NEUTRAL


def test_unknown_when_no_rule_matches() -> None:
    classifier = ActivityClassifier()
    result = classifier.classify(ActiveWindow("unknown.exe", "Qualquer coisa"))
    assert result.kind == ActivityKind.UNKNOWN
