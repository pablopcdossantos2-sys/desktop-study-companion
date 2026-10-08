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

    path = save_config(config, tmp_path / "config.json")
    loaded = load_config(path)

    assert loaded.personality.name == "Lumi"
    assert loaded.activity.distraction_keywords == ["youtube", "reddit"]
    assert loaded.voice.volume == 75


def test_invalid_accountability_order_is_rejected() -> None:
    config = AppConfig()
    config.accountability.gentle_after_seconds = 300
    config.accountability.firm_after_seconds = 100

    with pytest.raises(ValueError):
        validate_config(config)
