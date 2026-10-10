from desktop_study_companion.ui.windowing import prepare_top_level_window


class _FakeDialog:
    def __init__(self) -> None:
        self.parent = "original"
        self.flags = []
        self.modality = None

    def setParent(self, value) -> None:
        self.parent = value

    def setWindowFlag(self, flag, enabled=True) -> None:
        self.flags.append((flag, enabled))

    def setWindowModality(self, value) -> None:
        self.modality = value


def test_prepare_top_level_window_detaches_dialog() -> None:
    dialog = _FakeDialog()

    prepare_top_level_window(dialog, modal=True)

    assert dialog.parent is None
    assert dialog.modality is not None
    assert any(enabled for _flag, enabled in dialog.flags)
