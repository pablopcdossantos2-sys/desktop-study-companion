from desktop_study_companion.memory.sqlite_store import SQLiteMemoryStore


def test_conversation_history_persists_and_clears(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "companion.db")
    store.save_conversation_message("user", "Oi")
    store.save_conversation_message("assistant", "Olá")
    store.save_conversation_message("user", "Vamos estudar")

    assert store.load_conversation_messages(limit=2) == [
        ("assistant", "Olá"),
        ("user", "Vamos estudar"),
    ]

    store.clear_conversation_messages()
    assert store.load_conversation_messages() == []
    store.close()
