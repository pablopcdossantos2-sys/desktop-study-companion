# Limitações conhecidas da v0.1.0-dev10

A dev10 é um protótipo funcional para validar o ciclo completo de accountability, avatar e conversa por voz no Windows. Ela ainda não representa a experiência final de produto.

## Personagem VRM

A personagem **Sendagaya Shino** já é carregada como VRM 1.0 e possui:

- transparência;
- piscada automática;
- look-at seguindo o cursor;
- expressões básicas ligadas ao estado;
- lip-sync aproximado;
- movimento idle discreto;
- fallback visual caso o renderer falhe.

Ainda faltam:

- lip-sync baseado no áudio real;
- animações corporais/VRMA;
- gestos específicos de cobrança/comemoração;
- movimentação autônoma pela área de trabalho;
- estados de humor persistentes.

## Cérebro conversacional

O cérebro com LLM é opcional e vem desativado por padrão.

Limitações atuais:

- não há streaming de tokens;
- não há ferramentas concedidas ao LLM;
- o LLM não cria nem altera Standing Rules, Directives ou permissões;
- não há memória semântica de longo prazo;
- não há resumo automático de sessão por LLM;
- endpoints específicos de provedores fora de `/v1/chat/completions` não são usados.

Essa separação entre LLM e intervenções de desktop é deliberada.

Se um endpoint remoto for configurado, mensagens e contexto incluído no prompt passam a estar sujeitos à política de privacidade do provedor. Ollama local é a rota recomendada para testes locais.

## Voz e push-to-talk

A dev10 já possui:

- TTS SAPI;
- seleção de voz instalada;
- volume/velocidade;
- interrupção da fala;
- seleção de microfone;
- push-to-talk;
- STT local com faster-whisper;
- envio automático ou revisão da transcrição.

Limitações:

- o modelo Whisper é baixado no primeiro uso;
- não há wake word;
- não há escuta contínua;
- não há streaming parcial da transcrição;
- não há detecção automática do fim da fala;
- CUDA depende de ambiente NVIDIA compatível;
- CPU + INT8 é o modo padrão suportado;
- o lip-sync visual não usa o áudio real do SAPI.

## Monitoramento

A classificação usa somente metadados locais:

- processo em primeiro plano;
- título da janela.

Não há captura automática de screenshots para classificar distrações.

Consequências:

- sites podem não ser reconhecidos se o título não contiver uma palavra configurada;
- títulos genéricos podem exigir novas palavras-chave;
- atividade desconhecida permanece `UNKNOWN`.

## Navegadores

A classificação por aba depende do título exposto pelo navegador.

Quando uma intervenção de fechamento é autorizada, navegadores conhecidos usam `Ctrl+W` para tentar fechar apenas a aba ativa; outros aplicativos podem exigir fechamento da janela.

## Métricas

Tempo produtivo só é contado quando a atividade corresponde às regras produtivas.

Atividade `NEUTRAL` ou `UNKNOWN` não aumenta tempo produtivo nem tempo de distração.

Os insights comportamentais atuais são heurísticos/determinísticos e exigem amostra mínima antes de exibir algumas conclusões.

## Banco de dados e memória

Os dados ficam em `data/companion.db`.

Já existem histórico, analytics, exportação CSV e backup ZIP, porém ainda não há:

- migrações formais de esquema entre releases;
- restauração guiada pela interface;
- política configurável de retenção/esquecimento;
- memória semântica de fatos pessoais.

## Intervenções no desktop

Minimizar, fechar e lockdown limitado já existem, mas são **opt-in**.

Limitações atuais:

- o sistema não bloqueia mouse/teclado;
- não bloqueia a estação de trabalho;
- não impede que o usuário desative as intervenções;
- o lockdown é propositalmente limitado e reversível;
- ações dependem das APIs/janelas do Windows e ainda precisam ser validadas em máquina real.

## Distribuição

Existe build portátil via GitHub Actions.

Ainda faltam:

- instalador Windows convencional;
- assinatura de código;
- atualização automática;
- onboarding completo;
- validação em diferentes GPUs, microfones e configurações de áudio.

## Validação necessária em PC real

O CI valida código, dependências e empacotamento, mas não substitui testes reais de:

- janela ativa;
- transparência/Qt WebEngine;
- VRM/WebGL;
- vozes SAPI;
- microfone/PortAudio;
- download e desempenho do Whisper;
- Ollama;
- intervenções reais de janela.
