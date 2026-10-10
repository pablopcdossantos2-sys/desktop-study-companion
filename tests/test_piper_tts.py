from __future__ import annotations

import sys
import types
from pathlib import Path

from desktop_study_companion.voice.piper_tts import PiperNeuralTTS


class _FakeVoice:
    def synthesize_wav(self, text, wav_file, syn_config=None):
        assert text == "Olá"
        wav_file.setframerate(22050)
        wav_file.setsampwidth(2)
        wav_file.setnchannels(1)
        wav_file.writeframes(b"\x00\x00" * 100)


def test_piper_synthesizes_valid_wav_bytes(tmp_path, monkeypatch) -> None:
    engine = PiperNeuralTTS(
        model_id="fake",
        model_dir=tmp_path,
        fallback=None,
    )
    monkeypatch.setattr(engine, "_ensure_voice", lambda: _FakeVoice())
    try:
        audio = engine._synthesize_wav_bytes("Olá")
    finally:
        engine.close()

    assert audio.startswith(b"RIFF")
    assert b"WAVE" in audio[:16]
    assert len(audio) > 44


def test_piper_uses_native_windows_file_playback(tmp_path, monkeypatch) -> None:
    calls = []

    def play_sound(sound, flags):
        calls.append((sound, flags, Path(sound).read_bytes()))

    fake_winsound = types.SimpleNamespace(
        SND_FILENAME=0x00020000,
        SND_SYNC=0,
        PlaySound=play_sound,
    )
    monkeypatch.setitem(sys.modules, "winsound", fake_winsound)

    engine = PiperNeuralTTS(
        model_id="fake",
        model_dir=tmp_path / "data" / "models" / "piper",
        fallback=None,
    )
    try:
        engine._play_wav_bytes(b"RIFFfake-wave")
        expected = (
            tmp_path / "data" / "temp" / "piper-last.wav"
        )
        assert expected.exists()
    finally:
        engine.close()

    assert calls[0][0].endswith("piper-last.wav")
    assert calls[0][1] == 0x00020000
    assert calls[0][2] == b"RIFFfake-wave"
