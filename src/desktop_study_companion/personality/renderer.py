from __future__ import annotations

from desktop_study_companion.accountability.models import InterventionKind

from .models import Personality


class PersonalityRenderer:
    def __init__(self, personality: Personality, name: str = "Companion") -> None:
        self.personality = personality
        self.name = name

    def intervention_message(self, kind: InterventionKind) -> str:
        strict = self.personality.strictness >= 70
        sarcastic = self.personality.sarcasm >= 60

        if kind == InterventionKind.GENTLE_REMINDER:
            return "Ei — sua sessão ainda está valendo. Vamos voltar ao estudo?"

        if kind == InterventionKind.FIRM_REMINDER:
            if sarcastic:
                return "Isso definitivamente não parece fazer parte do plano de estudo."
            return "Você se afastou do estudo há alguns minutos. Volte ao material."

        if kind == InterventionKind.DIRECT_CHALLENGE:
            if strict and sarcastic:
                return "Chega de negociar com a distração. Volte a estudar agora."
            return "A distração já passou do limite combinado. Hora de voltar."

        if kind == InterventionKind.INSISTENT_CHALLENGE:
            if strict:
                return "Dez minutos de distração. Você assumiu um compromisso: volte agora."
            return "Já faz bastante tempo. Vamos retomar antes que a sessão se perca."

        return ""
