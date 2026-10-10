from desktop_study_companion.config.models import AppConfig
from desktop_study_companion.config.writer import validate_config


def test_dev15_defaults_enable_proactivity_and_neural_voice() -> None:
    config = AppConfig()

    assert config.proactivity.enabled is True
    assert config.proactivity.motivational_messages is True
    assert config.voice.engine == "piper"
    assert config.voice.piper_voice_id == "pt_BR-faber-medium"
    assert config.avatar.spontaneous_gestures is True

    validate_config(config)


def test_proactivity_interval_order_is_validated() -> None:
    config = AppConfig()
    config.proactivity.min_interval_minutes = 20
    config.proactivity.max_interval_minutes = 10

    try:
        validate_config(config)
    except ValueError as exc:
        assert "proactivity maximum" in str(exc)
    else:
        raise AssertionError("expected invalid proactivity interval")


def test_avatar_gesture_interval_order_is_validated() -> None:
    config = AppConfig()
    config.avatar.gesture_min_seconds = 40
    config.avatar.gesture_max_seconds = 10

    try:
        validate_config(config)
    except ValueError as exc:
        assert "gesture maximum" in str(exc)
    else:
        raise AssertionError("expected invalid gesture interval")
