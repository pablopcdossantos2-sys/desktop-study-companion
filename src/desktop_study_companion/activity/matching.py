"""Shared process/title matching rules used by classification and standing rules."""

from __future__ import annotations

import re
from collections.abc import Iterable


KNOWN_PRODUCTIVE_PROCESSES = frozenset(
    {
        "anki.exe",
        "code.exe",
        "devenv.exe",
        "excel.exe",
        "notepad.exe",
        "notepad++.exe",
        "obsidian.exe",
        "onenote.exe",
        "powerpnt.exe",
        "winword.exe",
    }
)


def normalized_keywords(values: Iterable[str]) -> tuple[str, ...]:
    cleaned = {
        value.casefold().strip()
        for value in values
        if isinstance(value, str) and value.strip()
    }
    return tuple(sorted(cleaned, key=len, reverse=True))


def process_matches(keyword: str, process_name: str) -> bool:
    process = process_name.casefold().strip()
    needle = keyword.casefold().strip()
    if not needle:
        return False
    return (
        process == needle
        or process.removesuffix(".exe") == needle.removesuffix(".exe")
    )


def is_known_productive_process(process_name: str) -> bool:
    return process_name.casefold().strip() in KNOWN_PRODUCTIVE_PROCESSES


def keyword_matches(
    keyword: str,
    process_name: str,
    title: str,
    *,
    protect_productive_titles: bool = True,
) -> bool:
    needle = keyword.casefold().strip()
    if not needle:
        return False
    if process_matches(needle, process_name):
        return True
    if protect_productive_titles and is_known_productive_process(process_name):
        return False
    return re.search(
        rf"(?<!\w){re.escape(needle)}(?!\w)",
        title.casefold(),
    ) is not None
