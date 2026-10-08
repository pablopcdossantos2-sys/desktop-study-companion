# Sistema de accountability

O Desktop Study Companion possui quatro mecanismos diferentes. Eles podem coexistir, mas têm responsabilidades distintas.

## 1. Sessão de estudo

Uma sessão é limitada no tempo.

Exemplo:

> Estudar cálculo por 45 minutos.

Durante a sessão, a aplicação classifica a janela ativa e mede tempo produtivo, neutro, desconhecido e distraído. Se a distração persistir, o `AccountabilityEngine` aumenta a intensidade da cobrança.

## 2. Rotina

Uma rotina é recorrente e baseada em calendário.

Exemplo:

> Todos os dias às 19:00, lembrar de começar inglês.

O sistema de rotinas foi adaptado da lógica de `core/routines.py` do bonziPONY e permanece salvo em `data/routines.json`.

## 3. Compromisso (Directive)

Um compromisso não termina quando o lembrete aparece. Ele permanece ativo até ser explicitamente concluído ou removido.

Exemplo:

> Hoje preciso terminar 30 questões.

Cada compromisso mantém:

- urgência de 1 a 10;
- número de cobranças anteriores;
- último estilo de cobrança;
- último texto usado;
- próximo horário de cobrança;
- estado ativo/concluído;
- indicador de prorrogação já utilizada.

Essa estrutura é adaptada do modelo `Directive` do `core/agent_loop.py` do bonziPONY.

### Escalada

A política é determinística. O LLM não controla quando a cobrança acontece.

A urgência define a primeira frequência e o nível inicial. Reincidências:

- aumentam a severidade;
- reduzem progressivamente o intervalo;
- preservam um intervalo mínimo para evitar spam.

Urgência 10 possui um modo particularmente insistente, com primeira cobrança rápida.

### Prorrogação única

Cada compromisso pode ser adiado manualmente por cinco minutos uma única vez.

Depois disso, o botão deixa de estar disponível para aquele compromisso.

Isso adapta a ideia `delayed` do bonziPONY e evita uma sequência ilimitada de "só mais cinco minutos".

Os compromissos ficam em:

```text
data\directives.json
```

## 4. Regra permanente (Standing Rule)

Uma regra permanente observa o processo e o título da janela ativa continuamente.

Exemplo:

> Não usar YouTube enquanto deveria estar focado.

Padrões:

```text
youtube
youtu.be
```

A regra mantém:

- descrição;
- padrões de detecção;
- estado ativado/desativado;
- contador de flagrantes;
- último flagrante;
- cooldown mínimo entre reações.

Essa estrutura adapta o `StandingRule` do bonziPONY.

Os dados ficam em:

```text
data\standing_rules.json
```

### Reincidência

A personalidade leva o número de flagrantes em consideração.

Primeiro flagrante:

> Regra permanente acionada: não usar YouTube.

Segundo:

> De novo? A regra continua a mesma...

Flagrantes posteriores podem receber linguagem progressivamente mais firme.

## Relação entre regras e sessões

Se uma regra permanente for acionada durante uma sessão de estudo, a atividade também passa a ser classificada como `DISTRACTION` para aquela medição.

Portanto uma regra personalizada pode ampliar o classificador sem exigir alteração no arquivo de configuração.

## Segurança

Nesta etapa, uma regra permanente pode **cobrar**, mas não fecha nem bloqueia aplicativos.

O bonziPONY oferece respostas como `close_and_nag` e `lockdown`. A estrutura foi mantida conceitualmente, mas controles de desktop ficarão em outra camada e continuarão desativados por padrão até que sejam implementados com consentimento explícito.

O LLM, quando for adicionado, poderá:

- variar linguagem;
- compreender contexto;
- sugerir compromissos/regras.

Mas não poderá conceder a si mesmo permissão para fechar aplicativos ou alterar políticas de segurança.


## Escalada da sessão para ações de desktop

O `AccountabilityEngine` continua responsável apenas por classificar a severidade.

A conversão de severidade em ação é feita separadamente por `SessionEscalationPolicy`.

```text
AccountabilityEngine
        ↓
Intervention(severity)
        ↓
SessionEscalationPolicy
        ↓
Permission Gate
        ↓
DesktopInterventionController
```

Isso garante que personalidade e LLM não possam conceder permissões de sistema.

### Lockdown limitado

A estrutura `LimitedLockdown` é temporária e mantida apenas em memória.

Ela registra:

- horário de expiração;
- último alvo que recebeu ação;
- último horário de ação;
- cooldown de repetição.

A intenção é aumentar a firmeza do acompanhamento sem assumir controle irrestrito do computador.
