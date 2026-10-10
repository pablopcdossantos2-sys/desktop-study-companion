"""Crash-safe JSON persistence helpers for small local state files."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Callable, TypeVar
from uuid import uuid4

logger = logging.getLogger("desktop_study_companion.safe_json")
T = TypeVar("T")


def _backup_path(path: Path) -> Path:
    candidate = path.with_name(path.name + ".bak")
    index = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.bak.{index}")
        index += 1
    return candidate


def quarantine_invalid_json(path: str | Path) -> Path | None:
    source = Path(path)
    if not source.exists():
        return None
    backup = _backup_path(source)
    try:
        os.replace(source, backup)
    except OSError:
        logger.exception("Could not quarantine invalid JSON path=%s", source)
        return None
    logger.error("Invalid JSON quarantined path=%s backup=%s", source, backup)
    return backup


def load_json_list(
    path: str | Path,
    item_loader: Callable[[dict], T],
) -> list[T]:
    source = Path(path)
    if not source.exists():
        return []
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        quarantine_invalid_json(source)
        return []

    if not isinstance(raw, list):
        quarantine_invalid_json(source)
        return []

    result: list[T] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            logger.warning(
                "Skipping invalid JSON item path=%s index=%s type=%s",
                source,
                index,
                type(item).__name__,
            )
            continue
        try:
            result.append(item_loader(item))
        except (AttributeError, KeyError, TypeError, ValueError):
            logger.exception(
                "Skipping malformed JSON item path=%s index=%s",
                source,
                index,
            )
    return result


def atomic_write_json(path: str | Path, payload) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)
    return target
