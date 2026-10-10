from __future__ import annotations

from PySide6.QtCore import Qt, Signal
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
    push_to_talk_started = Signal()
    push_to_talk_finished = Signal()

    def __init__(self, character_name: str, parent=None) -> None:
        super().__init__(parent)
        self.character_name = character_name
        self.setWindowTitle(f"Conversar com {character_name}")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.resize(620, 520)

        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Escreva uma mensagem…")
        self.input.returnPressed.connect(self._submit)

        self.send = QPushButton("Enviar")
        self.send.clicked.connect(self._submit)

        self.mic = QPushButton("Segure para falar")
        self.mic.pressed.connect(self.push_to_talk_started.emit)
        self.mic.released.connect(self.push_to_talk_finished.emit)

        self.clear = QPushButton("Limpar histórico")
        self.clear.clicked.connect(self.clear_requested.emit)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.mic)
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
        self.mic.setEnabled(not busy)
        self.clear.setEnabled(not busy)
        if not busy:
            self.input.setFocus()

    def set_recording(self, recording: bool) -> None:
        if recording:
            self.mic.setText("Gravando… solte para enviar")
            self.input.setEnabled(False)
            self.send.setEnabled(False)
            self.clear.setEnabled(False)
        else:
            self.mic.setText("Segure para falar")
            self.input.setEnabled(True)
            self.send.setEnabled(True)
            self.clear.setEnabled(True)

    def set_transcript_draft(self, text: str) -> None:
        self.input.setText(text)
        self.input.setFocus()

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
