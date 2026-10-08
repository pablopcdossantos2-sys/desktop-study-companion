from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class SessionDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nova sessão de estudo")

        self.goal = QLineEdit()
        self.goal.setPlaceholderText("Ex.: Revisar capítulo 3")
        self.minutes = QSpinBox()
        self.minutes.setRange(1, 480)
        self.minutes.setValue(30)
        self.minutes.setSuffix(" min")

        form = QFormLayout()
        form.addRow("Objetivo:", self.goal)
        form.addRow("Duração:", self.minutes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)
