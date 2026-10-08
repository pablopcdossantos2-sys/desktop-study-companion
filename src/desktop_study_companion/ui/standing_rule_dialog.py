from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class StandingRuleDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nova regra permanente")

        self.description = QLineEdit()
        self.description.setPlaceholderText(
            "Ex.: Não usar YouTube enquanto deveria estudar"
        )

        self.patterns = QLineEdit()
        self.patterns.setPlaceholderText("youtube, netflix, reddit")

        self.cooldown = QSpinBox()
        self.cooldown.setRange(5, 3600)
        self.cooldown.setValue(60)
        self.cooldown.setSuffix(" s")

        form = QFormLayout()
        form.addRow("Regra:", self.description)
        form.addRow("Padrões (separados por vírgula):", self.patterns)
        form.addRow("Intervalo mínimo entre cobranças:", self.cooldown)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)
