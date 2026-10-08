from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from desktop_study_companion.desktop.interventions import InterventionPermissions


class InterventionSettingsDialog(QDialog):
    def __init__(
        self,
        permissions: InterventionPermissions,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Permissões de intervenção")

        warning = QLabel(
            "Estas permissões permitem que a personagem altere janelas do "
            "desktop. Permanecem desativadas por padrão."
        )
        warning.setWordWrap(True)

        self.enabled = QCheckBox("Permitir intervenções no desktop")
        self.enabled.setChecked(permissions.enabled)

        self.allow_minimize = QCheckBox("Permitir minimizar janelas")
        self.allow_minimize.setChecked(permissions.allow_minimize)

        self.allow_close = QCheckBox(
            "Permitir fechar janela/aba quando uma regra solicitar"
        )
        self.allow_close.setChecked(permissions.allow_close)

        self.protected = QLineEdit(
            ", ".join(permissions.protected_processes)
        )

        form = QFormLayout()
        form.addRow("", self.enabled)
        form.addRow("", self.allow_minimize)
        form.addRow("", self.allow_close)
        form.addRow("Processos protegidos:", self.protected)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(warning)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> InterventionPermissions:
        protected = [
            part.strip()
            for part in self.protected.text().split(",")
            if part.strip()
        ]
        return InterventionPermissions(
            enabled=self.enabled.isChecked(),
            allow_minimize=self.allow_minimize.isChecked(),
            allow_close=self.allow_close.isChecked(),
            protected_processes=protected,
        )
