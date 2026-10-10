from desktop_study_companion.brain.prompt import build_system_prompt
from desktop_study_companion.config.models import AppConfig


def test_brain_prompt_denies_desktop_access_and_uses_context() -> None:
    config = AppConfig()
    prompt = build_system_prompt(
        config,
        {
            "session_count": 2,
            "average_focus_rate": 0.75,
            "completion_rate": 0.5,
        },
        {
            "active": True,
            "goal": "Revisar",
            "state": "focusing",
            "planned_minutes": 30,
        },
    )

    assert "não fornece ferramentas" in prompt
    assert "não pode alterar janelas" in prompt
    assert "75%" in prompt
    assert "Revisar" in prompt
    assert "coach de estudo e accountability" in prompt
    assert "Empatia não significa passividade" in prompt
    assert "menor próxima ação concreta" in prompt
    assert "privação de sono" in prompt
    assert "SOMENTE com a mensagem final" in prompt
