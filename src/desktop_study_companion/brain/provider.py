from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Sequence


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_CONTROL_TAG_RE = re.compile(
    r"\[(?:DESKTOP|ACTION|SYSTEM|TOOL):[^\]]*\]",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str
    content: str


class BrainError(RuntimeError):
    pass


def sanitize_assistant_text(text: str) -> str:
    """Make LLM output inert before it reaches UI/TTS.

    Desktop Study Companion never interprets model output as commands.
    Removing command-looking tags also prevents a model from misleading the
    user into thinking it executed an action.
    """
    text = _THINK_RE.sub("", text)
    lower = text.lower()
    if "<think>" in lower and "</think>" not in lower:
        text = text[: lower.rfind("<think>")]
    text = _CONTROL_TAG_RE.sub("", text)
    return " ".join(text.split()).strip()


class OpenAICompatibleProvider:
    """Minimal /v1/chat/completions client with no tool support."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str = "",
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout_seconds: int = 45,
        retries: int = 1,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.api_key = api_key.strip()
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.timeout_seconds = int(timeout_seconds)
        self.retries = max(0, int(retries))

        if not self.base_url:
            raise ValueError("brain base_url cannot be empty")
        if not self.model:
            raise ValueError("brain model cannot be empty")

    @property
    def endpoint(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    def chat(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *[
                    {"role": message.role, "content": message.content}
                    for message in messages
                ],
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers=headers,
            method="POST",
        )

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.timeout_seconds,
                ) as response:
                    raw = response.read()
                data = json.loads(raw.decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                cleaned = sanitize_assistant_text(str(text or ""))
                if not cleaned:
                    raise BrainError("the model returned an empty response")
                return cleaned
            except (
                urllib.error.HTTPError,
                urllib.error.URLError,
                TimeoutError,
                OSError,
                KeyError,
                IndexError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                break

        raise BrainError(f"brain request failed: {last_error}")
