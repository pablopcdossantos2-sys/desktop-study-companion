from __future__ import annotations

import logging

from PySide6.QtWebEngineCore import QWebEnginePage


class DiagnosticWebPage(QWebEnginePage):
    """QWebEngine page that mirrors JavaScript console output into app logs."""

    def javaScriptConsoleMessage(
        self,
        level,
        message: str,
        line_number: int,
        source_id: str,
    ) -> None:
        logger = logging.getLogger("desktop_study_companion.avatar.js")
        prefix = f"{source_id or '<renderer>'}:{line_number}"

        # Qt exposes enum values here, but comparing their string form keeps
        # this code compatible across minor PySide6 versions.
        level_name = str(level).casefold()
        if "error" in level_name:
            logger.error("%s | %s", prefix, message)
        elif "warning" in level_name:
            logger.warning("%s | %s", prefix, message)
        else:
            logger.info("%s | %s", prefix, message)

        super().javaScriptConsoleMessage(
            level,
            message,
            line_number,
            source_id,
        )
