from __future__ import annotations

import os

from desktop_study_companion.brain.prompt import build_system_prompt
from desktop_study_companion.brain.provider import (
    BrainError,
    ChatMessage,
    OllamaNativeProvider,
    OpenAICompatibleProvider,
    is_local_ollama_base_url,
)
from desktop_study_companion.config.models import AppConfig
from desktop_study_companion.memory.analytics import StudyAnalytics
from desktop_study_companion.memory.sqlite_store import SQLiteMemoryStore


class BrainService:
    def __init__(
        self,
        config: AppConfig,
        memory: SQLiteMemoryStore,
        analytics: StudyAnalytics,
    ) -> None:
        self.config = config
        self.memory = memory
        self.analytics = analytics

    @property
    def ready(self) -> bool:
        brain = self.config.brain
        return bool(
            brain.enabled
            and brain.base_url.strip()
            and brain.model.strip()
        )

    def _provider(self):
        brain = self.config.brain

        if is_local_ollama_base_url(brain.base_url):
            return OllamaNativeProvider(
                base_url=brain.base_url,
                model=brain.model,
                temperature=brain.temperature,
                max_tokens=brain.max_tokens,
                timeout_seconds=brain.timeout_seconds,
                retries=1,
            )

        api_key = ""
        if brain.api_key_env.strip():
            api_key = os.environ.get(brain.api_key_env.strip(), "")

        return OpenAICompatibleProvider(
            base_url=brain.base_url,
            model=brain.model,
            api_key=api_key,
            temperature=brain.temperature,
            max_tokens=brain.max_tokens,
            timeout_seconds=brain.timeout_seconds,
            retries=1,
        )

    def chat(self, user_text: str, session_context: dict) -> str:
        user_text = user_text.strip()
        if not user_text:
            raise BrainError("empty user message")
        if not self.ready:
            raise BrainError("conversational brain is not configured")

        history = [
            ChatMessage(role=role, content=content)
            for role, content in self.memory.load_conversation_messages(
                limit=self.config.brain.history_messages
            )
        ]
        history.append(ChatMessage(role="user", content=user_text))

        system_prompt = build_system_prompt(
            self.config,
            self.analytics.to_context_dict(30),
            session_context,
        )
        answer = self._provider().chat(
            system_prompt=system_prompt,
            messages=history,
        )

        self.memory.save_conversation_message("user", user_text)
        self.memory.save_conversation_message("assistant", answer)
        return answer

    def clear_history(self) -> None:
        self.memory.clear_conversation_messages()

    def update_config(self, config: AppConfig) -> None:
        self.config = config
