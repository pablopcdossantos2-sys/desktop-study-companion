from __future__ import annotations

import subprocess
import sys
import types
import wave
from pathlib import Path

from desktop_study_companion.voice.piper_tts import PiperNeuralTTS


def _write_test_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setframerate(22050)
        wav_file.setsampwidth(2)
        wav_file.setnchannels(1)
        wav_file.writeframes(b"\x00\x00" * 100)


def test_piper_synthesizes_in_isolated_worker(tmp_path, monkeypatch) -> None:
    commands = []

    def fake_run(command, **kwargs):
        commands.append((command, kwargs))
        output = Path(command[command.index("--output") + 1])
        _write_test_wav(output)
        return subprocess.CompletedProcess(
            command,
            returncode=0,
            stdout="stage=load model=fake\nstage=synthesize chars=3\nstage=done bytes=244",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    engine = PiperNeuralTTS(
        model_id="fake",
        model_dir=tmp_path / "data" / "models" / "piper",
        fallback=None,
    )
    try:
        audio = engine._synthesize_wav_bytes("Olá")
        diagnostic = tmp_path / "data" / "temp" / "piper-last.wav"
        assert diagnostic.exists()
    finally:
        engine.close()

    assert audio.startswith(b"RIFF")
    assert b"WAVE" in audio[:16]
    assert len(audio) > 44
    command, kwargs = commands[0]
    assert "desktop_study_companion.voice.piper_worker" in command
    assert kwargs["timeout"] == engine.SYNTHESIS_TIMEOUT_SECONDS
    assert kwargs["check"] is False


def test_piper_uses_frozen_executable_for_worker(tmp_path, monkeypatch) -> None:
    engine = PiperNeuralTTS(
        model_id="fake",
        model_dir=tmp_path / "data" / "models" / "piper",
        fallback=None,
    )
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\\App\\DesktopStudyCompanion.exe")
    try:
        command = engine._worker_command(
            text_file=tmp_path / "text.txt",
            output=tmp_path / "out.wav",
        )
    finally:
        engine.close()

    assert command[:2] == [
        r"C:\\App\\DesktopStudyCompanion.exe",
        "--piper-worker",
    ]


def test_piper_uses_native_windows_file_playback(tmp_path, monkeypatch) -> None:
    calls = []

    def play_sound(sound, flags):
        if sound is not None:
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
