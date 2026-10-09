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
    config.avatar.width = 420
    config.avatar.height = 620
    config.avatar.look_at_cursor = False

    path = save_config(config, tmp_path / "config.json")
    loaded = load_config(path)

    assert loaded.personality.name == "Lumi"
    assert loaded.activity.distraction_keywords == ["youtube", "reddit"]
    assert loaded.voice.volume == 75
    assert loaded.avatar.width == 420
    assert loaded.avatar.height == 620
    assert loaded.avatar.look_at_cursor is False


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
