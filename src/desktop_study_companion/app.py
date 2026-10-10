from __future__ import annotations

import logging
import os
import platform
import sys


def _maybe_run_piper_worker() -> None:
    """Dispatch the frozen executable into a Piper-only helper process."""
    if "--piper-worker" not in sys.argv:
        return
    index = sys.argv.index("--piper-worker")
    from desktop_study_companion.voice.piper_worker import main as piper_worker_main

    raise SystemExit(piper_worker_main(sys.argv[index + 1 :]))


_maybe_run_piper_worker()

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

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox

from desktop_study_companion.config.loader import load_config_with_recovery
from desktop_study_companion.diagnostics import (
    configure_logging,
    install_exception_hooks,
    install_native_fault_handler,
    install_qt_message_logging,
    mark_run_clean,
    mark_run_started,
)
from desktop_study_companion.controller import ApplicationController
from desktop_study_companion.runtime_paths import data_directory


def main() -> int:
    configure_logging()
    install_exception_hooks()
    install_native_fault_handler()
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

    lock = QLockFile(str(data_directory() / "desktop-study-companion.lock"))
    if not lock.tryLock(100):
        QMessageBox.information(
            None,
            "Desktop Study Companion já está aberto",
            "Já existe uma instância em execução. Use a janela que já está aberta.",
        )
        return 0

    previous_unclean = mark_run_started()
    app.aboutToQuit.connect(mark_run_clean)

    try:
        logger.info("Loading configuration")
        config, recovery_notice, recovery_state = load_config_with_recovery(
            include_state=True
        )
        controller = ApplicationController(
            app,
            config,
            config_recovery_state=recovery_state,
        )
        # Keep a strong reference for the whole Qt event loop.
        app._desktop_study_controller = controller  # type: ignore[attr-defined]
        controller.start()
        if recovery_notice:
            QMessageBox.warning(
                controller.widget,
                "Configuração recuperada",
                recovery_notice,
            )
        if previous_unclean:
            logger.warning(
                "The previous execution ended without a clean shutdown marker. "
                "See desktop-study-companion-fatal.log and the rotating log."
            )
        exit_code = app.exec()
        logger.info("Qt event loop exited code=%s", exit_code)
        mark_run_clean()
        return exit_code
    except Exception as exc:
        logger.exception("Fatal application startup/runtime error")
        QMessageBox.critical(
            None,
            "Falha ao iniciar",
            f"O Desktop Study Companion não conseguiu iniciar:\n\n{exc}",
        )
        mark_run_clean()
        return 1
    finally:
        lock.unlock()


if __name__ == "__main__":
    raise SystemExit(main())
