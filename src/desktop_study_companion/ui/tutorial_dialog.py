from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)


class TutorialDialog(QDialog):
    def __init__(
        self,
        title: str,
        tutorial_path: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.tutorial_path = tutorial_path
        self.setWindowTitle(title)
        self.resize(780, 650)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        heading = QLabel(title)
        heading.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)

        if tutorial_path.exists():
            try:
                self.browser.setMarkdown(
                    tutorial_path.read_text(encoding="utf-8")
                )
            except Exception as exc:
                self.browser.setPlainText(
                    f"Não foi possível carregar o tutorial.\n\n{exc}"
                )
        else:
            self.browser.setPlainText(
                "Este tutorial não foi encontrado na instalação.\n\n"
                f"Caminho esperado:\n{tutorial_path}"
            )

        open_file = QPushButton("Abrir arquivo completo")
        open_file.clicked.connect(self._open_file)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(heading)
        layout.addWidget(self.browser, 1)
        layout.addWidget(open_file)
        layout.addWidget(buttons)

    def _open_file(self) -> None:
        if not self.tutorial_path.exists():
            QMessageBox.warning(
                self,
                "Tutorial ausente",
                f"Arquivo não encontrado:\n{self.tutorial_path}",
            )
            return
        try:
            os.startfile(str(self.tutorial_path))
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Não foi possível abrir o arquivo",
                str(exc),
            )
