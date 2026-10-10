from pathlib import Path

from desktop_study_companion import runtime_paths


def test_source_application_root_is_anchored_to_project(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delattr(runtime_paths.sys, "frozen", raising=False)

    expected = Path(runtime_paths.__file__).resolve().parents[2]
    assert runtime_paths.application_root() == expected
    assert runtime_paths.data_directory() == expected / "data"
    assert runtime_paths.external_config_path() == expected / "data" / "config.json"
