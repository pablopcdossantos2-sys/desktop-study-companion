from __future__ import annotations

import random
from collections.abc import Sequence

from desktop_study_companion.accountability.models import InterventionKind

from .models import Personality


class PersonalityRenderer:
    def __init__(self, personality: Personality, name: str = "Companion") -> None:
        self.personality = personality
        self.name = name

    def _pick(
        self,
        defaults: Sequence[str],
        custom: Sequence[str] | None = None,
    ) -> str:
        pool = [item.strip() for item in (custom or []) if item.strip()]
        if not pool:
            pool = list(defaults)
        return random.choice(pool)

    def _render(
        self,
        text: str,
        *,
        goal: str | None = None,
        minutes: int | float | None = None,
        focused_minutes: int | float | None = None,
        distracted_minutes: int | float | None = None,
    ) -> str:
        replacements = {
            "{name}": self.name,
            "{goal}": goal or "seu estudo",
            "{minutes}": (
                f"{minutes:g}"
                if isinstance(minutes, float)
                else str(minutes if minutes is not None else "")
            ),
            "{focused_minutes}": (
                f"{focused_minutes:g}"
                if isinstance(focused_minutes, float)
                else str(
                    focused_minutes
                    if focused_minutes is not None
                    else ""
                )
            ),
            "{distracted_minutes}": (
                f"{distracted_minutes:g}"
                if isinstance(distracted_minutes, float)
                else str(
                    distracted_minutes
                    if distracted_minutes is not None
                    else ""
                )
            ),
        }
        rendered = text
        for token, value in replacements.items():
            rendered = rendered.replace(token, value)
        return rendered.strip()

    def intervention_message(self, kind: InterventionKind) -> str:
        strict = self.personality.strictness >= 70
        sarcastic = self.personality.sarcasm >= 60

        if kind == InterventionKind.GENTLE_REMINDER:
            return self._pick(
                [
                    "Ei. Sua sessão ainda está valendo. Volta para o que você decidiu fazer.",
                    "Pequeno desvio. Corrige agora e volta ao estudo antes que ele cresça.",
                    "Você saiu do trilho por um momento. Tudo bem. Agora volta.",
                ]
            )

        if kind == InterventionKind.FIRM_REMINDER:
            messages = [
                "A distração já está ocupando tempo demais. Volte ao material agora.",
                "Você tinha um plano para este bloco. Não entregue o bloco para a distração.",
                "Esse intervalo já deixou de ser uma pausa curta. Retome o estudo.",
            ]
            if sarcastic:
                messages.append(
                    "Isso definitivamente não parece parte do plano de estudo. Volta."
                )
            return self._pick(messages)

        if kind == InterventionKind.DIRECT_CHALLENGE:
            messages = [
                "Chega de negociar com a distração. Volte a estudar agora.",
                "Você já sabe o que precisa fazer. Feche a negociação mental e retome.",
                "A decisão de estudar já foi tomada antes. Agora cumpra essa decisão.",
                "Não espere vontade aparecer. Volte ao material e faça só a próxima ação.",
            ]
            if strict and sarcastic:
                messages.append(
                    "A distração já ganhou tempo suficiente. Não precisa ganhar a sessão inteira."
                )
            return self._pick(messages)

        if kind == InterventionKind.INSISTENT_CHALLENGE:
            messages = [
                "Eu vou continuar insistindo porque esse compromisso foi seu: volte agora.",
                "A distração já passou do razoável. Retome o estudo neste momento.",
                "Não transforme alguns minutos perdidos em uma sessão perdida. Volte agora.",
                "Você pode não estar com vontade. Ainda assim pode abrir o material e fazer a próxima etapa.",
            ]
            if strict:
                messages.append(
                    "Você assumiu um compromisso consigo mesmo. Eu não vou fingir que ele desapareceu."
                )
            return self._pick(messages)

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
            return self._pick(
                [
                    f"Lembrete: você se comprometeu a {goal}.",
                    f"Passando para manter o combinado visível: {goal}.",
                ]
            )
        if severity == 2:
            messages = [
                f"Você ainda não concluiu este compromisso: {goal}.",
                f"O combinado continua pendente. Qual é a próxima ação para {goal}?",
            ]
            if sarcastic:
                messages.append(
                    f"O compromisso continua existindo, mesmo se você fingir que esqueceu: {goal}."
                )
            return self._pick(messages)
        if severity == 3:
            if strict:
                return self._pick(
                    [
                        f"Chega de adiar. Faça o que você combinou: {goal}.",
                        f"Pare de renegociar o que já foi decidido. Avance em {goal}.",
                    ]
                )
            return f"Precisamos resolver este compromisso agora: {goal}."

        if nag_count >= 4 and sarcastic:
            return self._pick(
                [
                    f"Sim, eu ainda estou cobrando. E vou continuar: {goal}.",
                    f"Você já tentou esperar esse lembrete desaparecer. Não funcionou: {goal}.",
                ]
            )
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
            return (
                f"Esta é a ocorrência número {catch_count}. "
                f"Pare e respeite a regra: {description}."
            )
        return f"Você já acionou esta regra {catch_count} vezes: {description}."

    def session_start_message(
        self,
        goal: str,
        planned_minutes: int,
    ) -> str:
        defaults = [
            (
                "Combinado: {minutes} minutos para {goal}. "
                "Não precisa sentir vontade; só começa pela primeira ação concreta. "
                "Eu vou acompanhar."
            ),
            (
                "Sessão iniciada: {goal}, por {minutes} minutos. "
                "Seu trabalho agora é simples: proteger este bloco e continuar."
            ),
            (
                "Decisão tomada. Durante os próximos {minutes} minutos, "
                "o foco é {goal}. Se você sair do caminho, eu vou chamar de volta."
            ),
        ]
        if self.personality.strictness >= 75:
            defaults.append(
                (
                    "{minutes} minutos para {goal}. "
                    "A negociação terminou quando você iniciou a sessão. Vamos."
                )
            )
        return self._render(
            self._pick(defaults),
            goal=goal,
            minutes=planned_minutes,
        )

    def motivation_message(
        self,
        goal: str | None = None,
        *,
        state: str | None = None,
        focused_seconds: float = 0.0,
        distracted_seconds: float = 0.0,
        custom_activation: Sequence[str] | None = None,
        custom_focus: Sequence[str] | None = None,
    ) -> str:
        active = bool(goal and goal.strip())
        focused_minutes = round(max(0.0, focused_seconds) / 60.0, 1)
        distracted_minutes = round(max(0.0, distracted_seconds) / 60.0, 1)

        if active:
            defaults = [
                "Continua. Seu foco agora é {goal}. Só protege o próximo pedaço do bloco.",
                "Você já começou {goal}. Não procure uma nova decisão; execute a que já tomou.",
                "Check-in de coach: qual é a próxima ação concreta em {goal}? Faça só ela.",
                "Mantém o ritmo em {goal}. Consistência vale mais do que intensidade por alguns minutos.",
                "Não precisa terminar tudo agora. Precisa continuar em {goal}.",
                "Proteja os próximos cinco minutos. Depois você decide sobre os cinco seguintes.",
            ]
            if focused_minutes >= 10:
                defaults.extend(
                    [
                        "Você já acumulou {focused_minutes} minutos classificados como foco. Não quebra essa sequência agora.",
                        "{focused_minutes} minutos de foco já contam. Continua construindo em cima disso.",
                    ]
                )
            if distracted_minutes >= 2:
                defaults.append(
                    "Já houve {distracted_minutes} minutos de distração neste bloco. Não precisa compensar; só volta a proteger {goal}."
                )
            if state == "distracted":
                defaults.extend(
                    [
                        "Eu percebi que o bloco saiu do trilho. Não espera o momento perfeito: volta para {goal}.",
                        "A distração está tentando virar o plano padrão. Interrompe agora e retorna para {goal}.",
                    ]
                )
            text = self._pick(defaults, custom_focus)
        else:
            defaults = [
                "Escolha uma tarefa e me dê dez minutos. Começar pequeno é melhor do que continuar negociando.",
                "Se você está adiando, reduza a tarefa até caber em uma ação de dois minutos e comece.",
                "Não espere motivação chegar. Abra o material e deixe a ação gerar o impulso.",
                "Qual é a coisa mais importante que você deveria estudar agora? Transforme em um bloco curto.",
                "Uma sessão imperfeita ainda é uma sessão. Que tal iniciar um bloco agora?",
                "Seu futuro eu não precisa de um grande discurso. Precisa que você comece.",
            ]
            if self.personality.warmth >= 55:
                defaults.append(
                    "Eu fico com você no bloco. Escolha o objetivo, inicia a sessão e vamos por partes."
                )
            text = self._pick(defaults, custom_activation)

        return self._render(
            text,
            goal=goal,
            focused_minutes=focused_minutes,
            distracted_minutes=distracted_minutes,
        )

    def milestone_message(self, goal: str, percent: int) -> str:
        percent = max(1, min(99, int(percent)))
        if percent <= 25:
            defaults = [
                "Primeiro quarto do bloco feito. Continua em {goal}; não muda o plano agora.",
                "25% cumprido. O mais difícil era entrar no bloco. Agora mantém {goal}.",
            ]
        elif percent <= 50:
            defaults = [
                "Metade do bloco. Você não precisa acelerar; só continuar em {goal}.",
                "50% cumprido. Protege a segunda metade do mesmo jeito que protegeu a primeira.",
            ]
        else:
            defaults = [
                "75% cumprido. Reta final: fica com {goal} até fechar o combinado.",
                "Três quartos feitos. Não entrega os últimos minutos para a distração agora.",
            ]
        return self._render(self._pick(defaults), goal=goal)

    def recovery_message(
        self,
        goal: str | None,
        *,
        custom: Sequence[str] | None = None,
    ) -> str:
        defaults = [
            "Boa. Você voltou. Agora protege os próximos cinco minutos em {goal}.",
            "É isso. Percebeu o desvio e voltou. Continua em {goal}.",
            "Retomada feita. Não precisa recuperar o tempo perdido; só continua daqui.",
            "Voltar rápido vale mais do que nunca se distrair. Segue em {goal}.",
        ]
        if self.personality.strictness >= 70:
            defaults.append(
                "Certo. A distração terminou aqui. Nada de segunda rodada: volta para {goal}."
            )
        return self._render(self._pick(defaults, custom), goal=goal)

    def session_result_message(
        self,
        goal: str,
        *,
        completed: bool,
        focused_minutes: float,
        distracted_minutes: float,
        custom_celebration: Sequence[str] | None = None,
        custom_reset: Sequence[str] | None = None,
    ) -> str:
        if completed:
            defaults = [
                (
                    "Sessão concluída. Você apareceu para {goal} e sustentou o bloco. "
                    "Foco: {focused_minutes} min; distração: {distracted_minutes} min."
                ),
                (
                    "Fechado. {goal} avançou hoje. "
                    "Foco classificado: {focused_minutes} min. Isso é comportamento que vale repetir."
                ),
                (
                    "Bom trabalho. Não foi sobre sentir motivação; foi sobre cumprir o bloco de {goal}. "
                    "Foco: {focused_minutes} min."
                ),
            ]
            text = self._pick(defaults, custom_celebration)
        else:
            defaults = [
                (
                    "Sessão interrompida. Sem dramatizar: descubra o que tirou você de {goal} "
                    "e planeje um bloco menor para recomeçar."
                ),
                (
                    "Este bloco não fechou como planejado. A resposta útil agora é recomeçar melhor, "
                    "não abandonar {goal}."
                ),
                (
                    "Sessão registrada como interrompida. Use isso como dado: reduza a próxima meta "
                    "e volte para {goal} em um bloco mais fácil de cumprir."
                ),
            ]
            text = self._pick(defaults, custom_reset)

        return self._render(
            text,
            goal=goal,
            focused_minutes=focused_minutes,
            distracted_minutes=distracted_minutes,
        )

    def commitment_completed_message(
        self,
        goal: str,
        *,
        custom: Sequence[str] | None = None,
    ) -> str:
        defaults = [
            "Compromisso concluído: {goal}. Boa. Cumprir o combinado reforça o próximo.",
            "Fechado: {goal}. É assim que a consistência fica menos dependente de motivação.",
            "Você concluiu {goal}. Registra essa vitória e segue.",
        ]
        return self._render(self._pick(defaults, custom), goal=goal)
