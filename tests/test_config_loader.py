import json

from desktop_study_companion.config.loader import load_config


def test_load_config_including_voice(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "activity": {
                    "productive_keywords": ["anki"],
                    "neutral_keywords": ["explorer"],
                    "distraction_keywords": ["youtube"],
                },
                "voice": {
                    "enabled": False,
                    "rate": 2,
                    "volume": 75,
                    "voice_id": "voice-test"
                },
                "speech_input": {
                    "enabled": True,
                    "model": "tiny",
                    "language": "pt",
                    "device": "cpu",
                    "compute_type": "int8",
                    "microphone_device": 4,
                    "max_record_seconds": 20,
                    "auto_send": False
                },
                "brain": {
                    "enabled": True,
                    "base_url": "http://127.0.0.1:11434/v1",
                    "model": "demo",
                    "history_messages": 8
                },
                "avatar": {
                    "enabled": True,
                    "width": 480,
                    "height": 700,
                    "look_at_cursor": False,
                    "lip_sync": False
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_config(path)

    assert config.activity.productive_keywords == ["anki"]
    assert config.activity.neutral_keywords == ["explorer"]
    assert config.activity.distraction_keywords == ["youtube"]
    assert config.voice.enabled is False
    assert config.voice.rate == 2
    assert config.voice.volume == 75
    assert config.voice.voice_id == "voice-test"
    assert config.speech_input.enabled is True
    assert config.speech_input.model == "tiny"
    assert config.speech_input.microphone_device == 4
    assert config.speech_input.max_record_seconds == 20
    assert config.speech_input.auto_send is False
    assert config.brain.enabled is True
    assert config.brain.model == "demo"
    assert config.brain.history_messages == 8
    assert config.avatar.enabled is True
    assert config.avatar.width == 480
    assert config.avatar.height == 700
    assert config.avatar.look_at_cursor is False
    assert config.avatar.lip_sync is False
