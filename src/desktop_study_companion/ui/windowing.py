from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QEventLoop, QPoint, QRect, QSize, QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QWidget,
)


def choose_dialog_position(
    dialog_size: QSize,
    screen_geometries: Sequence[QRect],
    avoid_rect: QRect | None,
    *,
    margin: int = 32,
) -> QPoint:
    """Choose an on-screen corner that is as far as possible from the avatar."""
    screens = [rect for rect in screen_geometries if rect.isValid()]
    if not screens:
        return QPoint(margin, margin)

    width = max(240, int(dialog_size.width()))
    height = max(160, int(dialog_size.height()))
    avoid_center = (
        avoid_rect.center()
        if avoid_rect is not None and avoid_rect.isValid()
        else screens[0].center()
    )
    expanded_avoid = (
        avoid_rect.adjusted(-margin, -margin, margin, margin)
        if avoid_rect is not None and avoid_rect.isValid()
        else None
    )

    best_point = QPoint(screens[0].left() + margin, screens[0].top() + margin)
    best_score = float("-inf")

    for screen in screens:
        usable_width = max(1, screen.width() - 2 * margin)
        usable_height = max(1, screen.height() - 2 * margin)
        candidate_width = min(width, usable_width)
        candidate_height = min(height, usable_height)

        left = screen.left() + margin
        right = max(left, screen.right() - candidate_width - margin + 1)
        top = screen.top() + margin
        bottom = max(top, screen.bottom() - candidate_height - margin + 1)

        for x, y in (
            (left, top),
            (right, top),
            (left, bottom),
            (right, bottom),
        ):
            rect = QRect(x, y, candidate_width, candidate_height)
            center = rect.center()
            dx = center.x() - avoid_center.x()
            dy = center.y() - avoid_center.y()
            score = float(dx * dx + dy * dy)
            if expanded_avoid is not None and rect.intersects(expanded_avoid):
                score -= 1_000_000_000_000.0
            if score > best_score:
                best_score = score
                best_point = QPoint(x, y)

    return best_point


def _default_avoid_widget() -> QWidget | None:
    app = QApplication.instance()
    if app is None:
        return None
    for widget in app.topLevelWidgets():
        if (
            widget.isVisible()
            and widget.windowTitle() == "Desktop Study Companion"
        ):
            return widget
    return None


def position_away_from_companion(
    dialog: QWidget,
    avoid_widget: QWidget | None = None,
) -> None:
    app = QApplication.instance()
    if app is None:
        return

    avoid_widget = avoid_widget or _default_avoid_widget()
    avoid_rect = (
        avoid_widget.frameGeometry()
        if avoid_widget is not None and avoid_widget.isVisible()
        else None
    )
    screens = [screen.availableGeometry() for screen in app.screens()]
    point = choose_dialog_position(dialog.size(), screens, avoid_rect)
    dialog.move(point)


def prepare_top_level_window(
    dialog: QDialog,
    *,
    modal: bool = False,
    avoid_widget: QWidget | None = None,
) -> QDialog:
    """Detach dialogs from the WebEngine avatar and keep them reachable.

    Dialogs remain independent top-level windows so Qt WebEngine cannot cover
    them. They are deliberately non-application-modal: the user can still move
    the companion or use its context menu while a configuration window is open.
    """
    dialog.setParent(None)
    dialog.setWindowFlag(Qt.WindowType.Tool, False)
    dialog.setWindowFlag(Qt.WindowType.Dialog, True)
    dialog.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
    dialog.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
    dialog.setWindowFlag(Qt.WindowType.WindowSystemMenuHint, True)
    # Keep every application dialog non-modal with respect to the avatar.
    # The local event loop used by exec_top_level_dialog preserves synchronous
    # controller code without disabling the companion window.
    dialog.setWindowModality(Qt.WindowModality.NonModal)

    QTimer.singleShot(
        0,
        lambda d=dialog, a=avoid_widget: position_away_from_companion(d, a),
    )
    return dialog


def exec_top_level_dialog(
    dialog: QDialog,
    *,
    avoid_widget: QWidget | None = None,
):
    """Run a dialog synchronously without blocking the companion window."""
    prepare_top_level_window(
        dialog,
        modal=False,
        avoid_widget=avoid_widget,
    )
    loop = QEventLoop()
    result = [int(QDialog.DialogCode.Rejected)]

    def finished(code: int) -> None:
        result[0] = int(code)
        if loop.isRunning():
            loop.quit()

    dialog.finished.connect(finished)
    app = QApplication.instance()
    if app is not None:
        app.aboutToQuit.connect(dialog.reject)

    dialog.show()

    def bring_to_front() -> None:
        position_away_from_companion(dialog, avoid_widget)
        dialog.raise_()
        dialog.activateWindow()

    QTimer.singleShot(0, bring_to_front)
    try:
        loop.exec()
    finally:
        if app is not None:
            try:
                app.aboutToQuit.disconnect(dialog.reject)
            except (RuntimeError, TypeError):
                pass
    return result[0]


def get_item_top_level(
    title: str,
    label: str,
    items: Sequence[str],
    *,
    current: int = 0,
    editable: bool = False,
    avoid_widget: QWidget | None = None,
) -> tuple[str, bool]:
    if not items:
        return "", False

    dialog = QInputDialog()
    dialog.setWindowTitle(title)
    dialog.setLabelText(label)
    dialog.setComboBoxItems(list(items))
    dialog.setComboBoxEditable(editable)
    dialog.setTextValue(items[max(0, min(current, len(items) - 1))])

    accepted = (
        exec_top_level_dialog(dialog, avoid_widget=avoid_widget)
        == QDialog.DialogCode.Accepted
    )
    return dialog.textValue(), accepted


def get_existing_directory_top_level(
    title: str,
    directory: str,
    *,
    avoid_widget: QWidget | None = None,
) -> str:
    dialog = QFileDialog(None, title, directory)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dialog.setFileMode(QFileDialog.FileMode.Directory)
    dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
    if (
        exec_top_level_dialog(dialog, avoid_widget=avoid_widget)
        != QDialog.DialogCode.Accepted
    ):
        return ""
    selected = dialog.selectedFiles()
    return selected[0] if selected else ""


def get_save_file_name_top_level(
    title: str,
    suggested: str,
    name_filter: str,
    *,
    avoid_widget: QWidget | None = None,
) -> tuple[str, str]:
    dialog = QFileDialog(None, title, suggested, name_filter)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    dialog.setFileMode(QFileDialog.FileMode.AnyFile)
    if (
        exec_top_level_dialog(dialog, avoid_widget=avoid_widget)
        != QDialog.DialogCode.Accepted
    ):
        return "", ""
    selected = dialog.selectedFiles()
    return (selected[0] if selected else ""), dialog.selectedNameFilter()


def show_message_top_level(
    icon: QMessageBox.Icon,
    title: str,
    text: str,
    *,
    informative_text: str = "",
    avoid_widget: QWidget | None = None,
) -> int:
    box = QMessageBox()
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(text)
    if informative_text:
        box.setInformativeText(informative_text)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    return int(
        exec_top_level_dialog(
            box,
            avoid_widget=avoid_widget,
        )
    )
