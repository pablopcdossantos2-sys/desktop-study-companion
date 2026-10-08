from desktop_study_companion.accountability.engine import AccountabilityEngine
from desktop_study_companion.activity.classifier import ActivityClassifier
from desktop_study_companion.personality.models import Personality


def main() -> None:
    personality = Personality()
    classifier = ActivityClassifier(
        productive_keywords={"anki", "obsidian", "visual studio code"},
        distraction_keywords={"youtube", "netflix", "reddit"},
    )
    accountability = AccountabilityEngine()

    print("Desktop Study Companion — foundation v0.0.1")
    print(
        "Core modules loaded:",
        personality.__class__.__name__,
        classifier.__class__.__name__,
        accountability.__class__.__name__,
    )
    print("The Windows monitor, desktop character and voice pipeline are next.")


if __name__ == "__main__":
    main()
