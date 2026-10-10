from desktop_study_companion.voice.audio_capture import InputDevice


def test_input_device_shape() -> None:
    device = InputDevice(
        index=2,
        name="Microfone",
        channels=1,
        default_samplerate=48000.0,
    )

    assert device.index == 2
    assert device.channels == 1
