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
- `src/desktop_study_companion/desktop/interventions.py` — ações direcionadas de minimizar/fechar e fechamento de aba de navegador adaptados de `robot/desktop_controller.py` e das abstrações de janela do bonziPONY, com uma camada adicional de permissões e proteções;
- `src/desktop_study_companion/accountability/escalation.py` — inspirado na progressão de enforcement/lockdown do `core/agent_loop.py`, mas deliberadamente limitado a ações previamente autorizadas, sem bloqueio de mouse/teclado ou da estação.

Os arquivos derivados também possuem comentários de atribuição no próprio código.

Outras áreas do bonziPONY poderão ser incorporadas de forma seletiva nas próximas etapas.

## Outros projetos

YUI, Warashi, Noema e companion-emergence foram analisados durante a fase de arquitetura. Ideias gerais podem servir como referência, mas nenhuma reutilização literal deve ser presumida sem observar a licença específica de cada projeto.


## Sendagaya Shino (VRM 1.0)

Avatar usado pelo Desktop Study Companion:

- **Modelo:** Sendagaya Shino
- **Fonte oficial:** https://hub.vroid.com/en/characters/4593660874193246717/models/7956589129305596116
- **Formato:** VRM 1.0
- **Licença/condições:** coleção declarada CC0; uso, alteração e redistribuição permitidos; atribuição não exigida.

O projeto mantém este aviso por rastreabilidade, ainda que o crédito não seja obrigatório.

O arquivo binário é obtido durante build/desenvolvimento e validado por SHA-256 antes de ser usado.

## Three.js e @pixiv/three-vrm

O renderer do avatar usa Three.js e `@pixiv/three-vrm` para carregar e animar modelos VRM 1.0. As respectivas licenças permanecem aplicáveis aos componentes de software de terceiros.


The full MIT notices for Three.js and @pixiv/three-vrm are included in
`avatar_web/THIRD_PARTY_LICENSES.md` and copied into the portable build as
`THIRD_PARTY_LICENSES-AVATAR.md`.


## Local speech recognition

O pipeline de push-to-talk local usa:

- **faster-whisper** — MIT;
- **python-sounddevice** — MIT;
- **CTranslate2** — MIT;
- **PyAV** — BSD-style license.

Os textos de licença usados para redistribuição estão em:

`docs/THIRD_PARTY_LICENSES-VOICE.md`

e são copiados para a build portátil.


## Piper TTS

A partir da dev15, o Desktop Study Companion pode usar **Piper TTS** como motor neural local de síntese de voz.

A build mantém o pacote Python **OHF-Voice/piper1-gpl** (GPL-3.0) para gerenciamento/download de vozes e compatibilidade de desenvolvimento. A partir da dev22, o executável portátil para Windows também inclui o runtime standalone legado **rhasspy/piper 2023.11.14-2**, distribuído sob licença MIT, porque o wheel Windows moderno apresentou falha nativa de localização do `espeak-ng-data` em builds empacotadas.

- Runtime Python: OHF-Voice/piper1-gpl — GPL-3.0
- Runtime standalone Windows: rhasspy/piper — MIT
- Voz padrão sugerida: `pt_BR-faber-medium`
- Repositório de vozes: `rhasspy/piper-voices`
- O conjunto de dados indicado no model card de `faber` é CC0.

O modelo de voz não é versionado neste repositório. Ele é obtido no primeiro uso e armazenado localmente em `data/models/piper`. Para síntese no portátil Windows, modelo e runtime são copiados temporariamente para um caminho nativo compatível antes da execução.

As condições de licença do runtime e de cada modelo selecionado continuam aplicáveis.
