from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QDialog

from desktop_study_companion.accountability.engine import (
    AccountabilityEngine,
    AccountabilityPolicy,
)
from desktop_study_companion.accountability.models import InterventionKind
from desktop_study_companion.activity.classifier import ActivityClassifier
from desktop_study_companion.activity.models import ActivityKind
from desktop_study_companion.activity.windows_monitor import WindowsActiveWindowMonitor
from desktop_study_companion.config.models import AppConfig
from desktop_study_companion.memory.sqlite_store import SQLiteMemoryStore
from desktop_study_companion.personality.models import Personality
from desktop_study_companion.personality.renderer import PersonalityRenderer
from desktop_study_companion.study.manager import StudySessionManager
from desktop_study_companion.ui.companion_widget import CompanionWidget
from desktop_study_companion.ui.session_dialog import SessionDialog
from desktop_study_companion.voice.windows_sapi import WindowsSapiTTS


class ApplicationController(QObject):
    SESSION_SAVE_INTERVAL_SECONDS = 10.0

    def __init__(self, app: QApplication, config: AppConfig) -> None:
        super().__init__()
        self.app = app
        self.config = config
        self.monitor = WindowsActiveWindowMonitor()
        self.classifier = ActivityClassifier(
            productive_keywords=set(config.activity.productive_keywords),
            neutral_keywords=set(config.activity.neutral_keywords),
            distraction_keywords=set(config.activity.distraction_keywords),
        )
        self.sessions = StudySessionManager()
        self.accountability = AccountabilityEngine(
            AccountabilityPolicy(
                gentle_after_seconds=config.accountability.gentle_after_seconds,
                firm_after_seconds=config.accountability.firm_after_seconds,
                direct_after_seconds=config.accountability.direct_after_seconds,
                insistent_after_seconds=config.accountability.insistent_after_seconds,
            )
        )
        self.personality = PersonalityRenderer(
            Personality(
                warmth=config.personality.warmth,
                sarcasm=config.personality.sarcasm,
                strictness=config.personality.strictness,
                patience=config.personality.patience,
                humor=config.personality.humor,
                initiative=config.personality.initiative,
            ),
            name=config.personality.name,
        )
        self.voice = (
            WindowsSapiTTS(rate=config.voice.rate, volume=config.voice.volume)
            if config.voice.enabled
            else None
        )
        self.memory = SQLiteMemoryStore(Path("data") / "companion.db")
        self.widget = CompanionWidget(config.personality.name)

        self._paused = False
        self._last_poll = time.monotonic()
        self._last_intervention_kind = InterventionKind.NONE
        self._last_intervention_at = 0.0
        self._last_session_save_at = 0.0
        self._last_activity_key: tuple[str, str, str] | None = None

        self.timer = QTimer(self)
        self.timer.setInterval(config.monitor.poll_interval_ms)
        self.timer.timeout.connect(self._poll)

        self.widget.start_session_requested.connect(self.start_session)
        self.widget.finish_session_requested.connect(self.finish_session)
        self.widget.pause_monitoring_requested.connect(self.set_paused)
        self.widget.quit_requested.connect(self.shutdown)

    def start(self) -> None:
        self.widget.show()
        self.timer.start()

    def _say(self, text: str, *, voice: bool = True) -> None:
        self.widget.say(text)
        if voice and self.voice is not None:
            self.voice.speak(text)

    def start_session(self) -> None:
        if self.sessions.active:
            self._say("Já existe uma sessão em andamento.")
            return

        dialog = SessionDialog(self.widget)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        session = self.sessions.start(dialog.goal.text(), dialog.minutes.value())
        self.memory.save_session(session)
        self._last_session_save_at = time.monotonic()
        self._last_activity_key = None
        self._last_intervention_kind = InterventionKind.NONE
        self._say(
            f"Combinado: {session.planned_minutes} minutos para {session.goal}. "
            "Eu vou acompanhar."
        )

    def finish_session(self) -> None:
        if self.sessions.session is None:
            self._say("Não há sessão ativa.")
            return

        session = self.sessions.finish()
        self.memory.save_session(session)
        focused = round(session.focused_seconds / 60, 1)
        distracted = round(session.distracted_seconds / 60, 1)
        self._say(
            f"Sessão encerrada. Foco classificado: {focused} minutos; "
            f"distração: {distracted} minutos."
        )

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        self._last_poll = time.monotonic()

    def _save_activity_if_changed(self, session_id: str | None, classified) -> None:
        key = (
            classified.window.process_name.casefold(),
            classified.window.title.casefold(),
            classified.kind.value,
        )
        if key != self._last_activity_key:
            self.memory.save_activity(session_id, classified)
            self._last_activity_key = key

    def _save_session_periodically(self, now: float) -> None:
        if self.sessions.session is None:
            return
        if now - self._last_session_save_at >= self.SESSION_SAVE_INTERVAL_SECONDS:
            self.memory.save_session(self.sessions.session)
            self._last_session_save_at = now

    def _poll(self) -> None:
        now = time.monotonic()
        elapsed = max(0.0, now - self._last_poll)
        self._last_poll = now

        if self._paused:
            return

        window = self.monitor.sample()
        classified = self.classifier.classify(window)

        session_id = self.sessions.session.id if self.sessions.session else None
        if self.sessions.active:
            self._save_activity_if_changed(session_id, classified)

        tick = self.sessions.tick(classified.kind, elapsed)
        if tick is None:
            return

        self._save_session_periodically(now)

        if not self.sessions.active:
            session = self.sessions.session
            if session:
                self.memory.save_session(session)
                self._say(
                    f"Tempo cumprido para {session.goal}. "
                    "Sessão registrada. Bom trabalho."
                )
            return

        if classified.kind != ActivityKind.DISTRACTION:
            if self._last_intervention_kind != InterventionKind.NONE:
                self._say("Você voltou. Ótimo. Continue.")
            self._last_intervention_kind = InterventionKind.NONE
            return

        intervention = self.accountability.evaluate_distraction(
            tick.distraction_streak_seconds
        )
        if intervention.kind == InterventionKind.NONE:
            return

        cooldown = self.config.accountability.cooldown_seconds
        same_level = intervention.kind == self._last_intervention_kind
        if same_level and now - self._last_intervention_at < cooldown:
            return

        message = self.personality.intervention_message(intervention.kind)
        self._say(message)
        self.memory.save_intervention(
            session_id,
            intervention,
            payload={
                "process_name": classified.window.process_name,
                "window_title": classified.window.title,
                "message": message,
            },
        )
        self._last_intervention_kind = intervention.kind
        self._last_intervention_at = now

    def shutdown(self) -> None:
        if self.sessions.session is not None:
            self.memory.save_session(self.sessions.session)
        self.timer.stop()
        if self.voice is not None:
            self.voice.close()
        self.memory.close()
        self.app.quit()
