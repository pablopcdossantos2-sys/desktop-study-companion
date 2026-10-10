import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QRect, QSize, QTimer, Qt
from PySide6.QtWidgets import QApplication, QDialog, QWidget

from desktop_study_companion.ui.windowing import (
    choose_dialog_position,
    exec_top_level_dialog,
    prepare_top_level_window,
)
from desktop_study_companion.voice.piper_tts import PiperNeuralTTS
import desktop_study_companion.voice.piper_tts as piper_tts_module


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_dialog_position_prefers_corner_far_from_companion() -> None:
    screen = QRect(0, 0, 1920, 1080)
    avatar = QRect(1500, 500, 360, 540)

    point = choose_dialog_position(
        QSize(650, 560),
        [screen],
        avatar,
    )

    assert point.x() < avatar.left()
    assert point.y() <= 64


def test_dialog_position_can_use_another_monitor() -> None:
    left = QRect(-1920, 0, 1920, 1080)
    right = QRect(0, 0, 1920, 1080)
    avatar = QRect(1450, 500, 360, 540)

    point = choose_dialog_position(
        QSize(650, 560),
        [left, right],
        avatar,
    )

    assert point.x() < 0


def test_top_level_dialog_has_close_button_and_is_nonmodal() -> None:
    _app()
    dialog = QDialog()

    prepare_top_level_window(dialog)

    assert dialog.windowFlags() & Qt.WindowType.WindowCloseButtonHint
    assert dialog.windowModality() == Qt.WindowModality.NonModal


def test_exec_top_level_dialog_can_close_without_disabling_companion() -> None:
    app = _app()
    companion = QWidget()
    companion.setWindowTitle("Desktop Study Companion")
    companion.setGeometry(1200, 400, 360, 540)
    companion.show()

    dialog = QDialog()
    dialog.resize(420, 240)
    companion_enabled = []

    QTimer.singleShot(
        0,
        lambda: companion_enabled.append(companion.isEnabled()),
    )
    QTimer.singleShot(20, dialog.close)

    result = exec_top_level_dialog(
        dialog,
        avoid_widget=companion,
    )

    companion.close()
    app.processEvents()
    assert result == QDialog.DialogCode.Rejected
    assert companion_enabled == [True]


def test_frozen_piper_detects_bundled_standalone_runtime(
    tmp_path,
    monkeypatch,
) -> None:
    executable = tmp_path / "DesktopStudyCompanion.exe"
    executable.write_bytes(b"exe")
    runtime = tmp_path / "piper-runtime"
    data = runtime / "espeak-ng-data"
    data.mkdir(parents=True)
    (runtime / "piper.exe").write_bytes(b"exe")
    (data / "phontab").write_bytes(b"data")

    monkeypatch.setattr(piper_tts_module.sys, "executable", str(executable))
    monkeypatch.setattr(
        piper_tts_module.sys,
        "frozen",
        True,
        raising=False,
    )

    tts = object.__new__(PiperNeuralTTS)

    assert tts._portable_runtime_source() == runtime
