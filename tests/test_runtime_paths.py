from pathlib import Path

from desktop_study_companion import runtime_paths


def test_source_application_root_is_anchored_to_project(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delattr(runtime_paths.sys, "frozen", raising=False)

    expected = Path(runtime_paths.__file__).resolve().parents[2]
    assert runtime_paths.application_root() == expected
    assert runtime_paths.data_directory() == expected / "data"
    assert runtime_paths.external_config_path() == expected / "data" / "config.json"


def test_installed_wheel_uses_local_app_data_not_site_packages(
    monkeypatch,
    tmp_path,
) -> None:
    fake_file = (
        tmp_path
        / "Lib"
        / "site-packages"
        / "desktop_study_companion"
        / "runtime_paths.py"
    )
    fake_file.parent.mkdir(parents=True)
    monkeypatch.setattr(runtime_paths, "__file__", str(fake_file))
    monkeypatch.delattr(runtime_paths.sys, "frozen", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))

    assert runtime_paths.application_root() == (
        fake_file.parent / "_resources"
    )
    assert runtime_paths.data_directory() == (
        tmp_path / "LocalAppData" / "DesktopStudyCompanion"
    )
