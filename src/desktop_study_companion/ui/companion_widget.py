from __future__ import annotations

import logging

from PySide6.QtCore import QPoint, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QCursor, QMouseEvent, QPainter
from PySide6.QtWidgets import QLabel, QMenu, QVBoxLayout, QWidget

from desktop_study_companion.avatar.widget import AvatarWidget
from desktop_study_companion.config.models import AvatarConfig
from desktop_study_companion.runtime_paths import (
    avatar_model_path,
    avatar_renderer_directory,
)


logger = logging.getLogger("desktop_study_companion.ui.companion")


class CompanionWidget(QWidget):
    chat_requested = Signal()
    start_session_requested = Signal()
    finish_session_requested = Signal()
    add_directive_requested = Signal()
    manage_directives_requested = Signal()
    add_rule_requested = Signal()
    manage_rules_requested = Signal()
    add_routine_requested = Signal()
    manage_routines_requested = Signal()
    intervention_settings_requested = Signal()
    emergency_disable_requested = Signal()
    end_lockdown_requested = Signal()
    history_requested = Signal()
    export_csv_requested = Signal()
    backup_requested = Signal()
    settings_requested = Signal()
    tutorial_requested = Signal(str)
    open_logs_requested = Signal()
    copy_diagnostics_requested = Signal()
    pause_monitoring_requested = Signal(bool)
    quit_requested = Signal()

    def __init__(
        self,
        name: str = "Companion",
        avatar_config: AvatarConfig | None = None,
    ) -> None:
        super().__init__()
        self.name = name
        self._drag_origin: QPoint | None = None
        self._monitoring_paused = False
        self.avatar_config = avatar_config or AvatarConfig()

        self.setWindowTitle("Desktop Study Companion")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(self.avatar_config.width, self.avatar_config.height)

        self.bubble = QLabel("Clique com o botão direito para abrir o menu.")
        self.bubble.setWordWrap(True)
        self.bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bubble.setStyleSheet(
            "QLabel { background: rgba(255,255,255,235); color: #222; "
            "border: 1px solid #999; border-radius: 12px; padding: 10px; }"
        )

        self.avatar = self._create_avatar()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.addWidget(self.bubble)
        self._layout.addWidget(self.avatar, 1)

        self._look_timer = QTimer(self)
        self._look_timer.setInterval(120)
        self._look_timer.timeout.connect(self._update_avatar_look)
        self._look_timer.start()

    def _create_avatar(self):
        if not self.avatar_config.enabled:
            return self._fallback_avatar()

        renderer = avatar_renderer_directory()
        model = avatar_model_path()
        if renderer.exists() and (renderer / "index.html").exists() and model.exists():
            try:
                avatar = AvatarWidget(renderer, model, self)
                avatar.setMinimumHeight(380)
                avatar.avatar_failed.connect(self._avatar_failed)
                return avatar
            except Exception:
                logger.exception("Failed to create AvatarWidget")

        logger.warning(
            "Avatar fallback selected before renderer startup. renderer=%s model=%s",
            renderer,
            model,
        )
        return self._fallback_avatar()

    def _fallback_avatar(self) -> QLabel:
        fallback = QLabel("📚")
        fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback.setStyleSheet("font-size: 64px; background: transparent;")
        return fallback

    def _avatar_failed(self, reason: str) -> None:
        if not isinstance(self.avatar, AvatarWidget):
            return
        logger.error("Avatar failed; switching to fallback. reason=%s", reason)
        self._replace_avatar_widget(self._fallback_avatar())
        self.say(
            "Avatar 3D indisponível; usando fallback. "
            "Abra Diagnóstico > Abrir pasta de logs."
        )

    def set_avatar_expression(self, name: str, weight: float = 1.0) -> None:
        if isinstance(self.avatar, AvatarWidget):
            self.avatar.set_expression(name, weight)

    def animate_avatar_speech(self, text: str) -> None:
        if self.avatar_config.lip_sync and isinstance(self.avatar, AvatarWidget):
            self.avatar.talk_for_text(text)

    def _update_avatar_look(self) -> None:
        if (
            not self.avatar_config.look_at_cursor
            or not isinstance(self.avatar, AvatarWidget)
        ):
            return
        cursor = QCursor.pos()
        center = self.frameGeometry().center()
        dx = (cursor.x() - center.x()) / max(1, self.width())
        dy = (center.y() - cursor.y()) / max(1, self.height())
        self.avatar.set_look(dx * 1.8, dy * 1.8)
    def _replace_avatar_widget(self, new_widget) -> None:
        old = self.avatar
        self._layout.replaceWidget(old, new_widget)
        self.avatar = new_widget
        if isinstance(old, AvatarWidget):
            old.close_avatar()
        old.deleteLater()

    def apply_avatar_config(self, config: AvatarConfig) -> None:
        self.avatar_config = config
        self.resize(config.width, config.height)

        has_vrm = isinstance(self.avatar, AvatarWidget)
        if config.enabled and not has_vrm:
            self._replace_avatar_widget(self._create_avatar())
        elif not config.enabled and has_vrm:
            self._replace_avatar_widget(self._fallback_avatar())

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        super().paintEvent(event)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        # QWebEngineView uses its own accelerated surface. A plain child QMenu
        # can end up visually behind that surface on Windows. Use an independent
        # always-on-top popup so the menu remains selectable above the avatar.
        menu = QMenu()
        menu.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        menu.setWindowFlag(Qt.WindowType.Tool, True)

        chat = QAction("Conversar", self)
        chat.triggered.connect(self.chat_requested.emit)
        menu.addAction(chat)

        session_menu = menu.addMenu("Sessão de estudo")
        start = QAction("Iniciar sessão", self)
        start.triggered.connect(self.start_session_requested.emit)
        session_menu.addAction(start)
        finish = QAction("Encerrar sessão atual", self)
        finish.triggered.connect(self.finish_session_requested.emit)
        session_menu.addAction(finish)

        directive_menu = menu.addMenu("Compromissos")
        add_directive = QAction("Adicionar compromisso", self)
        add_directive.triggered.connect(self.add_directive_requested.emit)
        directive_menu.addAction(add_directive)
        manage_directives = QAction("Gerenciar compromissos", self)
        manage_directives.triggered.connect(self.manage_directives_requested.emit)
        directive_menu.addAction(manage_directives)

        rule_menu = menu.addMenu("Regras permanentes")
        add_rule = QAction("Adicionar regra", self)
        add_rule.triggered.connect(self.add_rule_requested.emit)
        rule_menu.addAction(add_rule)
        manage_rules = QAction("Gerenciar regras", self)
        manage_rules.triggered.connect(self.manage_rules_requested.emit)
        rule_menu.addAction(manage_rules)

        routine_menu = menu.addMenu("Rotinas")
        add_routine = QAction("Adicionar rotina diária", self)
        add_routine.triggered.connect(self.add_routine_requested.emit)
        routine_menu.addAction(add_routine)
        manage_routines = QAction("Gerenciar rotinas", self)
        manage_routines.triggered.connect(self.manage_routines_requested.emit)
        routine_menu.addAction(manage_routines)

        intervention_menu = menu.addMenu("Intervenções no desktop")
        settings = QAction("Configurar permissões", self)
        settings.triggered.connect(self.intervention_settings_requested.emit)
        intervention_menu.addAction(settings)
        end_lockdown = QAction("Encerrar lockdown atual", self)
        end_lockdown.triggered.connect(self.end_lockdown_requested.emit)
        intervention_menu.addAction(end_lockdown)

        emergency = QAction("DESATIVAR INTERVENÇÕES AGORA", self)
        emergency.triggered.connect(self.emergency_disable_requested.emit)
        intervention_menu.addAction(emergency)

        data_menu = menu.addMenu("Histórico e dados")
        history = QAction("Histórico e insights", self)
        history.triggered.connect(self.history_requested.emit)
        data_menu.addAction(history)

        export_csv = QAction("Exportar CSV", self)
        export_csv.triggered.connect(self.export_csv_requested.emit)
        data_menu.addAction(export_csv)

        backup = QAction("Criar backup ZIP", self)
        backup.triggered.connect(self.backup_requested.emit)
        data_menu.addAction(backup)

        settings_action = QAction("Configurações", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        menu.addAction(settings_action)

        diagnostics_menu = menu.addMenu("Diagnóstico")
        open_logs = QAction("Abrir pasta de logs", self)
        open_logs.triggered.connect(self.open_logs_requested.emit)
        diagnostics_menu.addAction(open_logs)
        copy_diagnostics = QAction("Copiar resumo do diagnóstico", self)
        copy_diagnostics.triggered.connect(
            self.copy_diagnostics_requested.emit
        )
        diagnostics_menu.addAction(copy_diagnostics)

        help_menu = menu.addMenu("Ajuda e tutoriais")

        getting_started = QAction("Primeiros passos", self)
        getting_started.triggered.connect(
            lambda: self.tutorial_requested.emit("getting_started")
        )
        help_menu.addAction(getting_started)

        brain_tutorial = QAction("Configurar Cérebro / Ollama", self)
        brain_tutorial.triggered.connect(
            lambda: self.tutorial_requested.emit("brain")
        )
        help_menu.addAction(brain_tutorial)

        voice_tutorial = QAction("Configurar voz e microfone", self)
        voice_tutorial.triggered.connect(
            lambda: self.tutorial_requested.emit("voice")
        )
        help_menu.addAction(voice_tutorial)

        avatar_tutorial = QAction("Diagnóstico do avatar", self)
        avatar_tutorial.triggered.connect(
            lambda: self.tutorial_requested.emit("avatar")
        )
        help_menu.addAction(avatar_tutorial)

        menu.addSeparator()

        pause_text = (
            "Retomar monitoramento"
            if self._monitoring_paused
            else "Pausar monitoramento"
        )
        pause = QAction(pause_text, self)
        pause.triggered.connect(self._toggle_pause)
        menu.addAction(pause)

        menu.addSeparator()
        quit_action = QAction("Sair", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        menu.raise_()
        menu.exec(event.globalPos())

    def _toggle_pause(self) -> None:
        self._monitoring_paused = not self._monitoring_paused
        self.pause_monitoring_requested.emit(self._monitoring_paused)
        if self._monitoring_paused:
            self.say("Monitoramento pausado.")
        else:
            self.say("Monitoramento retomado.")

    def say(self, text: str) -> None:
        if text:
            self.bubble.setText(text)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if (
            self._drag_origin is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.move(event.globalPosition().toPoint() - self._drag_origin)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_origin = None
        event.accept()

    def shutdown_avatar(self) -> None:
        if isinstance(self.avatar, AvatarWidget):
            self.avatar.close_avatar()
