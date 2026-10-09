from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QInputDialog,
    QMessageBox,
)

from desktop_study_companion.accountability.directives import DirectiveManager
from desktop_study_companion.accountability.escalation import (
    LimitedLockdown,
    SessionEscalationPolicy,
)
from desktop_study_companion.accountability.engine import (
    AccountabilityEngine,
    AccountabilityPolicy,
)
from desktop_study_companion.accountability.models import (
    Intervention,
    InterventionKind,
)
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
from desktop_study_companion.config.writer import save_config
from desktop_study_companion.desktop.interventions import (
    DesktopInterventionController,
    InterventionPermissionStore,
    WindowsWindowBackend,
)
from desktop_study_companion.memory.analytics import StudyAnalytics
from desktop_study_companion.memory.exporter import (
    create_backup_zip,
    export_csv_directory,
)
from desktop_study_companion.memory.sqlite_store import SQLiteMemoryStore
from desktop_study_companion.personality.models import Personality
from desktop_study_companion.personality.renderer import PersonalityRenderer
from desktop_study_companion.runtime_paths import (
    application_root,
    data_directory,
    external_config_path,
)
from desktop_study_companion.routines.manager import RoutineManager
from desktop_study_companion.routines.models import Routine
from desktop_study_companion.study.manager import StudySessionManager
from desktop_study_companion.ui.companion_widget import CompanionWidget
from desktop_study_companion.ui.directive_dialog import DirectiveDialog
from desktop_study_companion.ui.history_dialog import HistoryDialog
from desktop_study_companion.ui.intervention_settings_dialog import (
    InterventionSettingsDialog,
)
from desktop_study_companion.ui.routine_dialog import RoutineDialog
from desktop_study_companion.ui.session_dialog import SessionDialog
from desktop_study_companion.ui.settings_dialog import SettingsDialog
from desktop_study_companion.ui.standing_rule_dialog import StandingRuleDialog
from desktop_study_companion.voice.windows_sapi import WindowsSapiTTS
from desktop_study_companion import __version__


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
        self.data_dir = data_directory()
        self.directives = DirectiveManager(self.data_dir / "directives.json")
        self.standing_rules = StandingRuleManager(
            self.data_dir / "standing_rules.json"
        )
        self.routines = RoutineManager(self.data_dir / "routines.json")
        self.session_escalation = SessionEscalationPolicy()
        self.lockdown = LimitedLockdown()
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
        self.memory = SQLiteMemoryStore(self.data_dir / "companion.db")
        self.analytics = StudyAnalytics(self.memory.path)
        self.widget = CompanionWidget(
            config.personality.name,
            config.avatar,
        )
        self.intervention_permissions = InterventionPermissionStore(
            self.data_dir / "intervention_permissions.json"
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
        self.widget.end_lockdown_requested.connect(self.end_lockdown)
        self.widget.history_requested.connect(self.show_history)
        self.widget.export_csv_requested.connect(self.export_csv)
        self.widget.backup_requested.connect(self.create_backup)
        self.widget.settings_requested.connect(self.open_settings)
        self.widget.pause_monitoring_requested.connect(self.set_paused)
        self.widget.quit_requested.connect(self.shutdown)

    def start(self) -> None:
        self.widget.show()
        self.timer.start()

    def _say(
        self,
        text: str,
        *,
        voice: bool = True,
        avatar_state: str | None = None,
    ) -> None:
        self.widget.say(text)
        if avatar_state:
            self.widget.set_avatar_expression(avatar_state)
        self.widget.animate_avatar_speech(text)
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

        self.lockdown.clear()
        session = self.sessions.start(dialog.goal.text(), dialog.minutes.value())
        self.memory.save_session(session)
        self._last_session_save_at = time.monotonic()
        self._last_activity_key = None
        self._last_intervention_kind = InterventionKind.NONE
        self._say(
            f"Combinado: {session.planned_minutes} minutos para {session.goal}. "
            "Eu vou acompanhar.",
            avatar_state="happy",
        )

    def finish_session(self) -> None:
        if self.sessions.session is None:
            self._say("Não há sessão ativa.")
            return

        session = self.sessions.finish()
        self.lockdown.clear()
        self.memory.save_session(session)
        focused = round(session.focused_seconds / 60, 1)
        distracted = round(session.distracted_seconds / 60, 1)
        self._say(
            f"Sessão encerrada. Foco classificado: {focused} minutos; "
            f"distração: {distracted} minutos."
            + self._behavioral_insight_suffix(),
            avatar_state="happy",
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
            avatar_state = (
                "angry" if decision.severity >= 3 else
                "relaxed" if decision.severity == 2 else
                "neutral"
            )
            self._say(message, avatar_state=avatar_state)
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
                else:
                    message += " Eu fechei a distração."
                self._audit_desktop_action(
                    result,
                    violation.window,
                    reason=f"standing rule: {violation.rule.description}",
                    severity=violation.rule.catch_count,
                    rule_id=violation.rule.id,
                )
            state = "angry" if violation.rule.catch_count >= 2 else "neutral"
            self._say(message, avatar_state=state)

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
        if not values.allow_lockdown or not values.allow_session_escalation:
            self.lockdown.clear()

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
        self.lockdown.clear()
        self._say(
            "Intervenções desativadas imediatamente. "
            "Não vou minimizar nem fechar nenhuma janela."
        )

    def end_lockdown(self) -> None:
        if not self.lockdown.is_active():
            self._say("Nenhum lockdown está ativo.")
            return
        self.lockdown.clear()
        self._say(
            "Lockdown encerrado. As permissões gerais continuam como estavam."
        )

    def _audit_desktop_action(
        self,
        result,
        window,
        *,
        reason: str,
        severity: int,
        rule_id: str | None = None,
    ) -> None:
        if not result.performed:
            return

        session_id = (
            self.sessions.session.id
            if self.sessions.session is not None
            else None
        )
        if result.requested_action == "minimize_and_nag":
            intervention_kind = InterventionKind.MINIMIZE_DISTRACTION
        else:
            intervention_kind = InterventionKind.CLOSE_DISTRACTION

        payload = {
            "process_name": window.process_name,
            "window_title": window.title,
            "response": result.requested_action,
            "result": result.reason,
        }
        if rule_id:
            payload["rule_id"] = rule_id

        self.memory.save_intervention(
            session_id,
            Intervention(
                intervention_kind,
                max(1, min(5, int(severity))),
                reason,
            ),
            payload=payload,
        )

    def _apply_session_intervention(
        self,
        intervention: Intervention,
        classified: ClassifiedActivity,
    ) -> str:
        permissions = self.intervention_permissions.permissions
        response = self.session_escalation.response_for(
            intervention,
            permissions,
            lockdown_active=False,
        )
        result = self.desktop_interventions.perform(
            response,
            classified.window,
        )
        self._audit_desktop_action(
            result,
            classified.window,
            reason="automatic session escalation",
            severity=intervention.severity,
        )

        suffix = ""
        if result.performed:
            if result.requested_action == "minimize_and_nag":
                suffix = " Eu minimizei a distração."
            elif result.requested_action == "close_and_nag":
                suffix = " Eu fechei a distração."

        if (
            intervention.severity >= 4
            and permissions.enabled
            and permissions.allow_session_escalation
            and permissions.allow_lockdown
            and (permissions.allow_minimize or permissions.allow_close)
            and not self.lockdown.is_active()
        ):
            self.lockdown.activate(permissions.lockdown_minutes)
            suffix += (
                f" Modo de foco limitado ativado por "
                f"{permissions.lockdown_minutes} minutos."
            )

        return suffix

    def _apply_lockdown_if_needed(
        self,
        classified: ClassifiedActivity,
    ) -> bool:
        if not self.sessions.active:
            self.lockdown.clear()
            return False
        if classified.kind != ActivityKind.DISTRACTION:
            return False
        if not self.lockdown.is_active():
            return False

        key = (
            f"{classified.window.process_name.casefold()}|"
            f"{classified.window.title.casefold()}"
        )
        if not self.lockdown.should_act(key):
            return False

        permissions = self.intervention_permissions.permissions
        response = self.session_escalation.response_for(
            Intervention(
                InterventionKind.INSISTENT_CHALLENGE,
                4,
                "limited lockdown active",
            ),
            permissions,
            lockdown_active=True,
        )
        result = self.desktop_interventions.perform(
            response,
            classified.window,
        )
        self._audit_desktop_action(
            result,
            classified.window,
            reason="limited lockdown",
            severity=4,
        )
        if result.performed:
            remaining = max(1, self.lockdown.remaining_seconds() // 60)
            self._say(
                f"Modo de foco ativo. A distração foi interrompida. "
                f"Restam cerca de {remaining} minutos."
            )
        return result.performed

    # ------------------------------------------------------------------
    # Main settings
    # ------------------------------------------------------------------

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self.widget)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_config = dialog.values()
        try:
            save_config(new_config, external_config_path())
        except Exception as exc:
            QMessageBox.critical(
                self.widget,
                "Configuração inválida",
                f"Não foi possível salvar as configurações:\n\n{exc}",
            )
            return

        self._apply_runtime_config(new_config)
        self._say("Configurações salvas e aplicadas.")

    def _apply_runtime_config(self, new_config: AppConfig) -> None:
        self.config = new_config

        self.classifier = ActivityClassifier(
            productive_keywords=set(
                new_config.activity.productive_keywords
            ),
            neutral_keywords=set(new_config.activity.neutral_keywords),
            distraction_keywords=set(
                new_config.activity.distraction_keywords
            ),
        )

        self.accountability = AccountabilityEngine(
            AccountabilityPolicy(
                gentle_after_seconds=(
                    new_config.accountability.gentle_after_seconds
                ),
                firm_after_seconds=(
                    new_config.accountability.firm_after_seconds
                ),
                direct_after_seconds=(
                    new_config.accountability.direct_after_seconds
                ),
                insistent_after_seconds=(
                    new_config.accountability.insistent_after_seconds
                ),
            )
        )

        self.personality = PersonalityRenderer(
            Personality(
                warmth=new_config.personality.warmth,
                sarcasm=new_config.personality.sarcasm,
                strictness=new_config.personality.strictness,
                patience=new_config.personality.patience,
                humor=new_config.personality.humor,
                initiative=new_config.personality.initiative,
            ),
            name=new_config.personality.name,
        )
        self.widget.name = new_config.personality.name
        self.widget.apply_avatar_config(new_config.avatar)

        if self.voice is not None:
            self.voice.close()
            self.voice = None
        if new_config.voice.enabled:
            self.voice = WindowsSapiTTS(
                rate=new_config.voice.rate,
                volume=new_config.voice.volume,
            )

        self.timer.setInterval(new_config.monitor.poll_interval_ms)

    # ------------------------------------------------------------------
    # History, analytics and backups
    # ------------------------------------------------------------------

    def show_history(self) -> None:
        overview = self.analytics.overview(30)
        sessions = self.analytics.sessions(100)
        dialog = HistoryDialog(overview, sessions, self.widget)
        dialog.exec()

    def export_csv(self) -> None:
        destination = QFileDialog.getExistingDirectory(
            self.widget,
            "Escolha a pasta para exportar os CSVs",
            str(application_root()),
        )
        if not destination:
            return

        try:
            created = export_csv_directory(
                self.memory.path,
                destination,
            )
        except Exception as exc:
            QMessageBox.critical(
                self.widget,
                "Falha na exportação",
                f"Não foi possível exportar os dados:\n\n{exc}",
            )
            return

        self._say(
            f"Exportação concluída. {len(created)} arquivos CSV foram criados."
        )

    def create_backup(self) -> None:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        suggested = str(
            application_root()
            / f"desktop-study-companion-backup-{timestamp}.zip"
        )
        destination, _ = QFileDialog.getSaveFileName(
            self.widget,
            "Salvar backup",
            suggested,
            "Arquivo ZIP (*.zip)",
        )
        if not destination:
            return
        if not destination.casefold().endswith(".zip"):
            destination += ".zip"

        config_path = external_config_path()
        try:
            backup = create_backup_zip(
                self.memory.path,
                self.memory.path.parent,
                destination,
                config_path=config_path,
                app_version=__version__,
            )
        except Exception as exc:
            QMessageBox.critical(
                self.widget,
                "Falha no backup",
                f"Não foi possível criar o backup:\n\n{exc}",
            )
            return

        self._say(f"Backup criado: {backup.name}.")

    def _behavioral_insight_suffix(self) -> str:
        overview = self.analytics.overview(30)
        if overview.session_count < 3 or not overview.insights:
            return ""
        return f" {overview.insights[0]}"

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
            self._say(
                f"{prefix} {routine.goal}",
                avatar_state="neutral",
            )

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

        lockdown_acted = self._apply_lockdown_if_needed(classified)
        lockdown_active = self.lockdown.is_active()

        self._save_session_periodically(now)

        if not self.sessions.active:
            session = self.sessions.session
            if session:
                self.lockdown.clear()
                self.memory.save_session(session)
                self._say(
                    f"Tempo cumprido para {session.goal}. "
                    "Sessão registrada. Bom trabalho."
                    + self._behavioral_insight_suffix()
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
        if not lockdown_active:
            message += self._apply_session_intervention(
                intervention,
                classified,
            )
        if not lockdown_acted:
            state = {
                InterventionKind.GENTLE_REMINDER: "neutral",
                InterventionKind.FIRM_REMINDER: "relaxed",
                InterventionKind.DIRECT_CHALLENGE: "angry",
                InterventionKind.INSISTENT_CHALLENGE: "angry",
            }.get(intervention.kind, "neutral")
            self._say(message, avatar_state=state)
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
        self.lockdown.clear()
        self.timer.stop()
        if self.voice is not None:
            self.voice.close()
        self.memory.close()
        self.widget.shutdown_avatar()
        self.app.quit()
