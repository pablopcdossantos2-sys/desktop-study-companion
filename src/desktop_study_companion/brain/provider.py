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
    """Ollama /api/chat client with reasoning disabled and safe retry."""

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

    def _outgoing_messages(
        self,
        system_prompt: str,
        messages: Sequence[ChatMessage],
        *,
        strict_retry: bool = False,
    ) -> list[dict[str, str]]:
        system_suffix = (
            "\n\nMODO DE RESPOSTA: não use raciocínio visível. "
            "Produza somente a resposta final em português do Brasil.\n/no_think"
        )
        outgoing = [
            {
                "role": "system",
                "content": system_prompt.rstrip() + system_suffix,
            }
        ]

        last_user_index = -1
        for index, message in enumerate(messages):
            if message.role == "user":
                last_user_index = index

        for index, message in enumerate(messages):
            content = message.content
            if index == last_user_index and message.role == "user":
                suffix = (
                    "\n\n/no_think\n"
                    "Responda diretamente, em português do Brasil, "
                    "somente com a mensagem final."
                )
                if strict_retry:
                    suffix += (
                        " Não descreva análise, regras, planejamento, "
                        "raciocínio ou o que você pretende responder."
                    )
                content = content.rstrip() + suffix
            outgoing.append({"role": message.role, "content": content})

        return outgoing

    def _request_once(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
        strict_retry: bool = False,
    ) -> tuple[str, dict]:
        payload = {
            "model": self.model,
            "messages": self._outgoing_messages(
                system_prompt,
                messages,
                strict_retry=strict_retry,
            ),
            "stream": False,
            "think": False,
            "options": {
                "temperature": (
                    min(self.temperature, 0.3)
                    if strict_retry
                    else self.temperature
                ),
                "num_predict": self.max_tokens,
            },
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        logger.info(
            "Brain request provider=ollama-native model=%s endpoint=%s "
            "strict_retry=%s",
            self.model,
            self.endpoint,
            strict_retry,
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

        # A compliant recent Ollama/Qwen3 combination puts chain-of-thought in
        # message.thinking when thinking is enabled and keeps content final-only.
        # We never surface or log that field's contents.
        if message.get("thinking"):
            logger.warning(
                "Ollama returned a thinking field despite think=false "
                "model=%s chars=%s",
                self.model,
                len(str(message.get("thinking") or "")),
            )

        return cleaned, data

    def chat(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
    ) -> str:
        last_error: Exception | None = None

        for attempt in range(self.retries + 1):
            try:
                cleaned, data = self._request_once(
                    system_prompt=system_prompt,
                    messages=messages,
                    strict_retry=False,
                )

                if cleaned and not looks_like_reasoning_leak(cleaned):
                    logger.info(
                        "Brain response succeeded provider=ollama-native "
                        "model=%s chars=%s",
                        self.model,
                        len(cleaned),
                    )
                    return cleaned

                reason = (
                    "reasoning-like content"
                    if looks_like_reasoning_leak(cleaned)
                    else "empty final content"
                )
                logger.warning(
                    "Ollama response unusable model=%s reason=%s "
                    "done_reason=%r",
                    self.model,
                    reason,
                    data.get("done_reason"),
                )

                # Retry the original user request, not the leaked text. This
                # avoids feeding hidden/reasoning content back into the model.
                retry_cleaned, retry_data = self._request_once(
                    system_prompt=system_prompt,
                    messages=messages,
                    strict_retry=True,
                )
                if (
                    retry_cleaned
                    and not looks_like_reasoning_leak(retry_cleaned)
                ):
                    logger.info(
                        "Brain response recovered on strict no-think retry "
                        "model=%s chars=%s",
                        self.model,
                        len(retry_cleaned),
                    )
                    return retry_cleaned

                logger.error(
                    "Ollama still returned unusable output after no-think "
                    "retry model=%s done_reason=%r",
                    self.model,
                    retry_data.get("done_reason"),
                )
                raise BrainError(
                    "o modelo local continuou retornando raciocínio em vez "
                    "da resposta final. Para uma conversa mais estável, use "
                    "o modelo não-thinking 'qwen3:4b-instruct'."
                )
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
