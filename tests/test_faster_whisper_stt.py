import av

from desktop_study_companion.voice.faster_whisper_stt import FasterWhisperSTT


class _Segment:
    def __init__(self, text):
        self.text = text


class _FakeModel:
    def transcribe(self, path, **kwargs):
        assert path.endswith(".wav")
        assert kwargs["language"] == "pt"
        return [_Segment(" Olá "), _Segment(" mundo ")], object()


def test_transcription_joins_segments(tmp_path, monkeypatch) -> None:
    provider = FasterWhisperSTT(language="pt")
    monkeypatch.setattr(provider, "_load_model", lambda: _FakeModel())
    path = tmp_path / "sample.wav"
    path.write_bytes(b"fake")

    assert provider.transcribe_file(path) == "Olá mundo"



def test_pyav_major_version_is_compatible() -> None:
    major = int(av.__version__.split(".", 1)[0])
    assert major < 19
