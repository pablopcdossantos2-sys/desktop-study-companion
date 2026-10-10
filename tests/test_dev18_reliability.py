import json

from desktop_study_companion.accountability.directives import DirectiveManager
from desktop_study_companion.config.loader import load_config
from desktop_study_companion.memory.exporter import _csv_safe
from desktop_study_companion.memory.sqlite_store import SQLiteMemoryStore
from desktop_study_companion.study.models import StudySession, StudyState


def test_corrupt_directive_json_is_quarantined_before_new_save(tmp_path) -> None:
    path = tmp_path / "directives.json"
    path.write_text('[{"goal":"importante"', encoding="utf-8")

    manager = DirectiveManager(path)
    assert manager.directives == []
    backups = list(tmp_path.glob("directives.json.bak*"))
    assert backups

    manager.add("novo compromisso", 5, delay_seconds=0)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data[0]["goal"] == "novo compromisso"
    assert "importante" in backups[0].read_text(encoding="utf-8")


def test_malformed_json_items_do_not_crash_manager(tmp_path) -> None:
    path = tmp_path / "directives.json"
    path.write_text(
        json.dumps([
            {"goal": "válido", "urgency": 5},
            "inválido",
            {"goal": "urgência ruim", "urgency": "alta"},
        ]),
        encoding="utf-8",
    )
    manager = DirectiveManager(path)
    assert [item.goal for item in manager.directives] == ["válido"]


def test_config_ignores_unknown_keys_and_empty_keywords(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps({
            "future_root_key": True,
            "monitor": {"poll_interval_ms": 1000, "future_key": 123},
            "activity": {"distraction_keywords": ["", "  ", "youtube"]},
        }),
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.monitor.poll_interval_ms == 1000
    assert config.activity.distraction_keywords == ["youtube"]


def test_csv_formula_prefix_is_neutralized() -> None:
    assert _csv_safe('=HYPERLINK("http://evil","x")').startswith("'=")
    assert _csv_safe("+1+1") == "'+1+1"
    assert _csv_safe("normal") == "normal"


def test_orphaned_active_session_is_reconciled(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    try:
        session = StudySession("Teste", 10)
        session.start()
        store.save_session(session)
        assert store.reconcile_orphaned_sessions() == 1
        row = store.connection.execute(
            "SELECT state, ended_at FROM study_sessions WHERE id = ?",
            (session.id,),
        ).fetchone()
        assert row[0] == StudyState.ABANDONED.value
        assert row[1]
    finally:
        store.close()
