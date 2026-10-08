# Third-Party Notices

## bonziPONY

Projeto original:

- **Nome:** bonziPONY
- **Repositório:** https://github.com/maresmaremares/bonziPONY
- **Autor/mantenedor identificado pelo repositório:** maresmaremares

O Desktop Study Companion utiliza, adapta e/ou toma como base componentes de código e arquivos do bonziPONY.

O criador do bonziPONY autorizou pessoalmente o mantenedor deste projeto a reutilizar livremente esses materiais, solicitando como condição que o uso seja citado no README.

### Áreas de influência e reutilização

Entre os componentes do bonziPONY que podem ser reutilizados ou adaptados ao longo do desenvolvimento estão:

- monitoramento do desktop e da janela ativa;
- diretivas persistentes;
- regras permanentes;
- rotinas e agendamentos;
- mecanismos de cobrança/escalada;
- interação com janelas;
- voz, wake word e pipeline de conversação;
- visão;
- personagem de desktop;
- gerenciamento de perfil/memória;
- integração com provedores de LLM.

### Componentes concretamente incorporados

Nesta versão, os seguintes módulos do Desktop Study Companion contêm adaptação direta da lógica do bonziPONY:

- `src/desktop_study_companion/routines/models.py` — modelo persistente de rotina, inspirado/adaptado de `core/routines.py`;
- `src/desktop_study_companion/routines/manager.py` — persistência e avaliação de rotinas `daily`, `weekly`, `interval` e `on_wake`, adaptadas de `core/routines.py`;
- `src/desktop_study_companion/accountability/directives.py` — estado persistente de compromissos, incluindo urgência, próximo nag, contador e atraso único, adaptado do modelo `Directive` de `core/agent_loop.py`;
- `src/desktop_study_companion/accountability/standing_rules.py` — regras permanentes com padrões, contador de flagrantes e cooldown, adaptadas do modelo `StandingRule` de `core/agent_loop.py`;
- `src/desktop_study_companion/accountability/nagging.py` — política determinística inspirada na escalada e no agendamento de cobranças do sistema de diretivas do bonziPONY;
- `src/desktop_study_companion/desktop/interventions.py` — ações direcionadas de minimizar/fechar e fechamento de aba de navegador adaptados de `robot/desktop_controller.py` e das abstrações de janela do bonziPONY, com uma camada adicional de permissões e proteções.

Os arquivos derivados também possuem comentários de atribuição no próprio código.

Outras áreas do bonziPONY poderão ser incorporadas de forma seletiva nas próximas etapas.

## Outros projetos

YUI, Warashi, Noema e companion-emergence foram analisados durante a fase de arquitetura. Ideias gerais podem servir como referência, mas nenhuma reutilização literal deve ser presumida sem observar a licença específica de cada projeto.
