# Arquitetura

## Visão geral

O Desktop Study Companion é dividido em camadas independentes para evitar acoplamento entre personagem, voz, memória, monitoramento e regras de cobrança.

```text
Desktop UI / Character
        │
        ▼
Application Orchestrator
        │
        ├── Personality
        ├── Voice
        ├── Conversational Brain
        ├── Study Session Manager
        ├── Accountability Engine
        ├── Activity Monitor
        └── Memory
```

## Módulos

### `activity`

Responsável por observar o contexto local necessário para avaliar foco:

- processo em primeiro plano;
- título da janela ativa;
- tempo contínuo naquela janela;
- estado ocioso;
- classificação local da atividade.

O módulo não toma decisões de cobrança.

### `study`

Gerencia a máquina de estados da sessão:

- `IDLE`
- `PLANNED`
- `FOCUSING`
- `DISTRACTED`
- `BREAK`
- `COMPLETED`
- `ABANDONED`

Também registra meta, duração planejada, início, fim, tempo produtivo e tempo de distração.

### `accountability`

Recebe fatos do módulo de estudo/atividade e decide:

- se deve intervir;
- severidade;
- cooldown;
- mensagem/intenção;
- ação permitida.

A política não deve depender do texto produzido pelo LLM.

Exemplo de escala inicial:

1. observação silenciosa;
2. lembrete gentil;
3. lembrete firme;
4. cobrança direta;
5. cobrança insistente;
6. alerta visual/sonoro;
7. minimizar distração, se previamente autorizado;
8. fechar distração, se previamente autorizado.

Os níveis 7–8 ficam desativados por padrão.

### `personality`

Transforma uma intenção segura em estilo de comunicação.

Exemplo:

```text
intenção: RETURN_TO_STUDY
severidade: 4

gentil   -> "Seu intervalo já passou. Vamos voltar?"
sarcástica -> "O material não vai se estudar sozinho."
rigorosa -> "Volte ao material agora."
```

A personalidade não pode elevar por conta própria a permissão de uma intervenção.

### `memory`

Persistência local de:

- perfil do usuário;
- sessões;
- compromissos;
- intervenções;
- preferências;
- memórias de longo prazo.

SQLite é a opção preferencial para a primeira implementação persistente.

### `brain`

Camada opcional de conversa com LLM.

Responsabilidades:

- montar prompt com personalidade e contexto comportamental resumido;
- enviar mensagens a endpoints compatíveis com `/v1/chat/completions`;
- manter o histórico local no SQLite;
- sanitizar a resposta antes de enviá-la à UI/TTS;
- executar chamadas de rede fora da thread da interface.

Limite arquitetural:

```text
BrainService ──X──> DesktopInterventionController
BrainService ──X──> InterventionPermissionStore
BrainService ──X──> StandingRuleManager
```

Essas ligações não existem. O cérebro conversacional recebe contexto e retorna texto.

### `voice`

Interfaces desacopladas:

- STT;
- TTS;
- wake word;
- playback.

Assim será possível trocar provedores sem alterar o Study Engine.

### `ui`

Responsável apenas por apresentação:

- janela transparente;
- personagem;
- balão de fala;
- expressões;
- estado visual;
- menu rápido;
- indicador de monitoramento ativo/pausado.

## Fluxo de evento

```text
ActiveWindowChanged
        │
        ▼
ActivityClassifier
        │
        ▼
StudySessionManager
        │
        ▼
AccountabilityEngine
        │
        ├── nenhuma ação
        └── InterventionIntent
                 │
                 ▼
          PersonalityRenderer
                 │
                 ├── texto
                 ├── emoção
                 └── gesto
```

## Decisões arquiteturais

### Não copiar o monólito do projeto de referência

A principal referência funcional possui um agente central muito grande. Neste projeto, regras, monitoramento, memória e apresentação serão mantidos em módulos separados desde o início.

### Local first

O monitoramento de aplicações não depende de visão por IA. Sempre que possível, título da janela, processo e tempo de uso serão avaliados localmente.

### LLM como camada de linguagem, não de segurança

O modelo pode produzir linguagem e raciocínio contextual, mas:

- não decide sozinho se pode fechar uma aplicação;
- não recebe permissão implícita para controlar o computador;
- não redefine limites configurados pelo usuário.

### Windows primeiro

A v0.1 é direcionada a Windows 10/11. Interfaces internas deverão evitar dependências desnecessárias para permitir portabilidade futura.


## Fluxo de conversa

```text
Usuário
   │
   ▼
ChatDialog
   │
   ▼
BrainChatWorker
   │
   ▼
BrainService
   ├── personalidade configurada
   ├── contexto da sessão
   ├── analytics local resumido
   └── histórico SQLite limitado
   │
   ▼
OpenAICompatibleProvider
   │
   ▼
sanitização da resposta
   │
   ├── ChatDialog
   ├── balão
   ├── TTS
   └── expressão/lip-sync do avatar
```

Nenhuma ferramenta de desktop é incluída no payload da API.
