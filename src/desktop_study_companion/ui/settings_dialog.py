from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QComboBox,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop_study_companion.voice.audio_capture import list_input_devices
from desktop_study_companion.voice.windows_sapi import list_sapi_voices

from desktop_study_companion.config.models import (
    AccountabilityConfig,
    ActivityConfig,
    AppConfig,
    AvatarConfig,
    BrainConfig,
    MonitorConfig,
    PersonalityConfig,
    VoiceConfig,
)


def _lines(values: list[str]) -> str:
    return "\n".join(values)


def _parse_lines(text: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for raw in text.splitlines():
        value = raw.strip()
        if value and value.casefold() not in seen:
            result.append(value)
            seen.add(value.casefold())
    return result


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.resize(650, 560)
        self._monitor = config.monitor

        tabs = QTabWidget()
        tabs.addTab(self._activity_tab(config), "Atividade")
        tabs.addTab(self._accountability_tab(config), "Cobrança")
        tabs.addTab(self._personality_tab(config), "Personalidade")
        tabs.addTab(self._voice_tab(config), "Voz")
        tabs.addTab(self._speech_input_tab(config), "Microfone")
        tabs.addTab(self._brain_tab(config), "Cérebro")
        tabs.addTab(self._avatar_tab(config), "Avatar")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    def _activity_tab(self, config: AppConfig) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)

        self.productive = QTextEdit(_lines(config.activity.productive_keywords))
        self.neutral = QTextEdit(_lines(config.activity.neutral_keywords))
        self.distraction = QTextEdit(
            _lines(config.activity.distraction_keywords)
        )

        form.addRow("Produtivos (um por linha):", self.productive)
        form.addRow("Neutros (um por linha):", self.neutral)
        form.addRow("Distrações (um por linha):", self.distraction)
        return widget

    def _accountability_tab(self, config: AppConfig) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        p = config.accountability

        self.gentle = self._seconds_spin(p.gentle_after_seconds)
        self.firm = self._seconds_spin(p.firm_after_seconds)
        self.direct = self._seconds_spin(p.direct_after_seconds)
        self.insistent = self._seconds_spin(p.insistent_after_seconds)
        self.cooldown = self._seconds_spin(p.cooldown_seconds)

        form.addRow("Lembrete gentil após:", self.gentle)
        form.addRow("Cobrança firme após:", self.firm)
        form.addRow("Cobrança direta após:", self.direct)
        form.addRow("Cobrança insistente após:", self.insistent)
        form.addRow("Cooldown entre cobranças:", self.cooldown)
        return widget

    def _personality_tab(self, config: AppConfig) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        p = config.personality

        self.character_name = QLineEdit(p.name)
        self.warmth = self._percent_spin(p.warmth)
        self.sarcasm = self._percent_spin(p.sarcasm)
        self.strictness = self._percent_spin(p.strictness)
        self.patience = self._percent_spin(p.patience)
        self.humor = self._percent_spin(p.humor)
        self.initiative = self._percent_spin(p.initiative)

        form.addRow("Nome:", self.character_name)
        form.addRow("Calor humano:", self.warmth)
        form.addRow("Sarcasmo:", self.sarcasm)
        form.addRow("Rigor:", self.strictness)
        form.addRow("Paciência:", self.patience)
        form.addRow("Humor:", self.humor)
        form.addRow("Iniciativa:", self.initiative)
        return widget

    def _voice_tab(self, config: AppConfig) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)

        self.voice_enabled = QCheckBox("Ativar voz do Windows")
        self.voice_enabled.setChecked(config.voice.enabled)

        self.voice_rate = QSpinBox()
        self.voice_rate.setRange(-10, 10)
        self.voice_rate.setValue(config.voice.rate)

        self.voice_volume = QSpinBox()
        self.voice_volume.setRange(0, 100)
        self.voice_volume.setValue(config.voice.volume)
        self.voice_volume.setSuffix("%")

        self.voice_choice = QComboBox()
        self.voice_choice.addItem("Voz padrão do Windows", "")
        try:
            for voice in list_sapi_voices():
                self.voice_choice.addItem(voice.name, voice.token_id)
        except Exception:
            pass
        voice_index = self.voice_choice.findData(config.voice.voice_id)
        self.voice_choice.setCurrentIndex(max(0, voice_index))

        form.addRow("", self.voice_enabled)
        form.addRow("Voz:", self.voice_choice)
        form.addRow("Velocidade:", self.voice_rate)
        form.addRow("Volume:", self.voice_volume)
        return widget




    def _speech_input_tab(self, config: AppConfig) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        s = config.speech_input

        self.stt_enabled = QCheckBox("Ativar push-to-talk local")
        self.stt_enabled.setChecked(s.enabled)

        self.stt_model = QLineEdit(s.model)
        self.stt_model.setPlaceholderText("base")

        self.stt_language = QLineEdit(s.language)
        self.stt_language.setPlaceholderText("pt")

        self.stt_device = QComboBox()
        self.stt_device.addItems(["cpu", "auto", "cuda"])
        idx = self.stt_device.findText(s.device)
        self.stt_device.setCurrentIndex(max(0, idx))

        self.stt_compute = QLineEdit(s.compute_type)
        self.stt_compute.setPlaceholderText("int8")

        self.stt_microphone = QComboBox()
        self.stt_microphone.addItem("Microfone padrão do Windows", -1)
        try:
            for device in list_input_devices():
                self.stt_microphone.addItem(
                    f"{device.index}: {device.name}",
                    device.index,
                )
        except Exception:
            pass
        mic_index = self.stt_microphone.findData(s.microphone_device)
        self.stt_microphone.setCurrentIndex(max(0, mic_index))

        self.stt_max_seconds = QSpinBox()
        self.stt_max_seconds.setRange(2, 120)
        self.stt_max_seconds.setValue(s.max_record_seconds)
        self.stt_max_seconds.setSuffix(" s")

        self.stt_auto_send = QCheckBox(
            "Enviar automaticamente após transcrever"
        )
        self.stt_auto_send.setChecked(s.auto_send)

        form.addRow("", self.stt_enabled)
        form.addRow("Modelo Whisper:", self.stt_model)
        form.addRow("Idioma:", self.stt_language)
        form.addRow("Dispositivo de inferência:", self.stt_device)
        form.addRow("Compute type:", self.stt_compute)
        form.addRow("Microfone:", self.stt_microphone)
        form.addRow("Máx. gravação:", self.stt_max_seconds)
        form.addRow("", self.stt_auto_send)
        return widget

    def _brain_tab(self, config: AppConfig) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        b = config.brain

        self.brain_enabled = QCheckBox("Ativar conversa com LLM")
        self.brain_enabled.setChecked(b.enabled)

        self.brain_base_url = QLineEdit(b.base_url)
        self.brain_base_url.setPlaceholderText(
            "http://127.0.0.1:11434/v1"
        )

        self.brain_model = QLineEdit(b.model)
        self.brain_model.setPlaceholderText("Nome do modelo local/remoto")

        self.brain_api_key_env = QLineEdit(b.api_key_env)
        self.brain_api_key_env.setPlaceholderText(
            "DESKTOP_STUDY_COMPANION_LLM_API_KEY"
        )

        self.brain_temperature = QDoubleSpinBox()
        self.brain_temperature.setRange(0.0, 2.0)
        self.brain_temperature.setSingleStep(0.1)
        self.brain_temperature.setValue(b.temperature)

        self.brain_max_tokens = QSpinBox()
        self.brain_max_tokens.setRange(32, 8192)
        self.brain_max_tokens.setValue(b.max_tokens)

        self.brain_timeout = QSpinBox()
        self.brain_timeout.setRange(3, 300)
        self.brain_timeout.setValue(b.timeout_seconds)
        self.brain_timeout.setSuffix(" s")

        self.brain_history = QSpinBox()
        self.brain_history.setRange(2, 100)
        self.brain_history.setValue(b.history_messages)
        self.brain_history.setSuffix(" mensagens")

        form.addRow("", self.brain_enabled)
        form.addRow("URL base:", self.brain_base_url)
        form.addRow("Modelo:", self.brain_model)
        form.addRow("Variável da chave:", self.brain_api_key_env)
        form.addRow("Temperatura:", self.brain_temperature)
        form.addRow("Máx. tokens:", self.brain_max_tokens)
        form.addRow("Timeout:", self.brain_timeout)
        form.addRow("Histórico enviado:", self.brain_history)
        return widget

    def _avatar_tab(self, config: AppConfig) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)

        self.avatar_enabled = QCheckBox("Ativar avatar VRM 3D")
        self.avatar_enabled.setChecked(config.avatar.enabled)

        self.avatar_width = QSpinBox()
        self.avatar_width.setRange(220, 900)
        self.avatar_width.setValue(config.avatar.width)
        self.avatar_width.setSuffix(" px")

        self.avatar_height = QSpinBox()
        self.avatar_height.setRange(320, 1100)
        self.avatar_height.setValue(config.avatar.height)
        self.avatar_height.setSuffix(" px")

        self.avatar_look = QCheckBox("Olhar acompanha o cursor")
        self.avatar_look.setChecked(config.avatar.look_at_cursor)

        self.avatar_lip_sync = QCheckBox("Animar boca durante a fala")
        self.avatar_lip_sync.setChecked(config.avatar.lip_sync)

        form.addRow("", self.avatar_enabled)
        form.addRow("Largura:", self.avatar_width)
        form.addRow("Altura:", self.avatar_height)
        form.addRow("", self.avatar_look)
        form.addRow("", self.avatar_lip_sync)
        return widget

    def _seconds_spin(self, value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(0, 86400)
        spin.setValue(value)
        spin.setSuffix(" s")
        return spin

    def _percent_spin(self, value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(0, 100)
        spin.setValue(value)
        return spin

    def values(self) -> AppConfig:
        return AppConfig(
            monitor=MonitorConfig(
                poll_interval_ms=self._monitor.poll_interval_ms
            ),
            activity=ActivityConfig(
                productive_keywords=_parse_lines(
                    self.productive.toPlainText()
                ),
                neutral_keywords=_parse_lines(self.neutral.toPlainText()),
                distraction_keywords=_parse_lines(
                    self.distraction.toPlainText()
                ),
            ),
            accountability=AccountabilityConfig(
                gentle_after_seconds=self.gentle.value(),
                firm_after_seconds=self.firm.value(),
                direct_after_seconds=self.direct.value(),
                insistent_after_seconds=self.insistent.value(),
                cooldown_seconds=self.cooldown.value(),
            ),
            personality=PersonalityConfig(
                name=self.character_name.text().strip() or "Companion",
                warmth=self.warmth.value(),
                sarcasm=self.sarcasm.value(),
                strictness=self.strictness.value(),
                patience=self.patience.value(),
                humor=self.humor.value(),
                initiative=self.initiative.value(),
            ),
            voice=VoiceConfig(
                enabled=self.voice_enabled.isChecked(),
                rate=self.voice_rate.value(),
                volume=self.voice_volume.value(),
                voice_id=str(self.voice_choice.currentData() or ""),
            ),
            speech_input=SpeechInputConfig(
                enabled=self.stt_enabled.isChecked(),
                model=self.stt_model.text().strip(),
                language=self.stt_language.text().strip(),
                device=self.stt_device.currentText(),
                compute_type=self.stt_compute.text().strip(),
                microphone_device=int(
                    self.stt_microphone.currentData()
                    if self.stt_microphone.currentData() is not None
                    else -1
                ),
                max_record_seconds=self.stt_max_seconds.value(),
                auto_send=self.stt_auto_send.isChecked(),
            ),
            brain=BrainConfig(
                enabled=self.brain_enabled.isChecked(),
                base_url=self.brain_base_url.text().strip(),
                model=self.brain_model.text().strip(),
                api_key_env=self.brain_api_key_env.text().strip(),
                temperature=self.brain_temperature.value(),
                max_tokens=self.brain_max_tokens.value(),
                timeout_seconds=self.brain_timeout.value(),
                history_messages=self.brain_history.value(),
            ),
            avatar=AvatarConfig(
                enabled=self.avatar_enabled.isChecked(),
                width=self.avatar_width.value(),
                height=self.avatar_height.value(),
                look_at_cursor=self.avatar_look.isChecked(),
                lip_sync=self.avatar_lip_sync.isChecked(),
            ),
        )
