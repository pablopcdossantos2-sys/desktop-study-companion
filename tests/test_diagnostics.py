import json
from pathlib import Path

from desktop_study_companion import diagnostics


def test_diagnostic_summary_reports_runtime_paths(tmp_path, monkeypatch) -> None:
    root = tmp_path / "app"
    root.mkdir()
    model = root / "model.vrm"
    model.write_bytes(b"vrm")
    renderer = root / "renderer"
    renderer.mkdir()
    (renderer / "index.html").write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(diagnostics, "application_root", lambda: root)
    monkeypatch.setattr(
        diagnostics,
        "external_config_path",
        lambda: root / "config" / "default.json",
    )
    monkeypatch.setattr(diagnostics, "avatar_model_path", lambda: model)
    monkeypatch.setattr(
        diagnostics,
        "avatar_renderer_directory",
        lambda: renderer,
    )
    monkeypatch.setattr(
        diagnostics,
        "_log_path",
        root / "data" / "logs" / "desktop-study-companion.log",
    )

    summary = diagnostics.diagnostic_summary()

    assert "Desktop Study Companion" in summary
    assert "Avatar VRM:" in summary
    assert "3 bytes" in summary
    assert "Renderer:" in summary
    assert "index.html" in summary


def test_run_state_marks_unclean_and_clean_exits(tmp_path, monkeypatch) -> None:
    state_path = tmp_path / "run-state.json"
    monkeypatch.setattr(diagnostics, "run_state_path", lambda: state_path)

    assert diagnostics.mark_run_started() is False
    first = json.loads(state_path.read_text(encoding="utf-8"))
    assert first["clean_exit"] is False

    # Starting again before a clean marker simulates an abrupt prior exit.
    assert diagnostics.mark_run_started() is True

    diagnostics.mark_run_clean()
    clean = json.loads(state_path.read_text(encoding="utf-8"))
    assert clean["clean_exit"] is True
    assert "ended_at" in clean

    # A clean previous execution must not be reported as a crash.
    assert diagnostics.mark_run_started() is False
