from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class ChatDialog(QDialog):
    message_submitted = Signal(str)
    clear_requested = Signal()

    def __init__(self, character_name: str, parent=None) -> None:
        super().__init__(parent)
        self.character_name = character_name
        self.setWindowTitle(f"Conversar com {character_name}")
        self.resize(620, 520)

        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Escreva uma mensagem…")
        self.input.returnPressed.connect(self._submit)

        self.send = QPushButton("Enviar")
        self.send.clicked.connect(self._submit)

        self.clear = QPushButton("Limpar histórico")
        self.clear.clicked.connect(self.clear_requested.emit)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.send)

        layout = QVBoxLayout(self)
        layout.addWidget(self.transcript, 1)
        layout.addLayout(input_row)
        layout.addWidget(self.clear)

    def _submit(self) -> None:
        text = self.input.text().strip()
        if not text or not self.send.isEnabled():
            return
        self.append_user(text)
        self.input.clear()
        self.set_busy(True)
        self.message_submitted.emit(text)

    def append_user(self, text: str) -> None:
        self.transcript.append(f"<b>Você:</b> {self._escape(text)}")

    def append_assistant(self, text: str) -> None:
        name = self._escape(self.character_name)
        self.transcript.append(f"<b>{name}:</b> {self._escape(text)}")

    def append_status(self, text: str) -> None:
        self.transcript.append(f"<i>{self._escape(text)}</i>")

    def load_history(self, messages: list[tuple[str, str]]) -> None:
        self.transcript.clear()
        for role, content in messages:
            if role == "user":
                self.append_user(content)
            elif role == "assistant":
                self.append_assistant(content)

    def set_busy(self, busy: bool) -> None:
        self.send.setEnabled(not busy)
        self.input.setEnabled(not busy)
        self.clear.setEnabled(not busy)
        if not busy:
            self.input.setFocus()

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
