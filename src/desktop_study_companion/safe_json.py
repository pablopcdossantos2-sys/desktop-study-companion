"""Crash-safe JSON persistence helpers for small local state files."""

from __future__ import annotations

import json
import logging
import os
import shutil
import time
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


def _replace_with_retry(source: Path, target: Path, attempts: int = 5) -> None:
    last_error: OSError | None = None
    for attempt in range(max(1, attempts)):
        try:
            os.replace(source, target)
            return
        except PermissionError as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                raise
            time.sleep(0.05 * (attempt + 1))
    if last_error is not None:
        raise last_error


def quarantine_invalid_json(path: str | Path) -> Path | None:
    source = Path(path)
    if not source.exists():
        return None
    backup = _backup_path(source)
    try:
        _replace_with_retry(source, backup)
    except OSError:
        logger.exception("Could not quarantine invalid JSON path=%s", source)
        return None
    logger.error("Invalid JSON quarantined path=%s backup=%s", source, backup)
    return backup


def backup_json_snapshot(path: str | Path) -> Path | None:
    """Preserve the original file before dropping malformed list items."""
    source = Path(path)
    if not source.exists():
        return None
    backup = _backup_path(source)
    try:
        shutil.copy2(source, backup)
    except OSError:
        logger.exception("Could not preserve malformed JSON snapshot path=%s", source)
        return None
    logger.warning("Malformed JSON items preserved path=%s backup=%s", source, backup)
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
    malformed = False
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            malformed = True
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
            malformed = True
            logger.exception(
                "Skipping malformed JSON item path=%s index=%s",
                source,
                index,
            )

    if malformed:
        backup_json_snapshot(source)
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
        _replace_with_retry(temp, target)
    finally:
        temp.unlink(missing_ok=True)
    return target
