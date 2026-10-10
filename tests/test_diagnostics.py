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
