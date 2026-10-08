from desktop_study_companion import runtime_paths


def test_source_application_root_uses_working_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delattr(runtime_paths.sys, "frozen", raising=False)

    assert runtime_paths.application_root() == tmp_path
    assert runtime_paths.data_directory() == tmp_path / "data"
    assert runtime_paths.external_config_path() == tmp_path / "config" / "default.json"
