import json

import pytest

from desktop_study_companion.config.loader import load_config
from desktop_study_companion.config.models import AppConfig
from desktop_study_companion.config.writer import save_config, validate_config


def test_config_round_trip(tmp_path) -> None:
    config = AppConfig()
    config.personality.name = "Lumi"
    config.activity.distraction_keywords = ["youtube", "reddit"]
    config.voice.volume = 75
    config.voice.voice_id = "voice-token-test"
    config.avatar.width = 420
    config.avatar.height = 620
    config.avatar.look_at_cursor = False
    config.speech_input.enabled = True
    config.speech_input.model = "tiny"
    config.speech_input.language = "pt"
    config.speech_input.microphone_device = 3
    config.speech_input.auto_send = False
    config.brain.enabled = True
    config.brain.model = "local-model"
    config.brain.base_url = "http://127.0.0.1:11434/v1"
    config.proactivity.coach_mode = True
    config.proactivity.activation_phrases = ["Começa {goal}."]
    config.proactivity.focus_phrases = ["Continua {goal}."]

    path = save_config(config, tmp_path / "config.json")
    loaded = load_config(path)

    assert loaded.personality.name == "Lumi"
    assert loaded.activity.distraction_keywords == ["youtube", "reddit"]
    assert loaded.voice.volume == 75
    assert loaded.voice.voice_id == "voice-token-test"
    assert loaded.avatar.width == 420
    assert loaded.avatar.height == 620
    assert loaded.avatar.look_at_cursor is False
    assert loaded.speech_input.enabled is True
    assert loaded.speech_input.model == "tiny"
    assert loaded.speech_input.language == "pt"
    assert loaded.speech_input.microphone_device == 3
    assert loaded.speech_input.auto_send is False
    assert loaded.brain.enabled is True
    assert loaded.brain.model == "local-model"
    assert loaded.proactivity.coach_mode is True
    assert loaded.proactivity.activation_phrases == ["Começa {goal}."]
    assert loaded.proactivity.focus_phrases == ["Continua {goal}."]


def test_invalid_accountability_order_is_rejected() -> None:
    config = AppConfig()
    config.accountability.gentle_after_seconds = 300
    config.accountability.firm_after_seconds = 100

    with pytest.raises(ValueError):
        validate_config(config)


def test_invalid_avatar_dimensions_are_rejected() -> None:
    config = AppConfig()
    config.avatar.width = 100

    with pytest.raises(ValueError, match="avatar width"):
        validate_config(config)


def test_enabled_brain_requires_model() -> None:
    config = AppConfig()
    config.brain.enabled = True
    config.brain.model = ""

    with pytest.raises(ValueError, match="brain model"):
        validate_config(config)


def test_invalid_speech_recording_limit_is_rejected() -> None:
    config = AppConfig()
    config.speech_input.max_record_seconds = 1

    with pytest.raises(ValueError, match="max_record_seconds"):
        validate_config(config)
