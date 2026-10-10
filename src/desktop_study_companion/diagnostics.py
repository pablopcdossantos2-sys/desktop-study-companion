from __future__ import annotations

import faulthandler
import importlib.metadata
import json
import logging
import os
import platform
import sys
import threading
from datetime import datetime, timezone
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
_fault_log_handle = None


def log_directory() -> Path:
    path = data_directory() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def current_log_path() -> Path:
    global _log_path
    if _log_path is None:
        _log_path = log_directory() / "desktop-study-companion.log"
    return _log_path


def native_fault_log_path() -> Path:
    return log_directory() / "desktop-study-companion-fatal.log"


def run_state_path() -> Path:
    return log_directory() / "run-state.json"


def install_native_fault_handler() -> Path:
    """Persist Python/native fatal fault traces when the process dies abruptly."""
    global _fault_log_handle
    path = native_fault_log_path()
    if _fault_log_handle is not None:
        return path

    try:
        _fault_log_handle = path.open("a", encoding="utf-8", buffering=1)
        faulthandler.enable(file=_fault_log_handle, all_threads=True)
        logging.getLogger(_LOGGER_NAME).info(
            "Native fault handler enabled path=%s",
            path,
        )
    except Exception:
        logging.getLogger(_LOGGER_NAME).exception(
            "Could not enable native fault handler"
        )
    return path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def mark_run_started() -> bool:
    """Mark this run as active and report whether the previous run was unclean."""
    path = run_state_path()
    previous_unclean = False
    previous = {}
    try:
        if path.exists():
            previous = json.loads(path.read_text(encoding="utf-8"))
            previous_unclean = previous.get("clean_exit") is False
    except Exception:
        logging.getLogger(_LOGGER_NAME).exception(
            "Could not read previous run state"
        )

    payload = {
        "version": __version__,
        "pid": os.getpid(),
        "started_at": _utc_now(),
        "clean_exit": False,
    }
    try:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        logging.getLogger(_LOGGER_NAME).exception(
            "Could not write run state"
        )

    if previous_unclean:
        logging.getLogger(_LOGGER_NAME).warning(
            "Previous run did not record a clean exit: %r",
            previous,
        )
    return previous_unclean


def mark_run_clean() -> None:
    path = run_state_path()
    payload = {}
    try:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}

    payload.update(
        {
            "version": __version__,
            "pid": os.getpid(),
            "clean_exit": True,
            "ended_at": _utc_now(),
        }
    )
    try:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        logging.getLogger(_LOGGER_NAME).exception(
            "Could not mark run as cleanly finished"
        )


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

    # Keep third-party network/download chatter from drowning out application
    # diagnostics. Warnings and errors remain visible.
    for noisy_logger in (
        "httpcore",
        "httpcore2",
        "httpx",
        "httpx2",
        "filelock",
        "huggingface_hub",
    ):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    _configured = True

    logger = logging.getLogger(_LOGGER_NAME)
    logger.info("=== Desktop Study Companion starting ===")
    logger.info("version=%s", __version__)
    logger.info("python=%s", sys.version.replace("\n", " "))
    logger.info("platform=%s", platform.platform())
    logger.info("frozen=%s", bool(getattr(sys, "frozen", False)))
    logger.info("application_root=%s", application_root())
    logger.info("log_path=%s", path)
    for package in ("PySide6", "faster-whisper", "av"):
        try:
            logger.info(
                "dependency %s=%s",
                package,
                importlib.metadata.version(package),
            )
        except importlib.metadata.PackageNotFoundError:
            logger.info("dependency %s=not-installed", package)

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


def _package_exists(package: str) -> bool:
    try:
        importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


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
            f"Falhas nativas: {native_fault_log_path()}",
            f"Estado da execução: {run_state_path()}",
            "Dependências: "
            + ", ".join(
                f"{package}="
                + (
                    importlib.metadata.version(package)
                    if _package_exists(package)
                    else "não instalado"
                )
                for package in ("PySide6", "faster-whisper", "av")
            ),
            f"Avatar VRM: {describe(model)}",
            f"Renderer: {describe(renderer_index)}",
        ]
    )
