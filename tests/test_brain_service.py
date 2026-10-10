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
