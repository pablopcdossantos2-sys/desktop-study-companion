# Limitações conhecidas da v0.1

A v0.1 é um MVP para validar o ciclo de accountability no Windows. Ela ainda não representa a experiência final planejada.

## Personagem

A interface atual usa um widget flutuante simples e um ícone provisório. Ainda não há:

- avatar Live2D/VRM;
- animações;
- expressões;
- lip-sync;
- movimentação autônoma pela área de trabalho.

## Inteligência

As mensagens atuais são geradas por regras de personalidade. Ainda não há LLM conectado.

Isso é intencional: detecção, segurança e política de intervenção devem funcionar antes de acrescentarmos geração de linguagem.

## Monitoramento

A v0.1 utiliza somente metadados locais:

- processo em primeiro plano;
- título da janela.

Ela não captura screenshots para classificar distrações.

Consequências:

- um site pode não ser reconhecido se o título da aba não contiver uma palavra configurada;
- títulos genéricos podem exigir novas palavras-chave;
- aplicativos desconhecidos ficam na categoria `UNKNOWN`.

## Navegadores

A classificação procura palavras tanto no nome do processo quanto no título da janela. Isso permite diferenciar, por exemplo, uma aba do YouTube de uma página de estudo aberta no mesmo Chrome/Edge, mas depende do título fornecido pelo navegador.

## Voz

O TTS inicial usa o Windows SAPI e, portanto:

- depende das vozes instaladas no Windows;
- ainda não há seletor de voz na interface;
- ainda não há reconhecimento de fala;
- ainda não há lip-sync.

A voz pode ser desativada em `config/default.json`.

## Métricas

Tempo produtivo só é contado quando a janela corresponde a uma regra `productive_keywords`.

Atividade `NEUTRAL` ou `UNKNOWN` não aumenta o tempo produtivo nem o tempo de distração.

## Banco de dados

Os dados são armazenados localmente em `data/companion.db`.

Nesta versão ainda não existe:

- interface para consultar histórico;
- exportação;
- backup automático;
- migração formal de esquema entre releases.

## Intervenções

A v0.1 apenas fala e exibe mensagens.

Ela **não**:

- minimiza;
- fecha;
- bloqueia;
- impede o uso

de qualquer programa.

Essas ações serão implementadas apenas como recursos explicitamente opt-in.


## Cérebro conversacional (dev9)

- O cérebro conversacional é opcional e vem desativado por padrão.
- A integração atual é apenas texto → LLM → texto/TTS.
- Ainda não há streaming de tokens.
- O push-to-talk local existe na dev10, mas ainda não há wake word ou escuta contínua.
- O LLM não recebe ferramentas nem acesso às permissões de intervenção no desktop; essa separação é deliberada.
- A compatibilidade esperada é com servidores que implementem `/v1/chat/completions`; extensões específicas de cada provedor não são usadas nesta fase.
- Quando um endpoint remoto é configurado, mensagens e contexto comportamental enviados no prompt deixam o computador e passam a estar sujeitos à política do provedor.
- O Ollama local é a rota recomendada para testes sem API paga.


## Voz local (dev10)

- STT usa faster-whisper local e requer download do modelo na primeira utilização.
- A build não inclui pesos Whisper para evitar aumentar ainda mais o ZIP.
- Não há streaming parcial da transcrição.
- Não há wake word.
- Não há detecção automática de fim de fala; o modo principal é pressionar/soltar.
- CUDA é opcional e depende de ambiente NVIDIA compatível; CPU + INT8 é o padrão suportado.
- O lip-sync visual ainda é aproximado pela duração do texto e não pelo áudio real.
