"""Resolve stable paths in source and frozen/portable builds."""

from __future__ import annotations

import sys
from pathlib import Path


def application_root() -> Path:
    """Directory that owns bundled resources for this running copy."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def data_directory() -> Path:
    path = application_root() / "data"
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
