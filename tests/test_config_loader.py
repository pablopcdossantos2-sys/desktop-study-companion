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
                "voice": {"enabled": False, "rate": 2, "volume": 75},
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
