from __future__ import annotations

import queue
import threading
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _SpeechItem:
    text: str


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
        self._queue: queue.Queue[_SpeechItem | None] = queue.Queue()
        self._closed = False
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
        self._queue.put(_SpeechItem(text))

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
                    speaker.Speak(item.text)
                finally:
                    self._queue.task_done()
        finally:
            pythoncom.CoUninitialize()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._queue.put(None)
