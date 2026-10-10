"""Resolve stable paths in source, wheel and frozen/portable builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _source_checkout_root() -> Path | None:
    candidate = Path(__file__).resolve().parents[2]
    if (
        (candidate / "pyproject.toml").is_file()
        and (candidate / "src" / "desktop_study_companion").is_dir()
    ):
        return candidate
    return None


def _installed_resource_root() -> Path:
    return Path(__file__).resolve().parent / "_resources"


def application_root() -> Path:
    """Directory that owns resources for this running copy."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    source_root = _source_checkout_root()
    if source_root is not None:
        return source_root
    return _installed_resource_root()


def data_directory() -> Path:
    if getattr(sys, "frozen", False):
        path = application_root() / "data"
    else:
        source_root = _source_checkout_root()
        if source_root is not None:
            path = source_root / "data"
        else:
            local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
            if local_app_data:
                path = Path(local_app_data) / "DesktopStudyCompanion"
            else:
                xdg_data = os.environ.get("XDG_DATA_HOME", "").strip()
                base = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"
                path = base / "desktop-study-companion"
    path.mkdir(parents=True, exist_ok=True)
    return path


def external_config_path() -> Path:
    """Writable user configuration; never overwrite the versioned default."""
    return data_directory() / "config.json"


def bundled_config_path() -> Path | None:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if not bundle_root:
        return None
    return Path(bundle_root) / "config" / "default.json"


def source_default_config_path() -> Path:
    return application_root() / "config" / "default.json"


def avatar_model_path() -> Path:
    return application_root() / "assets" / "avatar" / "Sendagaya_Shino.vrm"


def avatar_renderer_directory() -> Path:
    return application_root() / "avatar" / "renderer"


def docs_directory() -> Path:
    return application_root() / "docs"
