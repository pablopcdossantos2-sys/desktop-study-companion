from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

logger = logging.getLogger("desktop_study_companion.brain.worker")

from .service import BrainService


class BrainWorkerSignals(QObject):
    succeeded = Signal(str)
    failed = Signal(str)


class BrainChatWorker(QRunnable):
    def __init__(
        self,
        service: BrainService,
        user_text: str,
        session_context: dict,
    ) -> None:
        super().__init__()
        self.service = service
        self.user_text = user_text
        self.session_context = session_context
        self.signals = BrainWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            answer = self.service.chat(
                self.user_text,
                self.session_context,
            )
        except Exception as exc:
            logger.exception("Brain chat worker failed")
            self.signals.failed.emit(str(exc))
            return
        self.signals.succeeded.emit(answer)
