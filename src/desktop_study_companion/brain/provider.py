from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Sequence
from urllib.parse import urlparse, urlunparse


logger = logging.getLogger("desktop_study_companion.brain.provider")

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
    """Make LLM output inert before it reaches UI/TTS."""
    text = _THINK_RE.sub("", text)
    lower = text.lower()
    if "<think>" in lower and "</think>" not in lower:
        text = text[: lower.rfind("<think>")]
    text = _CONTROL_TAG_RE.sub("", text)
    return " ".join(text.split()).strip()


def looks_like_reasoning_leak(text: str) -> bool:
    sample = " ".join(text.strip().split()).casefold()
    if not sample:
        return False
    markers = (
        "okay, the user",
        "the user said",
        "let me break",
        "i need to recall",
        "i need to respond",
        "the rules say",
        "my response should",
        "first, i need to",
        "wait, but",
    )
    hits = sum(marker in sample for marker in markers)
    return hits >= 2 or sample.startswith(("okay, the user", "the user said"))


def _message_content_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                value = item.get("text")
                if isinstance(value, str):
                    parts.append(value)
        return " ".join(parts)
    return str(content or "")


def is_local_ollama_base_url(base_url: str) -> bool:
    """Recognize the default local Ollama server used by our tutorial."""
    try:
        parsed = urlparse(base_url)
    except ValueError:
        return False
    host = (parsed.hostname or "").casefold()
    return (
        parsed.scheme in {"http", "https"}
        and host in {"127.0.0.1", "localhost", "::1"}
        and parsed.port == 11434
    )


def ollama_native_endpoint(base_url: str) -> str:
    parsed = urlparse(base_url)
    return urlunparse(
        (
            parsed.scheme or "http",
            parsed.netloc,
            "/api/chat",
            "",
            "",
            "",
        )
    )


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
                logger.info(
                    "Brain request provider=openai-compatible model=%s endpoint=%s",
                    self.model,
                    self.endpoint,
                )
                with urllib.request.urlopen(
                    request,
                    timeout=self.timeout_seconds,
                ) as response:
                    raw = response.read()
                data = json.loads(raw.decode("utf-8"))
                choice = data["choices"][0]
                message = choice["message"]
                text = _message_content_text(message.get("content"))
                cleaned = sanitize_assistant_text(text)
                if looks_like_reasoning_leak(cleaned):
                    logger.error(
                        "Blocked reasoning-like model output provider=openai-compatible model=%s",
                        self.model,
                    )
                    raise BrainError(
                        "o modelo devolveu raciocínio interno em vez da resposta final; "
                        "o conteúdo foi bloqueado por segurança. Tente novamente ou use "
                        "um modelo em modo não-thinking."
                    )
                if not cleaned:
                    reasoning_present = bool(
                        message.get("reasoning")
                        or message.get("reasoning_content")
                        or "<think>" in text.lower()
                    )
                    logger.warning(
                        "Brain returned no final content provider=%s model=%s "
                        "finish_reason=%r reasoning_present=%s",
                        "openai-compatible",
                        self.model,
                        choice.get("finish_reason"),
                        reasoning_present,
                    )
                    raise BrainError(
                        "o modelo não retornou uma resposta final. "
                        "Se estiver usando Ollama local, use o endereço padrão "
                        "http://127.0.0.1:11434/v1 para que o aplicativo use "
                        "automaticamente o modo nativo sem thinking."
                    )
                logger.info(
                    "Brain response succeeded provider=openai-compatible "
                    "model=%s chars=%s",
                    self.model,
                    len(cleaned),
                )
                return cleaned
            except BrainError:
                raise
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
                logger.warning(
                    "Brain request attempt failed provider=openai-compatible "
                    "model=%s attempt=%s error=%s",
                    self.model,
                    attempt + 1,
                    exc,
                )
                if attempt < self.retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                break

        raise BrainError(f"falha na consulta ao cérebro: {last_error}")


class OllamaNativeProvider:
    """Ollama /api/chat client with reasoning disabled."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout_seconds: int = 45,
        retries: int = 1,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.timeout_seconds = int(timeout_seconds)
        self.retries = max(0, int(retries))

        if not self.model:
            raise ValueError("brain model cannot be empty")

    @property
    def endpoint(self) -> str:
        return ollama_native_endpoint(self.base_url)

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
            "stream": False,
            "think": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                logger.info(
                    "Brain request provider=ollama-native model=%s endpoint=%s",
                    self.model,
                    self.endpoint,
                )
                with urllib.request.urlopen(
                    request,
                    timeout=self.timeout_seconds,
                ) as response:
                    raw = response.read()
                data = json.loads(raw.decode("utf-8"))
                message = data["message"]
                text = _message_content_text(message.get("content"))
                cleaned = sanitize_assistant_text(text)
                if looks_like_reasoning_leak(cleaned):
                    logger.error(
                        "Blocked reasoning-like Ollama output model=%s",
                        self.model,
                    )
                    raise BrainError(
                        "o modelo local devolveu raciocínio interno; a resposta "
                        "foi bloqueada. Atualize o Ollama ou tente novamente."
                    )
                if not cleaned:
                    logger.warning(
                        "Ollama returned no final content model=%s "
                        "done_reason=%r thinking_present=%s",
                        self.model,
                        data.get("done_reason"),
                        bool(message.get("thinking")),
                    )
                    raise BrainError(
                        "Ollama não retornou uma resposta final. "
                        "Atualize o Ollama e confirme se o modelo configurado "
                        f"({self.model}) responde no comando 'ollama run'."
                    )
                logger.info(
                    "Brain response succeeded provider=ollama-native "
                    "model=%s chars=%s",
                    self.model,
                    len(cleaned),
                )
                return cleaned
            except BrainError:
                raise
            except (
                urllib.error.HTTPError,
                urllib.error.URLError,
                TimeoutError,
                OSError,
                KeyError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ) as exc:
                last_error = exc
                logger.warning(
                    "Brain request attempt failed provider=ollama-native "
                    "model=%s attempt=%s error=%s",
                    self.model,
                    attempt + 1,
                    exc,
                )
                if attempt < self.retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                break

        raise BrainError(f"falha na consulta ao Ollama: {last_error}")
