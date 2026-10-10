from __future__ import annotations

import logging
import platform
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

from desktop_study_companion import __version__
from desktop_study_companion.runtime_paths import (
    application_root,
    avatar_model_path,
    avatar_renderer_directory,
    data_directory,
    external_config_path,
)


_LOGGER_NAME = "desktop_study_companion"
_configured = False
_log_path: Path | None = None


def log_directory() -> Path:
    path = data_directory() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def current_log_path() -> Path:
    global _log_path
    if _log_path is None:
        _log_path = log_directory() / "desktop-study-companion.log"
    return _log_path


def configure_logging() -> Path:
    global _configured
    path = current_log_path()
    if _configured:
        return path

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = RotatingFileHandler(
        path,
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | "
            "%(threadName)s | %(message)s"
        )
    )
    root.addHandler(handler)
    _configured = True

    logger = logging.getLogger(_LOGGER_NAME)
    logger.info("=== Desktop Study Companion starting ===")
    logger.info("version=%s", __version__)
    logger.info("python=%s", sys.version.replace("\n", " "))
    logger.info("platform=%s", platform.platform())
    logger.info("frozen=%s", bool(getattr(sys, "frozen", False)))
    logger.info("application_root=%s", application_root())
    logger.info("log_path=%s", path)

    return path


def install_exception_hooks() -> None:
    logger = logging.getLogger(f"{_LOGGER_NAME}.crash")
    previous = sys.excepthook

    def sys_hook(exc_type, exc_value, traceback) -> None:
        logger.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, traceback),
        )
        previous(exc_type, exc_value, traceback)

    sys.excepthook = sys_hook

    previous_thread = threading.excepthook

    def thread_hook(args: threading.ExceptHookArgs) -> None:
        logger.critical(
            "Unhandled thread exception in %s",
            getattr(args.thread, "name", "<unknown>"),
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )
        previous_thread(args)

    threading.excepthook = thread_hook


def install_qt_message_logging() -> None:
    try:
        from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    except Exception:
        return

    logger = logging.getLogger(f"{_LOGGER_NAME}.qt")

    def handler(msg_type, context, message) -> None:
        source = ""
        if context is not None:
            file_name = getattr(context, "file", None)
            line = getattr(context, "line", None)
            if file_name:
                source = f" [{file_name}:{line}]"

        if msg_type == QtMsgType.QtDebugMsg:
            logger.debug("%s%s", message, source)
        elif msg_type == QtMsgType.QtInfoMsg:
            logger.info("%s%s", message, source)
        elif msg_type == QtMsgType.QtWarningMsg:
            logger.warning("%s%s", message, source)
        elif msg_type == QtMsgType.QtCriticalMsg:
            logger.error("%s%s", message, source)
        elif msg_type == QtMsgType.QtFatalMsg:
            logger.critical("%s%s", message, source)
        else:
            logger.info("%s%s", message, source)

    qInstallMessageHandler(handler)


def diagnostic_summary() -> str:
    model = avatar_model_path()
    renderer = avatar_renderer_directory()
    renderer_index = renderer / "index.html"

    def describe(path: Path) -> str:
        if not path.exists():
            return f"{path} [AUSENTE]"
        if path.is_file():
            return f"{path} [{path.stat().st_size} bytes]"
        return f"{path} [presente]"

    return "\n".join(
        [
            f"Desktop Study Companion {__version__}",
            f"Python: {sys.version.split()[0]}",
            f"Windows/plataforma: {platform.platform()}",
            f"Frozen/portátil: {bool(getattr(sys, 'frozen', False))}",
            f"Raiz: {application_root()}",
            f"Config: {external_config_path()}",
            f"Log atual: {current_log_path()}",
            f"Avatar VRM: {describe(model)}",
            f"Renderer: {describe(renderer_index)}",
        ]
    )
