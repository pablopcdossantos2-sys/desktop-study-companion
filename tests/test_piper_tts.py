from __future__ import annotations

import sys
import types

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


def test_piper_uses_native_windows_memory_playback(tmp_path, monkeypatch) -> None:
    calls = []
    fake_winsound = types.SimpleNamespace(
        SND_MEMORY=4,
        PlaySound=lambda sound, flags: calls.append((sound, flags)),
    )
    monkeypatch.setitem(sys.modules, "winsound", fake_winsound)

    engine = PiperNeuralTTS(
        model_id="fake",
        model_dir=tmp_path,
        fallback=None,
    )
    try:
        engine._play_wav_bytes(b"RIFFfake-wave")
    finally:
        engine.close()

    assert calls[0] == (b"RIFFfake-wave", 4)
