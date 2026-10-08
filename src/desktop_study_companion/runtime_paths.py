from __future__ import annotations

"""Resolve stable paths in source and frozen/portable builds."""

import sys
from pathlib import Path


def application_root() -> Path:
    """Directory that owns config/ and data/ for this running copy."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd().resolve()


def data_directory() -> Path:
    path = application_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def external_config_path() -> Path:
    return application_root() / "config" / "default.json"


def bundled_config_path() -> Path | None:
    """PyInstaller's temporary/internal bundle path, when applicable."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if not bundle_root:
        return None
    return Path(bundle_root) / "config" / "default.json"
