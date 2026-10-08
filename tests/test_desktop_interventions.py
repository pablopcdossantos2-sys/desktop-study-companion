from desktop_study_companion.activity.models import ActiveWindow
from desktop_study_companion.desktop.interventions import (
    DesktopInterventionController,
    InterventionPermissionStore,
)


class FakeBackend:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def minimize(self, hwnd: int) -> bool:
        self.calls.append(("minimize", hwnd))
        return True

    def close_window(self, hwnd: int) -> bool:
        self.calls.append(("close_window", hwnd))
        return True

    def close_browser_tab(self, hwnd: int) -> bool:
        self.calls.append(("close_browser_tab", hwnd))
        return True


def _controller(tmp_path):
    store = InterventionPermissionStore(tmp_path / "permissions.json")
    backend = FakeBackend()
    return DesktopInterventionController(store, backend), store, backend


def test_interventions_are_disabled_by_default(tmp_path) -> None:
    controller, _, backend = _controller(tmp_path)
    window = ActiveWindow("chrome.exe", "YouTube", hwnd=123)

    result = controller.perform("close_and_nag", window)

    assert result.performed is False
    assert backend.calls == []


def test_minimize_requires_explicit_permission(tmp_path) -> None:
    controller, store, backend = _controller(tmp_path)
    store.permissions.enabled = True
    store.permissions.allow_minimize = True
    window = ActiveWindow("chrome.exe", "YouTube", hwnd=123)

    result = controller.perform("minimize_and_nag", window)

    assert result.performed is True
    assert backend.calls == [("minimize", 123)]


def test_browser_close_targets_tab(tmp_path) -> None:
    controller, store, backend = _controller(tmp_path)
    store.permissions.enabled = True
    store.permissions.allow_close = True
    window = ActiveWindow("msedge.exe", "YouTube", hwnd=55)

    result = controller.perform("close_and_nag", window)

    assert result.performed is True
    assert backend.calls == [("close_browser_tab", 55)]


def test_protected_process_never_receives_action(tmp_path) -> None:
    controller, store, backend = _controller(tmp_path)
    store.permissions.enabled = True
    store.permissions.allow_close = True
    window = ActiveWindow("powershell.exe", "Terminal", hwnd=99)

    result = controller.perform("close_and_nag", window)

    assert result.performed is False
    assert "protected process" in result.reason
    assert backend.calls == []


def test_emergency_disable_revokes_every_permission(tmp_path) -> None:
    _, store, _ = _controller(tmp_path)
    store.permissions.enabled = True
    store.permissions.allow_minimize = True
    store.permissions.allow_close = True
    store.save()

    store.emergency_disable()

    assert store.permissions.enabled is False
    assert store.permissions.allow_minimize is False
    assert store.permissions.allow_close is False
