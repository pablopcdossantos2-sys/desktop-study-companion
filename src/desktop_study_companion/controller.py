from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QDialog, QInputDialog, QMessageBox

from desktop_study_companion.accountability.directives import DirectiveManager
from desktop_study_companion.accountability.engine import (
    AccountabilityEngine,
    AccountabilityPolicy,
)
from desktop_study_companion.accountability.models import InterventionKind
from desktop_study_companion.accountability.standing_rules import (
    StandingRule,
    StandingRuleManager,
)
from desktop_study_companion.activity.classifier import ActivityClassifier
from desktop_study_companion.activity.models import (
    ActivityKind,
    ClassifiedActivity,
)
from desktop_study_companion.activity.windows_monitor import (
    WindowsActiveWindowMonitor,
)
from desktop_study_companion.config.models import AppConfig
from desktop_study_companion.desktop.interventions import (
    DesktopInterventionController,
    InterventionPermissionStore,
    WindowsWindowBackend,
)
from desktop_study_companion.memory.sqlite_store import SQLiteMemoryStore
from desktop_study_companion.personality.models import Personality
from desktop_study_companion.personality.renderer import PersonalityRenderer
from desktop_study_companion.routines.manager import RoutineManager
from desktop_study_companion.routines.models import Routine
from desktop_study_companion.study.manager import StudySessionManager
from desktop_study_companion.ui.companion_widget import CompanionWidget
from desktop_study_companion.ui.directive_dialog import DirectiveDialog
from desktop_study_companion.ui.intervention_settings_dialog import (
    InterventionSettingsDialog,
)
from desktop_study_companion.ui.routine_dialog import RoutineDialog
from desktop_study_companion.ui.session_dialog import SessionDialog
from desktop_study_companion.ui.standing_rule_dialog import StandingRuleDialog
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
        self.directives = DirectiveManager(Path("data") / "directives.json")
        self.standing_rules = StandingRuleManager(
            Path("data") / "standing_rules.json"
        )
        self.routines = RoutineManager(Path("data") / "routines.json")
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
            WindowsSapiTTS(
                rate=config.voice.rate,
                volume=config.voice.volume,
            )
            if config.voice.enabled
            else None
        )
        self.memory = SQLiteMemoryStore(Path("data") / "companion.db")
        self.widget = CompanionWidget(config.personality.name)
        self.intervention_permissions = InterventionPermissionStore(
            Path("data") / "intervention_permissions.json"
        )
        self.desktop_interventions = DesktopInterventionController(
            self.intervention_permissions,
            WindowsWindowBackend(),
        )

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
        self.widget.add_directive_requested.connect(self.add_directive)
        self.widget.manage_directives_requested.connect(self.manage_directives)
        self.widget.add_rule_requested.connect(self.add_standing_rule)
        self.widget.manage_rules_requested.connect(self.manage_standing_rules)
        self.widget.add_routine_requested.connect(self.add_daily_routine)
        self.widget.manage_routines_requested.connect(self.manage_routines)
        self.widget.intervention_settings_requested.connect(
            self.configure_interventions
        )
        self.widget.emergency_disable_requested.connect(
            self.emergency_disable_interventions
        )
        self.widget.pause_monitoring_requested.connect(self.set_paused)
        self.widget.quit_requested.connect(self.shutdown)

    def start(self) -> None:
        self.widget.show()
        self.timer.start()

    def _say(self, text: str, *, voice: bool = True) -> None:
        self.widget.say(text)
        if voice and self.voice is not None:
            self.voice.speak(text)

    # ------------------------------------------------------------------
    # Study sessions
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Persistent directives / commitments
    # ------------------------------------------------------------------

    def add_directive(self) -> None:
        dialog = DirectiveDialog(self.widget)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        goal = dialog.goal.text().strip()
        if not goal:
            QMessageBox.warning(
                self.widget,
                "Compromisso sem descrição",
                "Escreva o compromisso que deverá ser acompanhado.",
            )
            return

        directive = self.directives.add(
            goal,
            dialog.urgency.value(),
            delay_seconds=dialog.delay_minutes.value() * 60,
        )
        self._say(
            f"Compromisso registrado: {directive.goal}. "
            "Eu vou continuar cobrando até você marcar como concluído."
        )

    def manage_directives(self) -> None:
        active = self.directives.active
        if not active:
            QMessageBox.information(
                self.widget,
                "Compromissos",
                "Nenhum compromisso ativo.",
            )
            return

        labels = [
            f"{d.goal} — urgência {d.urgency} — cobranças {d.nag_count}"
            for d in active
        ]
        selected, ok = QInputDialog.getItem(
            self.widget,
            "Gerenciar compromissos",
            "Selecione um compromisso:",
            labels,
            0,
            False,
        )
        if not ok or not selected:
            return

        directive = active[labels.index(selected)]
        box = QMessageBox(self.widget)
        box.setWindowTitle("Gerenciar compromisso")
        box.setText(
            f"{directive.goal}\n\n"
            f"Urgência: {directive.urgency}\n"
            f"Cobranças realizadas: {directive.nag_count}"
        )
        complete = box.addButton(
            "Marcar como concluído",
            QMessageBox.ButtonRole.AcceptRole,
        )
        snooze = None
        if not directive.delayed:
            snooze = box.addButton(
                "Adiar 5 min uma vez",
                QMessageBox.ButtonRole.ActionRole,
            )
        remove = box.addButton(
            "Remover",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.exec()

        if box.clickedButton() is complete:
            self.directives.complete(directive.id)
            self._say(f"Compromisso concluído: {directive.goal}. Boa.")
        elif snooze is not None and box.clickedButton() is snooze:
            if self.directives.snooze(directive.id, minutes=5):
                self._say(
                    "Tudo bem. Cinco minutos. É a única prorrogação deste compromisso."
                )
        elif box.clickedButton() is remove:
            self.directives.remove(directive.id)
            self._say(f"Compromisso removido: {directive.goal}.")

    def _poll_directives(self) -> None:
        for directive in self.directives.due():
            decision = self.directives.policy.decide(
                directive.urgency,
                directive.nag_count,
            )
            message = self.personality.directive_message(
                directive.goal,
                decision.severity,
                directive.nag_count,
            )
            self._say(message)
            self.directives.record_nag(directive, message)

    # ------------------------------------------------------------------
    # Standing rules
    # ------------------------------------------------------------------

    def add_standing_rule(self) -> None:
        dialog = StandingRuleDialog(self.widget)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        description = dialog.description.text().strip()
        patterns = [
            p.strip()
            for p in dialog.patterns.text().split(",")
            if p.strip()
        ]
        if not description or not patterns:
            QMessageBox.warning(
                self.widget,
                "Regra incompleta",
                "Informe uma descrição e pelo menos um padrão de detecção.",
            )
            return

        rule = self.standing_rules.add(
            StandingRule(
                description=description,
                patterns=patterns,
                response=dialog.response_code(),
                cooldown_s=dialog.cooldown.value(),
            )
        )
        self._say(
            f"Regra permanente criada: {rule.description}. "
            "Eu vou observar as janelas ativas."
        )

    def manage_standing_rules(self) -> None:
        if not self.standing_rules.rules:
            QMessageBox.information(
                self.widget,
                "Regras permanentes",
                "Nenhuma regra permanente cadastrada.",
            )
            return

        labels = [
            f"{rule.description} — flagrantes {rule.catch_count}"
            + ("" if rule.enabled else " [desativada]")
            for rule in self.standing_rules.rules
        ]
        selected, ok = QInputDialog.getItem(
            self.widget,
            "Gerenciar regras permanentes",
            "Selecione uma regra:",
            labels,
            0,
            False,
        )
        if not ok or not selected:
            return

        rule = self.standing_rules.rules[labels.index(selected)]
        box = QMessageBox(self.widget)
        box.setWindowTitle("Gerenciar regra")
        box.setText(
            f"{rule.description}\n\n"
            f"Padrões: {', '.join(rule.patterns)}\n"
            f"Flagrantes: {rule.catch_count}\n"
            f"Resposta: {rule.response}\n"
            f"Cooldown: {rule.cooldown_s:g} s"
        )
        toggle = box.addButton(
            "Desativar" if rule.enabled else "Ativar",
            QMessageBox.ButtonRole.ActionRole,
        )
        remove = box.addButton(
            "Remover",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.exec()

        if box.clickedButton() is toggle:
            self.standing_rules.toggle(rule.id)
            state = "ativada" if rule.enabled else "desativada"
            self._say(f"Regra {state}: {rule.description}.")
        elif box.clickedButton() is remove:
            self.standing_rules.remove(rule.id)
            self._say(f"Regra removida: {rule.description}.")

    def _poll_standing_rules(self, window) -> bool:
        violations = self.standing_rules.check(window)
        if not violations:
            return False

        for violation in violations:
            self.standing_rules.record_trigger(violation.rule)
            result = self.desktop_interventions.perform(
                violation.rule.response,
                violation.window,
            )
            message = self.personality.standing_rule_message(
                violation.rule.description,
                violation.rule.catch_count,
            )
            if result.performed:
                if result.requested_action == "minimize_and_nag":
                    message += " Eu minimizei a janela."
                elif result.requested_action == "close_and_nag":
                    message += " Eu fechei a distração."
            self._say(message)

        return True

    # ------------------------------------------------------------------
    # Desktop intervention permissions
    # ------------------------------------------------------------------

    def configure_interventions(self) -> None:
        dialog = InterventionSettingsDialog(
            self.intervention_permissions.permissions,
            self.widget,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        values = dialog.values()
        self.intervention_permissions.permissions = values
        self.intervention_permissions.save()

        if values.enabled:
            actions = []
            if values.allow_minimize:
                actions.append("minimizar")
            if values.allow_close:
                actions.append("fechar")
            detail = ", ".join(actions) if actions else "nenhuma ação invasiva"
            self._say(
                f"Intervenções habilitadas. Permissões atuais: {detail}."
            )
        else:
            self._say("Intervenções no desktop permanecem desativadas.")

    def emergency_disable_interventions(self) -> None:
        self.intervention_permissions.emergency_disable()
        self._say(
            "Intervenções desativadas imediatamente. "
            "Não vou minimizar nem fechar nenhuma janela."
        )

    # ------------------------------------------------------------------
    # Routines
    # ------------------------------------------------------------------

    def add_daily_routine(self) -> None:
        dialog = RoutineDialog(self.widget)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        goal = dialog.goal.text().strip()
        if not goal:
            QMessageBox.warning(
                self.widget,
                "Rotina sem descrição",
                "Escreva o que a personagem deve lembrar.",
            )
            return

        routine = Routine(
            goal=goal,
            schedule="daily",
            time=dialog.time.time().toString("HH:mm"),
            urgency=dialog.urgency.value(),
        )
        if not self.routines.add_if_unique(routine):
            self._say("Já existe uma rotina com essa descrição.")
            return

        self._say(
            f"Rotina criada. Todos os dias às {routine.time}, "
            f"eu vou lembrar: {routine.goal}."
        )

    def manage_routines(self) -> None:
        if not self.routines.routines:
            QMessageBox.information(
                self.widget,
                "Rotinas",
                "Nenhuma rotina foi cadastrada.",
            )
            return

        labels = [
            f"{routine.goal} — {self.routines.describe(routine)}"
            + ("" if routine.enabled else " [desativada]")
            for routine in self.routines.routines
        ]
        selected, ok = QInputDialog.getItem(
            self.widget,
            "Gerenciar rotinas",
            "Selecione uma rotina para ativar/desativar ou remover:",
            labels,
            0,
            False,
        )
        if not ok or not selected:
            return

        index = labels.index(selected)
        routine = self.routines.routines[index]

        box = QMessageBox(self.widget)
        box.setWindowTitle("Gerenciar rotina")
        box.setText(f"{routine.goal}\n\n{self.routines.describe(routine)}")
        toggle = box.addButton(
            "Desativar" if routine.enabled else "Ativar",
            QMessageBox.ButtonRole.ActionRole,
        )
        remove = box.addButton(
            "Remover",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.exec()

        if box.clickedButton() is toggle:
            self.routines.toggle(routine.id)
            state = "ativada" if routine.enabled else "desativada"
            self._say(f"Rotina {state}: {routine.goal}.")
        elif box.clickedButton() is remove:
            self.routines.remove(routine.id)
            self._say(f"Rotina removida: {routine.goal}.")

    def _poll_routines(self) -> None:
        for routine in self.routines.get_due_routines():
            prefix = "Hora da rotina."
            if routine.urgency >= 8:
                prefix = "Isso é importante. Hora da rotina."
            elif routine.urgency >= 5:
                prefix = "Lembrete de rotina."
            self._say(f"{prefix} {routine.goal}")

    # ------------------------------------------------------------------
    # Main monitoring loop
    # ------------------------------------------------------------------

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        self._last_poll = time.monotonic()

    def _save_activity_if_changed(
        self,
        session_id: str | None,
        classified,
    ) -> None:
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

        # Proactive systems work even when no study session is active.
        self._poll_routines()
        self._poll_directives()

        window = self.monitor.sample()
        rule_violated = self._poll_standing_rules(window)
        classified = self.classifier.classify(window)

        # A permanent rule violation is considered a distraction during an
        # active study session even if the app is otherwise unknown.
        if rule_violated:
            classified = ClassifiedActivity(
                window=window,
                kind=ActivityKind.DISTRACTION,
                reason="matched an active standing rule",
            )

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
