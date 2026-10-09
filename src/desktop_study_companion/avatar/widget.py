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
        self._expression_timer = QTimer(self)
        self._expression_timer.setSingleShot(True)
        self._expression_timer.timeout.connect(
            lambda: self.set_expression("neutral", hold_ms=0)
        )

    def js(self, code: str) -> None:
        self.page().runJavaScript(code)

    def set_expression(
        self,
        name: str,
        weight: float = 1.0,
        *,
        hold_ms: int = 3500,
    ) -> None:
        safe = name.replace("'", "")
        self.js(
            f"window.companionAvatar?.setExpression('{safe}', {float(weight)});"
        )
        self._expression_timer.stop()
        if safe != "neutral" and hold_ms > 0:
            self._expression_timer.start(max(250, int(hold_ms)))

    def set_look(self, x: float, y: float) -> None:
        x = max(-1.0, min(1.0, float(x)))
        y = max(-1.0, min(1.0, float(y)))
        self.js(f"window.companionAvatar?.setLook({x}, {y});")

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
