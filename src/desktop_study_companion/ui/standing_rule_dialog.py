from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
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

        self.response = QComboBox()
        self.response.addItem("Somente cobrar", "nag")
        self.response.addItem("Minimizar e cobrar", "minimize_and_nag")
        self.response.addItem("Fechar e cobrar", "close_and_nag")

        note = QLabel(
            "Minimizar/fechar só funciona se a permissão correspondente "
            "também for habilitada em Intervenções no desktop."
        )
        note.setWordWrap(True)

        self.cooldown = QSpinBox()
        self.cooldown.setRange(5, 3600)
        self.cooldown.setValue(60)
        self.cooldown.setSuffix(" s")

        form = QFormLayout()
        form.addRow("Regra:", self.description)
        form.addRow("Padrões (separados por vírgula):", self.patterns)
        form.addRow("Resposta:", self.response)
        form.addRow("Intervalo mínimo entre cobranças:", self.cooldown)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addWidget(buttons)

    def response_code(self) -> str:
        return str(self.response.currentData())
