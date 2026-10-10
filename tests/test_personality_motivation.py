from desktop_study_companion.personality.models import Personality
from desktop_study_companion.personality.renderer import PersonalityRenderer


def test_motivation_message_uses_active_goal() -> None:
    renderer = PersonalityRenderer(Personality(), name="Companion")
    message = renderer.motivation_message("Revisar capítulo 3")

    assert message
    assert "Revisar capítulo 3" in message


def test_motivation_message_without_session_is_nonempty() -> None:
    renderer = PersonalityRenderer(Personality(), name="Companion")
    assert renderer.motivation_message()
