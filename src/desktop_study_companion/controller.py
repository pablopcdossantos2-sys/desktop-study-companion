from __future__ import annotations

import logging
import os
import random
import time

from PySide6.QtCore import QObject, QThreadPool, QTimer
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
from desktop_study_companion.brain.service import BrainService
from desktop_study_companion.brain.worker import BrainChatWorker
from desktop_study_companion.config.models import AppConfig
from desktop_study_companion.config.writer import (
    brain_transport_security_issue,
    save_config,
)
from desktop_study_companion.diagnostics import (
    diagnostic_summary,
    log_directory,
)
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
    docs_directory,
    external_config_path,
)
from desktop_study_companion.routines.manager import RoutineManager
from desktop_study_companion.routines.models import Routine
from desktop_study_companion.study.manager import StudySessionManager
from desktop_study_companion.ui.chat_dialog import ChatDialog
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
from desktop_study_companion.ui.tutorial_dialog import TutorialDialog
from desktop_study_companion.ui.windowing import (
    exec_top_level_dialog,
    prepare_top_level_window,
)
from desktop_study_companion.voice.audio_capture import (
    AudioCaptureError,
    MicrophoneRecorder,
)
from desktop_study_companion.voice.faster_whisper_stt import FasterWhisperSTT
from desktop_study_companion.voice.stt_worker import SttWorker
from desktop_study_companion.voice.factory import create_tts_engine
from desktop_study_companion.voice.piper_tts import PiperNeuralTTS
from desktop_study_companion import __version__


logger = logging.getLogger("desktop_study_companion.controller")


class ApplicationController(QObject):
    SESSION_SAVE_INTERVAL_SECONDS = 10.0
    WAKE_GAP_SECONDS = RoutineManager.WAKE_GAP_MINUTES * 60.0

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
        self.voice = create_tts_engine(config.voice, self.data_dir)
        self.memory = SQLiteMemoryStore(self.data_dir / "companion.db")
        orphaned = self.memory.reconcile_orphaned_sessions()
        if orphaned:
            logger.warning("Reconciled orphaned study sessions count=%s", orphaned)
        self.analytics = StudyAnalytics(self.memory.path)
        self.brain = BrainService(config, self.memory, self.analytics)
        self.thread_pool = QThreadPool.globalInstance()
        self._brain_workers: set[BrainChatWorker] = set()
        self._stt_workers: set[SttWorker] = set()
        self.chat_dialog: ChatDialog | None = None
        self.recorder = MicrophoneRecorder(
            output_dir=self.data_dir / "temp",
            device_index=config.speech_input.microphone_device,
        )
        self.stt = self._create_stt_provider(config)
        self._ptt_timer = QTimer(self)
        self._ptt_timer.setSingleShot(True)
        self._ptt_timer.timeout.connect(self._stop_push_to_talk)
        self._motivation_timer = QTimer(self)
        self._motivation_timer.setSingleShot(True)
        self._motivation_timer.timeout.connect(
            self._safe_proactive_motivation
        )
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
        self._shutting_down = False
        self._voice_preview: PiperNeuralTTS | None = None

        self.timer = QTimer(self)
        self.timer.setInterval(config.monitor.poll_interval_ms)
        self.timer.timeout.connect(self._safe_poll)

        self.widget.chat_requested.connect(self.open_chat)
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
        self.widget.tutorial_requested.connect(self.show_tutorial)
        self.widget.open_logs_requested.connect(self.open_logs_directory)
        self.widget.copy_diagnostics_requested.connect(
            self.copy_diagnostic_summary
        )
        self.widget.pause_monitoring_requested.connect(self.set_paused)
        self.widget.quit_requested.connect(self.shutdown)

    def start(self) -> None:
        self.widget.show()
        self.timer.start()
        self._schedule_next_motivation()

    def open_logs_directory(self) -> None:
        try:
            os.startfile(str(log_directory()))
        except Exception as exc:
            QMessageBox.warning(
                self.widget,
                "Não foi possível abrir os logs",
                f"A pasta de logs não pôde ser aberta:\n\n{exc}",
            )

    def copy_diagnostic_summary(self) -> None:
        summary = diagnostic_summary()
        self.app.clipboard().setText(summary)
        QMessageBox.information(
            self.widget,
            "Diagnóstico copiado",
            "Um resumo técnico sem histórico de janelas foi copiado "
            "para a área de transferência.",
        )

    def show_tutorial(self, key: str) -> None:
        tutorials = {
            "getting_started": (
                "Primeiros passos",
                "TUTORIAL-INSTALACAO-WINDOWS.md",
            ),
            "brain": (
                "Configurar Cérebro local com Ollama",
                "TUTORIAL-CEREBRO-LOCAL-OLLAMA.md",
            ),
            "voice": (
                "Voz e conversa por push-to-talk",
                "VOICE-CONVERSATION.md",
            ),
            "piper": (
                "Configurar e diagnosticar a voz Piper",
                "TUTORIAL-PIPER.md",
            ),
            "avatar": (
                "Diagnóstico do avatar",
                "DIAGNOSTICS.md",
            ),
        }
        title, filename = tutorials.get(
            key,
            tutorials["getting_started"],
        )
        dialog = TutorialDialog(
            title,
            docs_directory() / filename,
            None,
        )
        exec_top_level_dialog(dialog)

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

    def _schedule_next_motivation(self) -> None:
        self._motivation_timer.stop()
        p = self.config.proactivity
        if not p.enabled or not p.motivational_messages:
            return
        minutes = random.randint(
            max(1, p.min_interval_minutes),
            max(p.min_interval_minutes, p.max_interval_minutes),
        )
        self._motivation_timer.start(minutes * 60 * 1000)

    def _safe_proactive_motivation(self) -> None:
        try:
            self._proactive_motivation()
        except Exception:
            logger.exception(
                "Proactive motivation cycle failed; keeping app alive"
            )
            self._schedule_next_motivation()

    def _proactive_motivation(self) -> None:
        try:
            if (
                self._paused
                or self.recorder.recording
                or bool(self._brain_workers)
                or (self.voice is not None and self.voice.is_speaking)
            ):
                return

            goal = None
            if self.sessions.active and self.sessions.session is not None:
                goal = self.sessions.session.goal
            self._say(
                self.personality.motivation_message(goal),
                avatar_state="happy",
            )
        finally:
            self._schedule_next_motivation()

    # ------------------------------------------------------------------
    # Conversational brain
    # ------------------------------------------------------------------

    def _brain_session_context(self) -> dict:
        session = self.sessions.session
        if session is None or not self.sessions.active:
            return {"active": False}
        return {
            "active": True,
            "goal": session.goal,
            "state": session.state.value,
            "planned_minutes": session.planned_minutes,
            "focused_seconds": session.focused_seconds,
            "distracted_seconds": session.distracted_seconds,
        }

    def open_chat(self) -> None:
        if not self.brain.ready:
            box = QMessageBox(self.widget)
            box.setWindowTitle("Cérebro conversacional ainda não configurado")
            box.setIcon(QMessageBox.Icon.Information)
            box.setText(
                "Para conversar, primeiro configure o Cérebro. "
                "O caminho recomendado para começar é usar Ollama local, "
                "sem API paga."
            )
            box.setInformativeText(
                "Você pode abrir diretamente as Configurações ou seguir "
                "o tutorial didático passo a passo."
            )
            open_settings = box.addButton(
                "Abrir Configurações",
                QMessageBox.ButtonRole.ActionRole,
            )
            open_tutorial = box.addButton(
                "Abrir tutorial",
                QMessageBox.ButtonRole.HelpRole,
            )
            box.addButton(QMessageBox.StandardButton.Cancel)
            exec_top_level_dialog(box)
            if box.clickedButton() is open_settings:
                self.open_settings()
            elif box.clickedButton() is open_tutorial:
                self.show_tutorial("brain")
            return

        if self.chat_dialog is None:
            self.chat_dialog = ChatDialog(
                self.config.personality.name,
                None,
            )
            prepare_top_level_window(self.chat_dialog, modal=False)
            self.chat_dialog.message_submitted.connect(
                self._submit_chat_message
            )
            self.chat_dialog.clear_requested.connect(
                self.clear_chat_history
            )
            self.chat_dialog.push_to_talk_started.connect(
                self._start_push_to_talk
            )
            self.chat_dialog.push_to_talk_finished.connect(
                self._stop_push_to_talk
            )

        self.chat_dialog.character_name = self.config.personality.name
        self.chat_dialog.setWindowTitle(
            f"Conversar com {self.config.personality.name}"
        )
        self.chat_dialog.load_history(
            self.memory.load_conversation_messages(
                limit=self.config.brain.history_messages
            )
        )
        prepare_top_level_window(self.chat_dialog, modal=False)
        self.chat_dialog.show()
        self.chat_dialog.raise_()
        self.chat_dialog.activateWindow()

    def _create_stt_provider(self, config: AppConfig):
        speech = config.speech_input
        if not speech.enabled:
            return None
        return FasterWhisperSTT(
            model_name=speech.model,
            language=speech.language,
            device=speech.device,
            compute_type=speech.compute_type,
            download_root=self.data_dir / "models" / "faster-whisper",
        )

    def _start_push_to_talk(self) -> None:
        if self.chat_dialog is None:
            return
        if not self.config.speech_input.enabled or self.stt is None:
            self.chat_dialog.append_status(
                "Push-to-talk está desativado. "
                "Use Configurações > Microfone."
            )
            box = QMessageBox(self.chat_dialog)
            box.setWindowTitle("Microfone ainda não configurado")
            box.setText(
                "O push-to-talk precisa ser ativado em "
                "Configurações > Microfone."
            )
            tutorial = box.addButton(
                "Abrir tutorial",
                QMessageBox.ButtonRole.HelpRole,
            )
            settings = box.addButton(
                "Abrir Configurações",
                QMessageBox.ButtonRole.ActionRole,
            )
            box.addButton(QMessageBox.StandardButton.Cancel)
            exec_top_level_dialog(box)
            if box.clickedButton() is tutorial:
                self.show_tutorial("voice")
            elif box.clickedButton() is settings:
                self.open_settings()
            return
        if self.recorder.recording:
            return

        if self.voice is not None:
            self.voice.stop()

        try:
            self.recorder.start()
        except Exception as exc:
            self.chat_dialog.append_status(
                "Não foi possível iniciar o microfone: " + str(exc)
            )
            return

        self.chat_dialog.set_recording(True)
        self.chat_dialog.append_status(
            "Gravando… solte o botão para transcrever."
        )
        self._ptt_timer.start(
            self.config.speech_input.max_record_seconds * 1000
        )

    def _stop_push_to_talk(self) -> None:
        if self.chat_dialog is None or not self.recorder.recording:
            return

        self._ptt_timer.stop()
        self.chat_dialog.set_recording(False)
        self.chat_dialog.set_busy(True)

        try:
            audio_path = self.recorder.stop_to_wav()
        except AudioCaptureError as exc:
            self.chat_dialog.append_status(str(exc))
            self.chat_dialog.set_busy(False)
            return
        except Exception as exc:
            self.chat_dialog.append_status(
                "Falha ao finalizar gravação: " + str(exc)
            )
            self.chat_dialog.set_busy(False)
            return

        if self.stt is None:
            audio_path.unlink(missing_ok=True)
            self.chat_dialog.append_status(
                "Reconhecimento de fala não está disponível."
            )
            self.chat_dialog.set_busy(False)
            return

        self.chat_dialog.append_status(
            "Transcrevendo localmente… na primeira vez o modelo pode ser baixado."
        )
        worker = SttWorker(self.stt, audio_path)
        self._stt_workers.add(worker)
        worker.signals.succeeded.connect(
            lambda text, w=worker: self._stt_succeeded(w, text)
        )
        worker.signals.failed.connect(
            lambda error, w=worker: self._stt_failed(w, error)
        )
        self.thread_pool.start(worker)

    def _stt_succeeded(self, worker: SttWorker, text: str) -> None:
        self._stt_workers.discard(worker)
        if self.chat_dialog is None:
            return

        if self.config.speech_input.auto_send:
            self.chat_dialog.append_user(text)
            self._submit_chat_message(text)
        else:
            self.chat_dialog.set_busy(False)
            self.chat_dialog.set_transcript_draft(text)
            self.chat_dialog.append_status(
                "Transcrição pronta. Revise e clique em Enviar."
            )

    def _stt_failed(self, worker: SttWorker, error: str) -> None:
        self._stt_workers.discard(worker)
        if self.chat_dialog is not None:
            self.chat_dialog.append_status(
                "Falha no reconhecimento de fala: " + error
            )
            self.chat_dialog.set_busy(False)

    def _submit_chat_message(self, text: str) -> None:
        worker = BrainChatWorker(
            self.brain,
            text,
            self._brain_session_context(),
        )
        self._brain_workers.add(worker)
        worker.signals.succeeded.connect(
            lambda answer, w=worker: self._chat_succeeded(w, answer)
        )
        worker.signals.failed.connect(
            lambda error, w=worker: self._chat_failed(w, error)
        )
        self.thread_pool.start(worker)

    def _chat_succeeded(
        self,
        worker: BrainChatWorker,
        answer: str,
    ) -> None:
        self._brain_workers.discard(worker)
        if self.chat_dialog is not None:
            self.chat_dialog.append_assistant(answer)
            self.chat_dialog.set_busy(False)
        self._say(answer, avatar_state="happy")

    def _chat_failed(
        self,
        worker: BrainChatWorker,
        error: str,
    ) -> None:
        self._brain_workers.discard(worker)
        if self.chat_dialog is not None:
            self.chat_dialog.append_status(
                "Falha ao consultar o cérebro: " + error
            )
            self.chat_dialog.set_busy(False)

    def clear_chat_history(self) -> None:
        self.brain.clear_history()
        if self.chat_dialog is not None:
            self.chat_dialog.load_history([])
            self.chat_dialog.append_status(
                "Histórico local desta conversa foi apagado."
            )

    # ------------------------------------------------------------------
    # Study sessions
    # ------------------------------------------------------------------

    def start_session(self) -> None:
        if self.sessions.active:
            self._say("Já existe uma sessão em andamento.")
            return

        dialog = SessionDialog(None)
        if exec_top_level_dialog(dialog) != QDialog.DialogCode.Accepted:
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
        if not self.sessions.active:
            self._say("Não há sessão ativa.")
            return

        session = self.sessions.finish()
        self.lockdown.clear()
        self.memory.save_session(session)
        focused = round(session.focused_seconds / 60, 1)
        distracted = round(session.distracted_seconds / 60, 1)
        completed = session.state.value == "completed"
        prefix = (
            "Sessão concluída."
            if completed
            else "Sessão interrompida e registrada como abandonada."
        )
        self._say(
            f"{prefix} Foco classificado: {focused} minutos; "
            f"distração: {distracted} minutos."
            + self._behavioral_insight_suffix(),
            avatar_state="happy" if completed else "neutral",
        )

    # ------------------------------------------------------------------
    # Persistent directives / commitments
    # ------------------------------------------------------------------

    def add_directive(self) -> None:
        dialog = DirectiveDialog(None)
        if exec_top_level_dialog(dialog) != QDialog.DialogCode.Accepted:
            return

        goal = dialog.goal.text().strip()
        if not goal:
            QMessageBox.warning(
                self.widget,
                "Compromisso sem descrição",
                "Escreva o compromisso que deverá ser acompanhado.",
            )
            return

        active_ids = {item.id for item in self.directives.active}
        directive = self.directives.add(
            goal,
            dialog.urgency.value(),
            delay_seconds=dialog.delay_minutes.value() * 60,
        )
        if directive.id in active_ids:
            self._say(f"Esse compromisso já estava registrado: {directive.goal}.")
        else:
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
        exec_top_level_dialog(box)

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
            # Advance the nag schedule before presentation. If TTS/UI fails,
            # the same overdue directive will not break every monitoring tick.
            self.directives.record_nag(directive, message)
            self._say(message, avatar_state=avatar_state)

    # ------------------------------------------------------------------
    # Standing rules
    # ------------------------------------------------------------------

    def add_standing_rule(self) -> None:
        dialog = StandingRuleDialog(None)
        if exec_top_level_dialog(dialog) != QDialog.DialogCode.Accepted:
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

        existing_ids = {item.id for item in self.standing_rules.rules}
        rule = self.standing_rules.add(
            StandingRule(
                description=description,
                patterns=patterns,
                response=dialog.response_code(),
                cooldown_s=dialog.cooldown.value(),
            )
        )
        if rule.id in existing_ids:
            self._say(f"Essa regra permanente já existia: {rule.description}.")
        else:
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
        exec_top_level_dialog(box)

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
            if not violation.action_due:
                continue
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
            None,
        )
        if exec_top_level_dialog(dialog) != QDialog.DialogCode.Accepted:
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
        dialog = SettingsDialog(self.config, None)
        dialog.piper_test_requested.connect(self._preview_piper_voice)
        if exec_top_level_dialog(dialog) != QDialog.DialogCode.Accepted:
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

        security_issue = brain_transport_security_issue(new_config)
        if security_issue:
            new_config.brain.enabled = False
            QMessageBox.warning(
                self.widget,
                "Cérebro desativado por segurança",
                security_issue
                + "\n\nAs demais configurações foram preservadas e aplicadas.",
            )

        self._apply_runtime_config(new_config)
        self._say("Configurações salvas e aplicadas.")

    def _preview_piper_voice(
        self,
        model_id: str,
        length_scale: float,
        volume: int,
    ) -> None:
        if self._voice_preview is not None:
            self._voice_preview.close()
        self._voice_preview = PiperNeuralTTS(
            model_id=model_id,
            model_dir=self.data_dir / "models" / "piper",
            volume=volume,
            length_scale=length_scale,
            fallback=None,
        )
        self.widget.say(
            "Testando a voz Piper selecionada. "
            "No primeiro teste, o modelo pode precisar ser baixado."
        )
        self._voice_preview.speak(
            "Olá! Este é um teste da minha voz neural Piper."
        )

    def _apply_runtime_config(self, new_config: AppConfig) -> None:
        old_config = self.config
        self.config = new_config
        self.brain.update_config(new_config)
        if old_config.speech_input != new_config.speech_input:
            if self.recorder.recording:
                self.recorder.cancel()
            self.recorder.update_device(
                new_config.speech_input.microphone_device
            )
            self.stt = self._create_stt_provider(new_config)

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

        if self._voice_preview is not None:
            self._voice_preview.close()
            self._voice_preview = None
        if self.voice is not None:
            self.voice.close()
            self.voice = None
        self.voice = create_tts_engine(new_config.voice, self.data_dir)

        self.timer.setInterval(new_config.monitor.poll_interval_ms)
        self._schedule_next_motivation()

    # ------------------------------------------------------------------
    # History, analytics and backups
    # ------------------------------------------------------------------

    def show_history(self) -> None:
        overview = self.analytics.overview(30)
        sessions = self.analytics.sessions(100)
        dialog = HistoryDialog(overview, sessions, None)
        exec_top_level_dialog(dialog)

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
        dialog = RoutineDialog(None)
        if exec_top_level_dialog(dialog) != QDialog.DialogCode.Accepted:
            return

        goal = dialog.goal.text().strip()
        if not goal:
            QMessageBox.warning(
                self.widget,
                "Rotina sem descrição",
                "Escreva o que a personagem deve lembrar.",
            )
            return

        schedule = str(dialog.schedule.currentData() or "daily")
        routine = Routine(
            goal=goal,
            schedule=schedule,
            time=(
                dialog.time.time().toString("HH:mm")
                if schedule in {"daily", "weekly"}
                else None
            ),
            day=(
                str(dialog.day.currentData())
                if schedule == "weekly"
                else None
            ),
            interval_hours=(
                float(dialog.interval_hours.value())
                if schedule == "interval"
                else None
            ),
            urgency=dialog.urgency.value(),
        )
        if not self.routines.add_if_unique(routine):
            self._say(
                "Essa mesma rotina, com a mesma agenda, já está cadastrada."
            )
            return

        self._say(
            f"Rotina criada: {routine.goal}. "
            f"{self.routines.describe(routine)}."
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
        exec_top_level_dialog(box)

        if box.clickedButton() is toggle:
            self.routines.toggle(routine.id)
            state = "ativada" if routine.enabled else "desativada"
            self._say(f"Rotina {state}: {routine.goal}.")
        elif box.clickedButton() is remove:
            self.routines.remove(routine.id)
            self._say(f"Rotina removida: {routine.goal}.")

    def _poll_routines(self, *, wake_event: bool = False) -> None:
        for routine in self.routines.get_due_routines(wake_event=wake_event):
            prefix = "Hora da rotina."
            if routine.urgency >= 8:
                prefix = "Isso é importante. Hora da rotina."
            elif routine.urgency >= 5:
                prefix = "Lembrete de rotina."
            self._say(
                f"{prefix} {routine.goal}",
                avatar_state="neutral",
            )

    def _safe_poll_routines(self, *, wake_event: bool = False) -> None:
        try:
            self._poll_routines(wake_event=wake_event)
        except Exception:
            logger.exception(
                "Routine polling failed; continuing core monitoring"
            )

    def _safe_poll_directives(self) -> None:
        try:
            self._poll_directives()
        except Exception:
            logger.exception(
                "Directive polling failed; continuing core monitoring"
            )

    def _safe_poll_standing_rules(self, window) -> bool:
        try:
            return self._poll_standing_rules(window)
        except Exception:
            logger.exception(
                "Standing-rule polling failed; continuing core monitoring"
            )
            return False

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

    def _safe_poll(self) -> None:
        try:
            self._poll()
        except Exception:
            logger.exception(
                "Monitoring cycle failed; keeping application alive"
            )

    def _poll(self) -> None:
        now = time.monotonic()
        elapsed = max(0.0, now - self._last_poll)
        self._last_poll = now
        wake_event = elapsed >= self.WAKE_GAP_SECONDS
        suspension_threshold = max(
            5.0,
            (self.config.monitor.poll_interval_ms / 1000.0) * 5.0,
        )
        if elapsed > suspension_threshold:
            logger.info(
                "Large monitoring gap ignored elapsed=%.2fs threshold=%.2fs",
                elapsed,
                suspension_threshold,
            )
            elapsed = self.config.monitor.poll_interval_ms / 1000.0

        if self._paused:
            return

        # Proactive systems are isolated from the core monitoring loop.
        # A wake routine is only considered after a real monitoring gap,
        # never merely because the application has just started.
        self._safe_poll_routines(wake_event=wake_event)
        self._safe_poll_directives()

        window = self.monitor.sample()
        rule_violated = self._safe_poll_standing_rules(window)
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
        if self._shutting_down:
            return
        self._shutting_down = True
        logger.info("Clean shutdown requested by user")
        try:
            if self.sessions.active:
                self.memory.save_session(self.sessions.finish())
            elif self.sessions.session is not None:
                self.memory.save_session(self.sessions.session)
            self.lockdown.clear()
            self.timer.stop()
            self._ptt_timer.stop()
            self._motivation_timer.stop()
            if self.recorder.recording:
                self.recorder.cancel()
            if self._voice_preview is not None:
                self._voice_preview.close()
                self._voice_preview = None
            if self.voice is not None:
                self.voice.close()
                self.voice = None
            if self.chat_dialog is not None:
                self.chat_dialog.close()
                self.chat_dialog = None
            self.memory.close()
            self.widget.shutdown_avatar()
        except Exception:
            logger.exception("Error while shutting down cleanly")
        finally:
            self.app.quit()
