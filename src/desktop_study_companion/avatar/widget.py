from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWebEngineWidgets import QWebEngineView

from .page import DiagnosticWebPage
from .server import AvatarAssetServer

logger = logging.getLogger("desktop_study_companion.avatar")


class AvatarWidget(QWebEngineView):
    avatar_ready = Signal()
    avatar_failed = Signal(str)
    def __init__(self, renderer_dir: Path, model_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.server = AvatarAssetServer(renderer_dir, model_path)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setPage(DiagnosticWebPage(self))
        self.page().setBackgroundColor(QColor(0, 0, 0, 0))
        self.setStyleSheet("background: transparent;")
        self._url = self.server.start()
        logger.info(
            "Starting avatar renderer url=%s renderer=%s model=%s model_bytes=%s",
            self._url,
            renderer_dir,
            model_path,
            model_path.stat().st_size if model_path.exists() else "missing",
        )
        self.load(QUrl(self._url))
        self._talk_timer = QTimer(self)
        self._talk_timer.setSingleShot(True)
        self._talk_timer.timeout.connect(lambda: self.set_speaking(False))
        self._expression_timer = QTimer(self)
        self._expression_timer.setSingleShot(True)
        self._expression_timer.timeout.connect(
            lambda: self.set_expression("neutral", hold_ms=0)
        )
        self._ready = False
        self._ready_checks = 0
        self._ready_timer = QTimer(self)
        self._ready_timer.setInterval(250)
        self._ready_timeout_checks = 160  # 40 s; first WebEngine/VRM load can be slow.
        self._ready_timer.timeout.connect(self._poll_ready)
        self.loadFinished.connect(self._on_page_loaded)

    def _on_page_loaded(self, ok: bool) -> None:
        logger.info("Avatar renderer page loadFinished ok=%s", ok)
        if not ok:
            reason = "renderer page failed to load"
            logger.error(reason)
            self.avatar_failed.emit(reason)
            return
        self._ready_checks = 0
        self._ready_timer.start()

    def _poll_ready(self) -> None:
        self._ready_checks += 1
        self.page().runJavaScript(
            "({ready:document.body.dataset.ready||'',error:document.body.dataset.error||''})",
            self._handle_ready_state,
        )

    def _handle_ready_state(self, state) -> None:
        if self._ready:
            return
        state = state or {}
        if state.get("ready") == "true":
            self._ready = True
            self._ready_timer.stop()
            logger.info("Avatar renderer reported ready")
            self.page().runJavaScript(
                "window.companionAvatar?.diagnostics?.() ?? {}",
                self._log_renderer_diagnostics,
            )
            self.avatar_ready.emit()
            return
        error = str(state.get("error") or "")
        if error:
            self._ready_timer.stop()
            logger.error("Avatar renderer error: %s", error)
            self.avatar_failed.emit(error)
            return
        if self._ready_checks >= self._ready_timeout_checks:
            self._ready_timer.stop()
            reason = "avatar load timed out"
            logger.error(reason)
            self.page().runJavaScript(
                "window.companionAvatar?.diagnostics?.() ?? {}",
                self._log_renderer_diagnostics,
            )
            self.avatar_failed.emit(reason)

    def _log_renderer_diagnostics(self, diagnostics) -> None:
        logger.info("Avatar renderer diagnostics: %r", diagnostics)
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
        logger.info("Closing avatar renderer")
        self.server.close()
