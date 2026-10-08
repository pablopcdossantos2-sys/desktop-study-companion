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
- [x] editor nativo de traços básicos;
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
- [x] padrões comportamentais locais básicos;
- [x] taxa de retorno após intervenção;
- [x] tendência recente de foco;
- [x] processo de distração mais recorrente;
- [x] melhor horário de foco com amostra mínima;
- [ ] fatos pessoais extraídos de conversa;
- [ ] resumos periódicos por LLM;
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

- [x] minimizar janela por Standing Rule, somente opt-in;
- [ ] ocultar janela;
- [x] fechar aba/janela por Standing Rule, somente opt-in;
- [x] cooldown configurável pela interface;
- [x] lista de processos protegidos;
- [x] proteções críticas irremovíveis;
- [x] botão de emergência para suspender controle;
- [x] fechamento de navegador tenta fechar somente a aba;
- [x] auditoria SQLite das intervenções executadas;
- [x] escalada automática de intervenção vinculada à sessão, opcional;
- [x] fala → minimizar → fechar conforme severidade e permissões;
- [x] lockdown limitado temporário e reversível;
- [x] cooldown por alvo durante lockdown;
- [x] encerramento manual do lockdown;
- [x] lockdown termina com sessão/emergência;
- [x] configuração inválida falha para permissões seguras;
- [ ] modo lockdown avançado com políticas personalizadas por perfil.

## v0.7 — Estatísticas de estudo

- [x] coleta de tempo líquido classificado;
- [x] coleta de tempo distraído;
- [x] taxa de conclusão;
- [x] registro do número de intervenções;
- [x] taxa estimada de retorno após intervenção;
- [ ] calendário;
- [x] padrões básicos por horário;
- [x] histórico consultável pela interface;
- [x] exportação CSV;
- [x] backup ZIP consistente.

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

- [x] build portátil Windows via GitHub Actions;\n- [ ] instalador Windows;
- [ ] atualização automática;
- [x] backup/exportação básica;
- [ ] onboarding;
- [x] permissões de intervenção configuráveis pela interface;
- [ ] documentação de privacidade;
- [ ] testes automatizados abrangentes;
- [ ] recuperação de falhas.
