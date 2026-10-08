from __future__ import annotations

from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
)


class RoutineDialog(QDialog):
    """Simple v0.1 editor for a daily proactive study routine."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nova rotina diária")

        self.goal = QLineEdit()
        self.goal.setPlaceholderText("Ex.: Começar a revisão de inglês")

        self.time = QTimeEdit()
        self.time.setDisplayFormat("HH:mm")
        self.time.setTime(QTime.currentTime())

        self.urgency = QSpinBox()
        self.urgency.setRange(1, 10)
        self.urgency.setValue(5)

        form = QFormLayout()
        form.addRow("Lembrete/meta:", self.goal)
        form.addRow("Horário:", self.time)
        form.addRow("Urgência:", self.urgency)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)
