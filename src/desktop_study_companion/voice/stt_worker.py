from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("desktop_study_companion.voice.stt_worker")

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from .faster_whisper_stt import FasterWhisperSTT


class SttWorkerSignals(QObject):
    succeeded = Signal(str)
    failed = Signal(str)


class SttWorker(QRunnable):
    def __init__(
        self,
        provider: FasterWhisperSTT,
        audio_path: str | Path,
    ) -> None:
        super().__init__()
        self.provider = provider
        self.audio_path = Path(audio_path)
        self.signals = SttWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            text = self.provider.transcribe_file(self.audio_path)
        except Exception as exc:
            logger.exception(
                "STT worker failed audio=%s",
                self.audio_path.name,
            )
            self.signals.failed.emit(str(exc))
        else:
            self.signals.succeeded.emit(text)
        finally:
            self.audio_path.unlink(missing_ok=True)
