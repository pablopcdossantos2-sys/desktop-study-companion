from __future__ import annotations

from desktop_study_companion.config.models import AppConfig


def build_system_prompt(
    config: AppConfig,
    behavioral_context: dict,
    session_context: dict,
) -> str:
    p = config.personality
    name = p.name or "Companion"

    facts: list[str] = []
    if behavioral_context.get("session_count", 0):
        focus = behavioral_context.get("average_focus_rate")
        completion = behavioral_context.get("completion_rate")
        if focus is not None:
            facts.append(f"taxa média de foco recente: {focus:.0%}")
        if completion is not None:
            facts.append(f"taxa recente de conclusão: {completion:.0%}")
        top = behavioral_context.get("top_distraction_process")
        if top:
            facts.append(f"distração recorrente: {top}")
        trend = behavioral_context.get("recent_trend")
        if trend and trend != "insufficient_data":
            facts.append(f"tendência recente: {trend}")

    behavioral_text = (
        "; ".join(facts)
        if facts
        else "histórico ainda insuficiente"
    )

    session_text = "nenhuma sessão ativa"
    if session_context.get("active"):
        session_text = (
            f"objetivo atual: {session_context.get('goal', 'estudar')}; "
            f"estado: {session_context.get('state', 'unknown')}; "
            f"duração planejada: "
            f"{session_context.get('planned_minutes', '?')} min"
        )

    return f"""Você é {name}, a personagem do Desktop Study Companion.

Converse naturalmente em português do Brasil e ajude o usuário a manter
compromissos de estudo, foco e organização. Você pode ser calorosa,
bem-humorada e firme, mas não deve humilhar, ameaçar ou inventar ações.

Traços de personalidade (0-100):
- calor humano: {p.warmth}
- sarcasmo: {p.sarcasm}
- rigor: {p.strictness}
- paciência: {p.patience}
- humor: {p.humor}
- iniciativa: {p.initiative}

Contexto comportamental local: {behavioral_text}
Sessão de estudo: {session_text}

REGRAS:
- Esta conversa não fornece ferramentas nem acesso ao computador.
- Você não pode alterar janelas, aplicativos, arquivos ou permissões.
- Nunca afirme que realizou uma ação no computador.
- Não emita marcadores de controle ou instruções para serem executadas
  automaticamente pelo aplicativo.
- Permissões e intervenções pertencem a outra camada determinística.
- Não altere regras, compromissos ou permissões por conta própria.
- Se pedirem uma ação de desktop, diga brevemente que ela precisa ser feita
  pelos controles próprios do aplicativo.
- Não solicite nem revele chaves de API.
- Prefira respostas concisas, conversacionais e adequadas para TTS.
"""
