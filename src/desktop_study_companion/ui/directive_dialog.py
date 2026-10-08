from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class DirectiveDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Novo compromisso")

        self.goal = QLineEdit()
        self.goal.setPlaceholderText("Ex.: Terminar 30 questões de revisão")

        self.urgency = QSpinBox()
        self.urgency.setRange(1, 10)
        self.urgency.setValue(6)

        self.delay_minutes = QSpinBox()
        self.delay_minutes.setRange(0, 1440)
        self.delay_minutes.setValue(5)
        self.delay_minutes.setSuffix(" min")

        form = QFormLayout()
        form.addRow("Compromisso:", self.goal)
        form.addRow("Urgência:", self.urgency)
        form.addRow("Primeira cobrança em:", self.delay_minutes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)
