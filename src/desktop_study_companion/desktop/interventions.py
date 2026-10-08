from __future__ import annotations

"""Permission-gated desktop interventions adapted from bonziPONY.

Relevant upstream behavior:
- targeted minimize/close actions;
- close only the active browser tab via Ctrl+W when possible;
- guard against acting on the companion/console;
- desktop-control actions are separated from conversational decisions.

Upstream:
https://github.com/maresmaremares/bonziPONY/blob/master/robot/desktop_controller.py

This adaptation adds a stricter opt-in permission layer and protected-process
list. No invasive action is enabled by default.
"""

import json
import platform
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

from desktop_study_companion.activity.models import ActiveWindow


_BROWSER_PROCESSES = {
    "chrome",
    "chrome.exe",
    "msedge",
    "msedge.exe",
    "firefox",
    "firefox.exe",
    "brave",
    "brave.exe",
    "opera",
    "opera.exe",
    "vivaldi",
    "vivaldi.exe",
}

_DEFAULT_PROTECTED_PROCESSES = {
    "desktop-study-companion.exe",
    "explorer.exe",
    "taskmgr.exe",
    "powershell.exe",
    "pwsh.exe",
    "cmd.exe",
    "conhost.exe",
    "python.exe",
    "pythonw.exe",
}


@dataclass(slots=True)
class InterventionPermissions:
    enabled: bool = False
    allow_minimize: bool = False
    allow_close: bool = False
    allow_session_escalation: bool = False
    allow_lockdown: bool = False
    lockdown_minutes: int = 5
    protected_processes: list[str] = field(
        default_factory=lambda: sorted(_DEFAULT_PROTECTED_PROCESSES)
    )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "InterventionPermissions":
        return cls(
            enabled=bool(data.get("enabled", False)),
            allow_minimize=bool(data.get("allow_minimize", False)),
            allow_close=bool(data.get("allow_close", False)),
            allow_session_escalation=bool(
                data.get("allow_session_escalation", False)
            ),
            allow_lockdown=bool(data.get("allow_lockdown", False)),
            lockdown_minutes=max(1, min(60, int(data.get("lockdown_minutes", 5)))),
            protected_processes=list(
                data.get(
                    "protected_processes",
                    sorted(_DEFAULT_PROTECTED_PROCESSES),
                )
            ),
        )


class InterventionPermissionStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.permissions = InterventionPermissions()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.permissions = InterventionPermissions()
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.permissions = InterventionPermissions.from_dict(data)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            self.permissions = InterventionPermissions()

    def save(self) -> None:
        self.path.write_text(
            json.dumps(
                self.permissions.to_dict(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def emergency_disable(self) -> None:
        self.permissions.enabled = False
        self.permissions.allow_minimize = False
        self.permissions.allow_close = False
        self.permissions.allow_session_escalation = False
        self.permissions.allow_lockdown = False
        self.save()


@dataclass(frozen=True, slots=True)
class InterventionResult:
    requested_action: str
    performed: bool
    reason: str


class WindowBackend(Protocol):
    def minimize(self, hwnd: int) -> bool: ...
    def close_window(self, hwnd: int) -> bool: ...
    def close_browser_tab(self, hwnd: int) -> bool: ...


class WindowsWindowBackend:
    """Small pywin32 backend for targeted window operations."""

    def __init__(self) -> None:
        if platform.system() != "Windows":
            raise RuntimeError("WindowsWindowBackend requires Windows.")

    def minimize(self, hwnd: int) -> bool:
        if not hwnd:
            return False
        try:
            import win32con
            import win32gui

            win32gui.ShowWindow(int(hwnd), win32con.SW_MINIMIZE)
            return True
        except Exception:
            return False

    def close_window(self, hwnd: int) -> bool:
        if not hwnd:
            return False
        try:
            import win32con
            import win32gui

            win32gui.PostMessage(int(hwnd), win32con.WM_CLOSE, 0, 0)
            return True
        except Exception:
            return False

    def close_browser_tab(self, hwnd: int) -> bool:
        """Close the active browser tab, not the browser process."""
        if not hwnd:
            return False
        try:
            import win32api
            import win32con
            import win32gui

            win32gui.SetForegroundWindow(int(hwnd))
            time.sleep(0.12)
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord("W"), 0, 0, 0)
            win32api.keybd_event(ord("W"), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(
                win32con.VK_CONTROL,
                0,
                win32con.KEYEVENTF_KEYUP,
                0,
            )
            return True
        except Exception:
            return False


class DesktopInterventionController:
    def __init__(
        self,
        permission_store: InterventionPermissionStore,
        backend: WindowBackend,
    ) -> None:
        self.permission_store = permission_store
        self.backend = backend

    @property
    def permissions(self) -> InterventionPermissions:
        return self.permission_store.permissions

    def _is_protected(self, process_name: str) -> bool:
        process = process_name.casefold().strip()
        protected = {
            p.casefold().strip()
            for p in self.permissions.protected_processes
        }
        protected |= {
            p.casefold().strip()
            for p in _DEFAULT_PROTECTED_PROCESSES
        }
        return process in protected

    def perform(self, response: str, window: ActiveWindow) -> InterventionResult:
        response = (response or "nag").casefold().strip()

        if response == "nag":
            return InterventionResult("nag", False, "rule requests nag only")

        permissions = self.permissions
        if not permissions.enabled:
            return InterventionResult(
                response,
                False,
                "desktop interventions are disabled",
            )

        if not window.hwnd:
            return InterventionResult(
                response,
                False,
                "target window handle is unavailable",
            )

        if self._is_protected(window.process_name):
            return InterventionResult(
                response,
                False,
                f"protected process: {window.process_name}",
            )

        if response == "minimize_and_nag":
            if not permissions.allow_minimize:
                return InterventionResult(
                    response,
                    False,
                    "minimize permission is disabled",
                )
            ok = self.backend.minimize(window.hwnd)
            return InterventionResult(
                response,
                ok,
                "window minimized" if ok else "minimize operation failed",
            )

        if response == "close_and_nag":
            if not permissions.allow_close:
                return InterventionResult(
                    response,
                    False,
                    "close permission is disabled",
                )

            process = window.process_name.casefold().strip()
            if process in _BROWSER_PROCESSES:
                ok = self.backend.close_browser_tab(window.hwnd)
                return InterventionResult(
                    response,
                    ok,
                    "browser tab closed" if ok else "browser tab close failed",
                )

            ok = self.backend.close_window(window.hwnd)
            return InterventionResult(
                response,
                ok,
                "window close requested" if ok else "window close failed",
            )

        return InterventionResult(
            response,
            False,
            f"unknown intervention response: {response}",
        )
