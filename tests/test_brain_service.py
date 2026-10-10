from desktop_study_companion.brain.service import BrainService
from desktop_study_companion.config.models import AppConfig
from desktop_study_companion.memory.analytics import StudyAnalytics
from desktop_study_companion.memory.sqlite_store import SQLiteMemoryStore


class FakeProvider:
    def chat(self, *, system_prompt, messages):
        assert "Sessão de estudo" in system_prompt
        assert messages[-1].content == "Oi"
        return "Olá. Vamos estudar."


def test_brain_service_saves_successful_exchange(tmp_path, monkeypatch) -> None:
    db = tmp_path / "companion.db"
    memory = SQLiteMemoryStore(db)
    config = AppConfig()
    config.brain.enabled = True
    config.brain.model = "fake"
    service = BrainService(config, memory, StudyAnalytics(db))

    monkeypatch.setattr(service, "_provider", lambda: FakeProvider())

    answer = service.chat("Oi", {"active": False})

    assert answer == "Olá. Vamos estudar."
    assert memory.load_conversation_messages() == [
        ("user", "Oi"),
        ("assistant", "Olá. Vamos estudar."),
    ]
    memory.close()



def test_brain_service_uses_native_ollama_for_default_local_endpoint(
    tmp_path,
) -> None:
    from desktop_study_companion.brain.provider import OllamaNativeProvider

    db = tmp_path / "companion.db"
    memory = SQLiteMemoryStore(db)
    config = AppConfig()
    config.brain.enabled = True
    config.brain.base_url = "http://127.0.0.1:11434/v1"
    config.brain.model = "qwen3:4b"
    service = BrainService(config, memory, StudyAnalytics(db))

    provider = service._provider()

    assert isinstance(provider, OllamaNativeProvider)
    assert provider.endpoint == "http://127.0.0.1:11434/api/chat"
    memory.close()
