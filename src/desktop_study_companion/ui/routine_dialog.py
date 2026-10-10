from __future__ import annotations

from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
)


class RoutineDialog(QDialog):
    """Editor for daily, weekly, interval and resume-triggered routines."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nova rotina")

        self.goal = QLineEdit()
        self.goal.setPlaceholderText("Ex.: Começar a revisão de inglês")

        self.schedule = QComboBox()
        self.schedule.addItem("Todos os dias", "daily")
        self.schedule.addItem("Semanal", "weekly")
        self.schedule.addItem("A cada intervalo", "interval")
        self.schedule.addItem("Ao voltar após longo período", "on_wake")

        self.time = QTimeEdit()
        self.time.setDisplayFormat("HH:mm")
        self.time.setTime(QTime.currentTime())

        self.day = QComboBox()
        for label, code in (
            ("Segunda-feira", "monday"),
            ("Terça-feira", "tuesday"),
            ("Quarta-feira", "wednesday"),
            ("Quinta-feira", "thursday"),
            ("Sexta-feira", "friday"),
            ("Sábado", "saturday"),
            ("Domingo", "sunday"),
        ):
            self.day.addItem(label, code)

        self.interval_hours = QDoubleSpinBox()
        self.interval_hours.setRange(0.25, 168.0)
        self.interval_hours.setSingleStep(0.25)
        self.interval_hours.setDecimals(2)
        self.interval_hours.setValue(2.0)
        self.interval_hours.setSuffix(" h")

        self.urgency = QSpinBox()
        self.urgency.setRange(1, 10)
        self.urgency.setValue(5)

        form = QFormLayout()
        form.addRow("Lembrete/meta:", self.goal)
        form.addRow("Tipo:", self.schedule)
        form.addRow("Horário:", self.time)
        form.addRow("Dia da semana:", self.day)
        form.addRow("Intervalo:", self.interval_hours)
        form.addRow("Urgência:", self.urgency)
        self._form = form

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.schedule.currentIndexChanged.connect(
            self._sync_schedule_fields
        )
        self._sync_schedule_fields()

    def _sync_schedule_fields(self) -> None:
        schedule = str(self.schedule.currentData() or "daily")
        uses_time = schedule in {"daily", "weekly"}
        uses_day = schedule == "weekly"
        uses_interval = schedule == "interval"

        self.time.setEnabled(uses_time)
        self.day.setEnabled(uses_day)
        self.interval_hours.setEnabled(uses_interval)

        for field, enabled in (
            (self.time, uses_time),
            (self.day, uses_day),
            (self.interval_hours, uses_interval),
        ):
            label = self._form.labelForField(field)
            if label is not None:
                label.setEnabled(enabled)
