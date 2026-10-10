from pathlib import Path

from desktop_study_companion.runtime_paths import docs_directory


def test_docs_directory_points_to_docs_folder(monkeypatch, tmp_path) -> None:
    from desktop_study_companion import runtime_paths

    monkeypatch.setattr(runtime_paths, "application_root", lambda: tmp_path)
    assert docs_directory() == Path(tmp_path) / "docs"
