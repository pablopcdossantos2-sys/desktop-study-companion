from __future__ import annotations

import ctypes
import platform
import time
from ctypes import wintypes

import psutil

from .models import ActiveWindow


class WindowsActiveWindowMonitor:
    """Reads the Windows foreground window without taking screenshots."""

    def __init__(self) -> None:
        if platform.system() != "Windows":
            raise RuntimeError("WindowsActiveWindowMonitor requires Windows.")

        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._last_identity: tuple[str, str] | None = None
        self._active_since = time.monotonic()

    def sample(self) -> ActiveWindow:
        hwnd = self._user32.GetForegroundWindow()
        if not hwnd:
            return ActiveWindow("", "", 0.0)

        length = self._user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        self._user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value

        pid = wintypes.DWORD()
        self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        process_name = ""
        try:
            process_name = psutil.Process(pid.value).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            process_name = f"pid:{pid.value}"

        identity = (process_name.casefold(), title.casefold())
        now = time.monotonic()
        if identity != self._last_identity:
            self._last_identity = identity
            self._active_since = now

        return ActiveWindow(
            process_name=process_name,
            title=title,
            duration_seconds=max(0.0, now - self._active_since),
        )
