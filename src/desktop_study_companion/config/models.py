from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class MonitorConfig:
    poll_interval_ms: int = 1000


@dataclass(slots=True)
class ActivityConfig:
    productive_keywords: list[str] = field(default_factory=list)
    neutral_keywords: list[str] = field(default_factory=list)
    distraction_keywords: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AccountabilityConfig:
    gentle_after_seconds: int = 60
    firm_after_seconds: int = 180
    direct_after_seconds: int = 300
    insistent_after_seconds: int = 600
    cooldown_seconds: int = 45


@dataclass(slots=True)
class PersonalityConfig:
    name: str = "Companion"
    warmth: int = 60
    sarcasm: int = 55
    strictness: int = 80
    patience: int = 40
    humor: int = 50
    initiative: int = 75


@dataclass(slots=True)
class ProactivityConfig:
    enabled: bool = True
    motivational_messages: bool = True
    coach_mode: bool = True
    min_interval_minutes: int = 6
    max_interval_minutes: int = 12
    activation_phrases: list[str] = field(default_factory=list)
    focus_phrases: list[str] = field(default_factory=list)
    recovery_phrases: list[str] = field(default_factory=list)
    celebration_phrases: list[str] = field(default_factory=list)
    reset_phrases: list[str] = field(default_factory=list)


@dataclass(slots=True)
class VoiceConfig:
    enabled: bool = True
    engine: str = "piper"
    rate: int = 0
    volume: int = 90
    voice_id: str = ""
    piper_voice_id: str = "pt_BR-faber-medium"
    piper_length_scale: float = 1.0
    piper_noise_scale: float = 0.667
    piper_noise_w_scale: float = 0.8
    fallback_to_sapi: bool = True


@dataclass(slots=True)
class SpeechInputConfig:
    enabled: bool = False
    model: str = "base"
    language: str = "pt"
    device: str = "cpu"
    compute_type: str = "int8"
    microphone_device: int = -1
    max_record_seconds: int = 30
    auto_send: bool = True


@dataclass(slots=True)
class BrainConfig:
    enabled: bool = False
    base_url: str = "http://127.0.0.1:11434/v1"
    model: str = ""
    api_key_env: str = "DESKTOP_STUDY_COMPANION_LLM_API_KEY"
    temperature: float = 0.7
    max_tokens: int = 500
    timeout_seconds: int = 45
    history_messages: int = 12


@dataclass(slots=True)
class AvatarConfig:
    enabled: bool = True
    width: int = 360
    height: int = 540
    look_at_cursor: bool = True
    lip_sync: bool = True
    spontaneous_gestures: bool = True
    gesture_min_seconds: int = 12
    gesture_max_seconds: int = 30


@dataclass(slots=True)
class AppConfig:
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    activity: ActivityConfig = field(default_factory=ActivityConfig)
    accountability: AccountabilityConfig = field(default_factory=AccountabilityConfig)
    personality: PersonalityConfig = field(default_factory=PersonalityConfig)
    proactivity: ProactivityConfig = field(default_factory=ProactivityConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    speech_input: SpeechInputConfig = field(default_factory=SpeechInputConfig)
    brain: BrainConfig = field(default_factory=BrainConfig)
    avatar: AvatarConfig = field(default_factory=AvatarConfig)
