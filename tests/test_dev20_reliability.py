import json
from pathlib import Path

from desktop_study_companion.accountability.directives import DirectiveManager
from desktop_study_companion.config.loader import load_config_with_recovery
from desktop_study_companion.controller import ApplicationController
from desktop_study_companion.routines.manager import RoutineManager
from desktop_study_companion.routines.models import Routine


def _write_config(path: Path, *, name: str = "Luna", brain: dict | None = None) -> None:
    payload = {
        "personality": {"name": name},
        "voice": {"enabled": False},
    }
    if brain is not None:
        payload["brain"] = brain
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_remote_http_key_disables_only_brain_and_preserves_config(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "config.json"
    key_env = "DESKTOP_STUDY_COMPANION_LLM_API_KEY"
    _write_config(
        path,
        brain={
            "enabled": True,
            "base_url": "http://192.168.1.5:11434/v1",
            "model": "qwen3:4b-instruct",
            "api_key_env": key_env,
        },
    )
    monkeypatch.setenv(key_env, "sk-test")

    config, notice = load_config_with_recovery(path)

    assert config.personality.name == "Luna"
    assert config.brain.enabled is True
    assert path.exists()
    assert not list(tmp_path.glob("config.json.bak*"))
    assert notice is not None
    assert "http" in notice.casefold()


def test_transient_config_read_error_is_retried_without_quarantine(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "config.json"
    _write_config(path)
    original_read_text = Path.read_text
    calls = {"count": 0}

    def flaky_read_text(self, *args, **kwargs):
        if self == path and calls["count"] == 0:
            calls["count"] += 1
            raise PermissionError("arquivo temporariamente ocupado")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", flaky_read_text)

    config, notice = load_config_with_recovery(path)

    assert calls["count"] == 1
    assert config.personality.name == "Luna"
    assert path.exists()
    assert not list(tmp_path.glob("config.json.bak*"))
    assert notice is None


def test_identical_malformed_json_creates_only_one_snapshot(tmp_path) -> None:
    path = tmp_path / "directives.json"
    path.write_text(
        json.dumps(
            [
                {"goal": "válido", "urgency": 5},
                {"goal": "inválido", "urgency": "alta"},
            ]
        ),
        encoding="utf-8",
    )

    for _ in range(4):
        manager = DirectiveManager(path)
        assert [item.goal for item in manager.directives] == ["válido"]

    backups = list(tmp_path.glob("directives.json.bak*"))
    assert len(backups) == 1


def test_on_wake_requires_ten_minute_gap_and_description_matches(tmp_path) -> None:
    manager = RoutineManager(tmp_path / "routines.json")
    routine = Routine(goal="Retomar estudos", schedule="on_wake")

    assert RoutineManager.WAKE_GAP_MINUTES == 10
    assert ApplicationController.WAKE_GAP_SECONDS == 600.0
    assert "10 minutos" in manager.describe(routine)
