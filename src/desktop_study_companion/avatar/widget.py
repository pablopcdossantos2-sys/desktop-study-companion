from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, QUrl, Qt
from PySide6.QtGui import QColor
from PySide6.QtWebEngineWidgets import QWebEngineView

from .server import AvatarAssetServer


class AvatarWidget(QWebEngineView):
    def __init__(self, renderer_dir: Path, model_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.server = AvatarAssetServer(renderer_dir, model_path)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.page().setBackgroundColor(QColor(0, 0, 0, 0))
        self.setStyleSheet("background: transparent;")
        self.load(QUrl(self.server.start()))
        self._talk_timer = QTimer(self)
        self._talk_timer.setSingleShot(True)
        self._talk_timer.timeout.connect(lambda: self.set_speaking(False))

    def js(self, code: str) -> None:
        self.page().runJavaScript(code)

    def set_expression(self, name: str, weight: float = 1.0) -> None:
        safe = name.replace("'", "")
        self.js(
            f"window.companionAvatar?.setExpression('{safe}', {float(weight)});"
        )

    def set_speaking(self, speaking: bool) -> None:
        self.js(
            f"window.companionAvatar?.setSpeaking({str(bool(speaking)).lower()});"
        )

    def talk_for_text(self, text: str) -> None:
        self.set_speaking(True)
        duration_ms = max(900, min(12000, int(len(text) / 13 * 1000)))
        self._talk_timer.start(duration_ms)

    def close_avatar(self) -> None:
        self.server.close()
