# Roadmap

## Fase 0 — Fundação

- [x] Criar repositório.
- [x] Definir arquitetura modular.
- [x] Registrar autorização de reutilização e atribuição ao bonziPONY.
- [x] Criar scaffold Python inicial.
- [ ] Definir identidade/nome definitivo da personagem.
- [x] Definir stack visual provisória da v0.1: PySide6.
- [ ] Definir stack visual definitiva para avatar/personagem animada.

## v0.1 — Ciclo mínimo de accountability

Objetivo: completar o fluxo “planejar → estudar → distrair → cobrar → retornar → registrar”.

Implementado no código:

- [x] Monitorar janela ativa no Windows.
- [x] Configurar lista de aplicativos produtivos/neutros/distrativos.
- [x] Criar sessão de estudo com duração e objetivo.
- [x] Detectar permanência em distração.
- [x] Implementar níveis 1–4 de cobrança.
- [x] Exibir personagem/widget sempre no topo.
- [x] Persistir histórico da sessão em SQLite.
- [x] Exibir resumo ao terminar.
- [x] Reduzir gravações repetitivas no banco durante monitoramento.
- [x] Adicionar inicializador simples para Windows.
- [x] Criar tutorial de instalação e teste.
- [x] Criar testes automatizados e CI para Windows.

Validação ainda necessária em máquina Windows real:

- [ ] confirmar leitura correta da janela ativa;
- [ ] confirmar comportamento com Edge/Chrome e títulos de abas;
- [ ] confirmar widget sempre no topo e arrastável;
- [ ] confirmar persistência após reiniciar;
- [ ] confirmar escalada 1–4 com sessão real.

Critério de conclusão:

> É possível iniciar uma sessão de 30 minutos, abrir uma aplicação marcada como distração, receber uma intervenção e concluir a sessão com os tempos registrados.

## v0.2 — Voz

- [x] TTS local inicial usando Windows SAPI.
- [ ] seletor de vozes instaladas no Windows.
- [ ] STT push-to-talk.
- [ ] interrupção da fala.
- [ ] seleção de voz pela interface.
- [ ] controles de volume pela interface.
- [x] fallback textual no balão.

## v0.3 — Personalidade programável

- [ ] presets;
- [ ] editor de traços;
- [x] estrutura para calor humano;
- [x] estrutura para sarcasmo;
- [x] estrutura para rigor;
- [x] estrutura para paciência;
- [x] estrutura para humor;
- [x] estrutura para iniciativa;
- [ ] exemplos de fala;
- [ ] limites de linguagem;
- [ ] geração contextual por LLM.

## v0.4 — Memória

- [x] SQLite inicial;
- [ ] fatos do usuário;
- [x] histórico de compromissos/sessões;
- [ ] padrões de procrastinação;
- [ ] resumos periódicos;
- [ ] esquecimento/configuração de retenção.

## v0.5 — Proatividade

- [ ] agenda;
- [x] rotinas persistentes básicas, adaptadas do bonziPONY;
- [x] lembretes proativos por horário/intervalo;
- [ ] heartbeat;
- [ ] comentário espontâneo contextual;
- [ ] início automático opcional.

## v0.5.1 — Accountability persistente

- [x] diretivas/compromissos persistentes, adaptados do bonziPONY;
- [x] urgência 1–10;
- [x] nag_count persistente;
- [x] escalada determinística de cobrança;
- [x] uma única prorrogação negociada;
- [x] concluir/remover compromissos pela interface;
- [x] regras permanentes baseadas em processo/título;
- [x] contador de reincidências;
- [x] cooldown por regra;
- [x] ativar/desativar/remover regras pela interface;
- [x] regra permanente influencia a classificação de distração em sessão;
- [ ] geração automática de padrões por LLM;
- [ ] criação de compromissos/regras por linguagem natural.

## v0.6 — Intervenções avançadas

Sempre opt-in.

- [ ] minimizar aplicativo;
- [ ] ocultar janela;
- [ ] fechar aplicativo;
- [ ] cooldown configurável pela interface;
- [ ] lista de aplicativos protegidos;
- [ ] botão de emergência para suspender controle.

## v0.7 — Estatísticas de estudo

- [x] coleta de tempo líquido classificado;
- [x] coleta de tempo distraído;
- [ ] adesão ao plano;
- [x] registro do número de intervenções;
- [ ] taxa de retorno após intervenção;
- [ ] calendário;
- [ ] padrões por horário/dia.

## v0.8 — Inteligência contextual

- [ ] integração LLM;
- [ ] ferramentas;
- [ ] resumo de sessão;
- [ ] avaliação de padrões;
- [ ] planejamento;
- [ ] memória semanticamente recuperável.

## v0.9 — Personagem avançada

- [ ] expressões;
- [ ] animações;
- [ ] lip-sync;
- [ ] gestos;
- [ ] estados de humor persistentes;
- [ ] múltiplas aparências.

## v1.0

- [ ] instalador Windows;
- [ ] atualização automática;
- [ ] backup/exportação;
- [ ] onboarding;
- [ ] permissões;
- [ ] documentação de privacidade;
- [ ] testes automatizados abrangentes;
- [ ] recuperação de falhas.
