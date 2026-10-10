from __future__ import annotations

import logging
import os
import platform
import sys

# Transparent always-on-top QWebEngine windows can be considered occluded by
# Chromium and have their renderer/timers backgrounded. Keep this tiny avatar
# surface active even when another window overlaps it.
_existing_chromium_flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "").strip()
_required_chromium_flags = (
    "--disable-background-timer-throttling "
    "--disable-backgrounding-occluded-windows "
    "--disable-renderer-backgrounding"
)
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    f"{_existing_chromium_flags} {_required_chromium_flags}".strip()
)

from PySide6.QtWidgets import QApplication, QMessageBox

from desktop_study_companion.config.loader import load_config
from desktop_study_companion.diagnostics import (
    configure_logging,
    install_exception_hooks,
    install_qt_message_logging,
)
from desktop_study_companion.controller import ApplicationController


def main() -> int:
    configure_logging()
    install_exception_hooks()
    install_qt_message_logging()
    logger = logging.getLogger("desktop_study_companion.app")

    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Study Companion")
    app.setQuitOnLastWindowClosed(False)

    if platform.system() != "Windows":
        QMessageBox.critical(
            None,
            "Plataforma não suportada",
            "A v0.1 é destinada ao Windows 10/11. "
            "O monitor de janela ativa ainda não possui implementação para este sistema.",
        )
        return 2

    try:
        logger.info("Loading configuration")
        config = load_config()
        controller = ApplicationController(app, config)
        # Keep a strong reference for the whole Qt event loop.
        app._desktop_study_controller = controller  # type: ignore[attr-defined]
        controller.start()
        return app.exec()
    except Exception as exc:
        logger.exception("Fatal application startup/runtime error")
        QMessageBox.critical(
            None,
            "Falha ao iniciar",
            f"O Desktop Study Companion não conseguiu iniciar:\n\n{exc}",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
