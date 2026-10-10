import io
import json
import os
import wave
from array import array
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog

import desktop_study_companion.controller as controller_module
from desktop_study_companion.config.loader import (
    ConfigRecoveryState,
    load_config_with_recovery,
    preserve_recovery_source_before_write,
)
from desktop_study_companion.config.models import AppConfig
from desktop_study_companion.controller import ApplicationController
from desktop_study_companion.ui.windowing import exec_top_level_dialog
from desktop_study_companion.voice.piper_tts import (
    PiperNeuralTTS,
    _scale_pcm16_wav_volume,
)


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _pcm16_wav(samples: list[int]) -> bytes:
    payload = array("h", samples)
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(22050)
        writer.writeframes(payload.tobytes())
    return output.getvalue()


def _wav_samples(audio: bytes) -> list[int]:
    with wave.open(io.BytesIO(audio), "rb") as reader:
        frames = reader.readframes(reader.getnframes())
    values = array("h")
    values.frombytes(frames)
    return list(values)


def test_coach_late_return_announces_only_latest_milestone() -> None:
    controller = object.__new__(ApplicationController)
    controller.config = AppConfig()
    controller.sessions = SimpleNamespace(
        active=True,
        session=SimpleNamespace(
            goal="Cálculo",
            planned_minutes=60,
        ),
    )
    controller.personality = SimpleNamespace(
        milestone_message=lambda goal, milestone: f"{goal}:{milestone}"
    )
    controller._coach_milestones_announced = set()
    spoken: list[str] = []
    controller._say = lambda text, avatar_state=None: spoken.append(text)

    for elapsed in (2881.0, 2882.0, 2883.0, 2884.0):
        controller._maybe_coach_milestone(elapsed)

    assert spoken == ["Cálculo:75"]
    assert controller._coach_milestones_announced == {25, 50, 75}


def test_piper_portable_volume_scales_pcm16_samples() -> None:
    audio = _pcm16_wav([10000, -10000, 20000, -20000])

    half = _scale_pcm16_wav_volume(audio, 50)
    muted = _scale_pcm16_wav_volume(audio, 0)

    assert _wav_samples(half) == [5000, -5000, 10000, -10000]
    assert _wav_samples(muted) == [0, 0, 0, 0]


def test_second_sync_dialog_is_rejected_without_nested_event_loop() -> None:
    app = _app()
    first = QDialog()
    second = QDialog()
    nested_result: list[int] = []

    def try_second() -> None:
        nested_result.append(exec_top_level_dialog(second))
        QTimer.singleShot(10, first.reject)

    QTimer.singleShot(10, try_second)
    first_result = exec_top_level_dialog(first)
    app.processEvents()

    assert first_result == QDialog.DialogCode.Rejected
    assert nested_result == [QDialog.DialogCode.Rejected]
    assert not second.isVisible()


def _fake_runtime(path: Path, *, dll: bytes = b"runtime-v1") -> None:
    (path / "espeak-ng-data").mkdir(parents=True, exist_ok=True)
    (path / "piper.exe").write_bytes(b"piper")
    (path / "espeak-ng-data" / "phontab").write_bytes(b"phonemes")
    (path / "onnxruntime.dll").write_bytes(dll)


def _bare_piper(cache_root: Path) -> PiperNeuralTTS:
    engine = object.__new__(PiperNeuralTTS)
    engine._runtime_cache = None
    engine._ascii_native_root = lambda: cache_root
    return engine


def test_piper_runtime_staging_repairs_partial_copy_and_tracks_updates(
    tmp_path,
) -> None:
    source = tmp_path / "source-runtime"
    cache = tmp_path / "cache"
    _fake_runtime(source)

    first = _bare_piper(cache)
    target1 = first._stage_portable_runtime(source)
    (target1 / "onnxruntime.dll").unlink()

    restarted = _bare_piper(cache)
    repaired = restarted._stage_portable_runtime(source)
    assert (repaired / "onnxruntime.dll").read_bytes() == b"runtime-v1"

    (source / "onnxruntime.dll").write_bytes(b"runtime-v2")
    updated = _bare_piper(cache)._stage_portable_runtime(source)

    assert updated != repaired
    assert (updated / "onnxruntime.dll").read_bytes() == b"runtime-v2"


def test_piper_preview_keeps_polling_explicit_running_state(monkeypatch) -> None:
    engine = SimpleNamespace(
        synthesis_status="running",
        last_error=None,
        last_success=False,
    )
    controller = object.__new__(ApplicationController)
    controller._voice_preview = engine
    controller.widget = SimpleNamespace(say=lambda text: None)

    messages: list[tuple[str, bool]] = []
    dialog = SimpleNamespace(
        set_piper_test_status=lambda text, error=False:
            messages.append((text, error)),
    )
    scheduled = []
    monkeypatch.setattr(
        controller_module.QTimer,
        "singleShot",
        lambda delay, callback: scheduled.append((delay, callback)),
    )

    controller._poll_piper_preview(engine, dialog, attempts=480)

    assert scheduled and scheduled[0][0] == 250
    assert messages
    assert "ainda está trabalhando" in messages[0][0]
    assert messages[0][1] is False


def test_unreadable_config_is_marked_for_backup_before_overwrite(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "config.json"
    original = b'{"personality":{"name":"Original"}}\n'
    path.write_bytes(original)
    real_read_text = Path.read_text

    def blocked_read(self, *args, **kwargs):
        if self == path:
            raise PermissionError("temporarily locked")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", blocked_read)
    config, notice, state = load_config_with_recovery(
        path,
        include_state=True,
    )

    assert config is not None
    assert notice is not None
    assert state == ConfigRecoveryState(
        preserve_before_write=path,
        reason="unreadable",
    )

    backup = preserve_recovery_source_before_write(state, path)
    assert backup is not None
    assert backup.read_bytes() == original


def test_insecure_brain_runtime_disable_preserves_original_before_save(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "config.json"
    payload = {
        "voice": {"enabled": False},
        "brain": {
            "enabled": True,
            "base_url": "http://192.168.1.10:11434/v1",
            "model": "local",
            "api_key_env": "DSC_TEST_API_KEY",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("DSC_TEST_API_KEY", "secret")

    config, notice, state = load_config_with_recovery(
        path,
        include_state=True,
    )

    assert config.brain.enabled is False
    assert notice is not None
    assert state.reason == "brain_transport"

    backup = preserve_recovery_source_before_write(state, path)
    assert backup is not None
    preserved = json.loads(backup.read_text(encoding="utf-8"))
    assert preserved["brain"]["enabled"] is True
