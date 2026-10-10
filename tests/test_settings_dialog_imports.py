from desktop_study_companion.config.models import (
    ProactivityConfig,
    SpeechInputConfig,
)
from desktop_study_companion.ui.settings_dialog import SettingsDialog


def test_settings_dialog_has_speech_input_config_in_scope() -> None:
    assert (
        SettingsDialog.values.__globals__["SpeechInputConfig"]
        is SpeechInputConfig
    )



def test_settings_dialog_has_proactivity_config_in_scope() -> None:
    assert (
        SettingsDialog.values.__globals__["ProactivityConfig"]
        is ProactivityConfig
    )
