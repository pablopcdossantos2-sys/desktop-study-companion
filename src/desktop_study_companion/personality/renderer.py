from __future__ import annotations

import random

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
                return "A distração já passou do razoável. Você assumiu um compromisso: volte agora."
            return "Já faz bastante tempo. Vamos retomar antes que a sessão se perca."

        return ""

    def directive_message(
        self,
        goal: str,
        severity: int,
        nag_count: int,
    ) -> str:
        sarcastic = self.personality.sarcasm >= 60
        strict = self.personality.strictness >= 70

        if severity <= 1:
            return f"Lembrete: você se comprometeu a {goal}."
        if severity == 2:
            if sarcastic:
                return f"O compromisso continua existindo, mesmo se você fingir que esqueceu: {goal}."
            return f"Você ainda não concluiu este compromisso: {goal}."
        if severity == 3:
            if strict:
                return f"Chega de adiar. Faça o que você combinou: {goal}."
            return f"Precisamos resolver este compromisso agora: {goal}."

        if nag_count >= 4 and sarcastic:
            return f"Sim, eu ainda estou cobrando. E vou continuar: {goal}."
        return f"Você já foi lembrado várias vezes. Cumpra o compromisso agora: {goal}."

    def standing_rule_message(self, description: str, catch_count: int) -> str:
        strict = self.personality.strictness >= 70
        sarcastic = self.personality.sarcasm >= 60

        if catch_count <= 1:
            return f"Regra permanente acionada: {description}."
        if catch_count == 2:
            if sarcastic:
                return f"De novo? A regra continua a mesma: {description}."
            return f"Segunda ocorrência. Lembre-se da regra: {description}."
        if strict:
            return f"Esta é a ocorrência número {catch_count}. Pare e respeite a regra: {description}."
        return f"Você já acionou esta regra {catch_count} vezes: {description}."


    def motivation_message(self, goal: str | None = None) -> str:
        warm = self.personality.warmth >= 55
        strict = self.personality.strictness >= 70
        active = bool(goal and goal.strip())

        if active:
            messages = [
                f"Continua comigo. Seu foco agora é {goal}. Um passo de cada vez.",
                f"Você não precisa terminar tudo agora. Só precisa continuar em {goal}.",
                f"Vamos manter o ritmo. Volta para {goal} e fecha mais um pequeno bloco.",
                f"Você já começou. Proteja esse impulso e siga em {goal}.",
            ]
            if strict:
                messages.append(
                    f"Sem renegociar com a distração agora. O combinado é {goal}."
                )
        else:
            messages = [
                "Só passando para lembrar: um bloco curto de estudo já conta.",
                "Se estiver adiando alguma coisa, escolha a menor próxima ação e começa por ela.",
                "Seu progresso não precisa ser dramático. Precisa ser consistente.",
                "Que tal aproveitar os próximos minutos para avançar um pouco no que importa?",
            ]
            if warm:
                messages.append(
                    "Estou por aqui. Quando quiser começar um bloco de foco, a gente faz isso junto."
                )

        return random.choice(messages)
