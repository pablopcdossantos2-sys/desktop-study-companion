from __future__ import annotations

import queue
import threading
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _SpeechItem:
    text: str
    generation: int


@dataclass(frozen=True, slots=True)
class SapiVoice:
    token_id: str
    name: str


def list_sapi_voices() -> list[SapiVoice]:
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        voices = speaker.GetVoices()
        result: list[SapiVoice] = []
        for index in range(voices.Count):
            token = voices.Item(index)
            result.append(
                SapiVoice(
                    token_id=str(token.Id),
                    name=str(token.GetDescription()),
                )
            )
        return result
    finally:
        pythoncom.CoUninitialize()


class WindowsSapiTTS:
    """Non-blocking wrapper around the speech engine built into Windows."""

    def __init__(
        self,
        rate: int = 0,
        volume: int = 90,
        voice_token_id: str = "",
    ) -> None:
        self.rate = max(-10, min(10, rate))
        self.volume = max(0, min(100, volume))
        self.voice_token_id = voice_token_id.strip()
        self._queue: queue.Queue[_SpeechItem | None] = queue.Queue(maxsize=8)
        self._closed = False
        self._interrupt = threading.Event()
        self._generation_lock = threading.Lock()
        self._generation = 0
        self._speaking = threading.Event()
        self._thread = threading.Thread(
            target=self._worker,
            name="desktop-study-companion-tts",
            daemon=True,
        )
        self._thread.start()

    def speak(self, text: str) -> None:
        text = text.strip()
        if not text or self._closed:
            return
        with self._generation_lock:
            item = _SpeechItem(text, self._generation)
        try:
            self._queue.put_nowait(item)
        except queue.Full:
            try:
                dropped = self._queue.get_nowait()
                if dropped is not None:
                    self._queue.task_done()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(item)
            except queue.Full:
                pass

    def _worker(self) -> None:
        # COM must be initialized inside the thread that uses the SAPI object.
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        try:
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Rate = self.rate
            speaker.Volume = self.volume
            if self.voice_token_id:
                voices = speaker.GetVoices()
                for index in range(voices.Count):
                    token = voices.Item(index)
                    if str(token.Id) == self.voice_token_id:
                        speaker.Voice = token
                        break

            while True:
                item = self._queue.get()
                if item is None:
                    return
                try:
                    with self._generation_lock:
                        if item.generation != self._generation:
                            continue
                        self._interrupt.clear()
                        self._speaking.set()
                    speaker.Speak(item.text, 1)
                    while not speaker.WaitUntilDone(50):
                        if self._interrupt.is_set():
                            speaker.Speak("", 3)
                            break
                finally:
                    self._speaking.clear()
                    with self._generation_lock:
                        if item.generation == self._generation:
                            self._interrupt.clear()
                    self._queue.task_done()
        finally:
            pythoncom.CoUninitialize()

    @property
    def is_speaking(self) -> bool:
        return self._speaking.is_set()

    def stop(self) -> None:
        if self._closed:
            return
        with self._generation_lock:
            self._generation += 1
            self._interrupt.set()
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            if item is not None:
                self._queue.task_done()

    def close(self) -> None:
        if self._closed:
            return
        self.stop()
        self._closed = True
        self._queue.put(None)
