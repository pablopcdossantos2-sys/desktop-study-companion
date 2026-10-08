from __future__ import annotations

from typing import Protocol


class TextToSpeech(Protocol):
    def speak(self, text: str) -> None: ...


class SpeechToText(Protocol):
    def listen_once(self) -> str: ...
