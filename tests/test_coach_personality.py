from desktop_study_companion.accountability.models import InterventionKind
from desktop_study_companion.personality.models import Personality
import desktop_study_companion.personality.renderer as renderer_module
from desktop_study_companion.personality.renderer import PersonalityRenderer


def test_custom_activation_phrase_overrides_default_and_renders_tokens() -> None:
    renderer = PersonalityRenderer(
        Personality(strictness=85, initiative=90),
        name="Luna",
    )

    message = renderer.motivation_message(
        custom_activation=[
            "{name}: escolha {goal} e me dê um bloco curto."
        ],
    )

    assert message == "Luna: escolha seu estudo e me dê um bloco curto."


def test_custom_focus_phrase_uses_session_metrics() -> None:
    renderer = PersonalityRenderer(Personality(), name="Luna")

    message = renderer.motivation_message(
        "Cálculo",
        state="focusing",
        focused_seconds=750,
        distracted_seconds=120,
        custom_focus=[
            "{name}: {goal}; foco {focused_minutes}; distração {distracted_minutes}."
        ],
    )

    assert message == "Luna: Cálculo; foco 12.5; distração 2."


def test_recovery_phrase_can_be_programmed() -> None:
    renderer = PersonalityRenderer(Personality(), name="Luna")

    message = renderer.recovery_message(
        "Anatomia",
        custom=["Voltou para {goal}. Agora protege cinco minutos."],
    )

    assert message == "Voltou para Anatomia. Agora protege cinco minutos."


def test_session_result_uses_custom_celebration_and_reset() -> None:
    renderer = PersonalityRenderer(Personality(), name="Luna")

    completed = renderer.session_result_message(
        "Inglês",
        completed=True,
        focused_minutes=28.5,
        distracted_minutes=1.5,
        custom_celebration=[
            "Fechou {goal}: {focused_minutes} minutos de foco."
        ],
    )
    abandoned = renderer.session_result_message(
        "Inglês",
        completed=False,
        focused_minutes=8,
        distracted_minutes=5,
        custom_reset=[
            "{goal} não acabou. Recomeça menor."
        ],
    )

    assert completed == "Fechou Inglês: 28.5 minutos de foco."
    assert abandoned == "Inglês não acabou. Recomeça menor."


def test_insistent_intervention_is_direct_without_humiliation() -> None:
    renderer = PersonalityRenderer(
        Personality(strictness=90, sarcasm=80),
        name="Luna",
    )

    for _ in range(20):
        message = renderer.intervention_message(
            InterventionKind.INSISTENT_CHALLENGE
        ).casefold()
        assert "idiota" not in message
        assert "fracasso" not in message
        assert any(
            cue in message
            for cue in (
                "volte",
                "retome",
                "compromisso",
                "material",
                "sessão",
            )
        )


def test_initiative_biases_proactive_interval_toward_shorter_end(
    monkeypatch,
) -> None:
    captured = {}

    def fake_triangular(low, high, mode):
        captured["low"] = low
        captured["high"] = high
        captured["mode"] = mode
        return mode

    monkeypatch.setattr(renderer_module.random, "triangular", fake_triangular)
    renderer = PersonalityRenderer(
        Personality(initiative=90),
        name="Luna",
    )

    chosen = renderer.proactive_interval_minutes(6, 12)

    assert captured["low"] == 6
    assert captured["high"] == 12
    assert captured["mode"] < 7
    assert 6 <= chosen <= 12
