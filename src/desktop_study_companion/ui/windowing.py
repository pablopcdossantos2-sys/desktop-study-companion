from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QDialog


def prepare_top_level_window(
    dialog: QDialog,
    *,
    modal: bool = False,
) -> QDialog:
    """Detach a window from the always-on-top avatar and keep it foreground.

    Qt WebEngine uses an accelerated native surface on Windows. Windows owned
    directly by the frameless avatar can end up behind that surface. Independent
    top-level windows avoid that compositor/owner ordering problem.
    """
    dialog.setParent(None)
    dialog.setWindowFlag(Qt.WindowType.Tool, False)
    dialog.setWindowFlag(Qt.WindowType.Dialog, True)
    dialog.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
    dialog.setWindowModality(
        Qt.WindowModality.ApplicationModal
        if modal
        else Qt.WindowModality.NonModal
    )
    return dialog


def exec_top_level_dialog(dialog: QDialog):
    prepare_top_level_window(dialog, modal=True)

    def bring_to_front() -> None:
        dialog.raise_()
        dialog.activateWindow()

    QTimer.singleShot(0, bring_to_front)
    return dialog.exec()
