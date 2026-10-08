from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop_study_companion.memory.analytics import BehavioralOverview, SessionRecord


def _minutes(seconds: int) -> str:
    return f"{seconds / 60:.1f}"


class HistoryDialog(QDialog):
    def __init__(
        self,
        overview: BehavioralOverview,
        sessions: list[SessionRecord],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Histórico e insights")
        self.resize(820, 520)

        tabs = QTabWidget()
        tabs.addTab(self._overview_tab(overview), "Resumo")
        tabs.addTab(self._sessions_tab(sessions), "Sessões")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    def _overview_tab(self, overview: BehavioralOverview) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        headline = QLabel(
            f"Sessões: {overview.session_count} | "
            f"Conclusão: {overview.completion_rate:.0%} | "
            f"Foco classificado: {overview.average_focus_rate:.0%} | "
            f"Intervenções: {overview.intervention_count}"
        )
        headline.setWordWrap(True)
        headline.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(headline)

        for insight in overview.insights:
            label = QLabel(f"• {insight}")
            label.setWordWrap(True)
            label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            layout.addWidget(label)

        layout.addStretch(1)
        return widget

    def _sessions_tab(self, sessions: list[SessionRecord]) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        table = QTableWidget(len(sessions), 7)
        table.setHorizontalHeaderLabels(
            [
                "Início",
                "Objetivo",
                "Estado",
                "Planejado",
                "Foco",
                "Distração",
                "% foco",
            ]
        )

        for row, session in enumerate(sessions):
            started = session.started_at or "—"
            if "T" in started:
                started = started.replace("T", " ")[:16]

            values = [
                started,
                session.goal,
                session.state,
                f"{session.planned_minutes} min",
                f"{_minutes(session.focused_seconds)} min",
                f"{_minutes(session.distracted_seconds)} min",
                f"{session.focus_rate:.0%}",
            ]
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))

        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)
        return widget
