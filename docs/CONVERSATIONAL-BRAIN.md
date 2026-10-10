# Cérebro conversacional

## Objetivo

O Desktop Study Companion possui uma camada opcional de conversa com LLM.

Ela foi construída para permitir que a personagem converse usando:

- um modelo local via Ollama;
- LM Studio ou outro servidor compatível;
- um endpoint remoto que implemente `/v1/chat/completions`.

O recurso vem **desativado por padrão**.

## Separação de segurança

A arquitetura deliberadamente separa o LLM da camada que controla o desktop:

```text
ChatDialog
   │
   ▼
BrainService
   │
   ▼
OpenAICompatibleProvider
   │
   ▼
texto da resposta
   │
   ▼
sanitização
   │
   ▼
UI / TTS / avatar

                     ┌───────────────────────────┐
                     │ Desktop interventions     │
                     │ regras determinísticas    │
                     │ permissões opt-in         │
                     └───────────────────────────┘
                               ▲
                               │
                    NÃO existe ligação de tools
                    com o BrainService
```

O LLM:

- não recebe ferramentas;
- não recebe objetos de permissão;
- não chama `DesktopInterventionController`;
- não pode habilitar intervenções;
- não pode alterar Standing Rules ou Directives;
- não pode minimizar/fechar janelas;
- não pode clicar ou digitar no computador.

A resposta também passa por uma camada de sanitização que remove blocos de raciocínio internos e marcadores que pareçam comandos de controle antes de chegar ao balão/TTS.

## Contexto fornecido ao modelo

Quando a conversa está habilitada, o prompt pode incluir contexto local resumido:

- traços configurados da personalidade;
- sessão de estudo atual;
- taxa recente de foco;
- taxa recente de conclusão;
- distração recorrente;
- tendência recente de foco.

O histórico enviado é limitado pelo campo **Histórico enviado** em `Configurações > Cérebro`.

## Persistência

As conversas são gravadas localmente na tabela:

`conversation_messages`

do arquivo:

`data/companion.db`

O usuário pode apagar o histórico pelo botão **Limpar histórico** da janela de conversa.

O histórico também passa a fazer parte:

- do backup ZIP;
- da exportação CSV, em `conversation_messages.csv`.

## Privacidade

### Backend local

Com um servidor local, por exemplo:

`http://127.0.0.1:11434/v1`

a aplicação envia a conversa para o serviço que está executando no próprio computador.

### Backend remoto

Se `URL base` apontar para a Internet, mensagens e contexto comportamental incluído no prompt serão enviados ao servidor configurado.

Portanto, use um endpoint remoto somente quando aceitar a política de privacidade daquele provedor.

## Chaves

O arquivo `config/default.json` não armazena o segredo da API.

Ele armazena somente o nome de uma variável de ambiente, por padrão:

`DESKTOP_STUDY_COMPANION_LLM_API_KEY`

O aplicativo procura o valor dessa variável somente em runtime.

Para Ollama local, chave não é necessária.

## Configurações

Em **Configurações > Cérebro** existem:

- Ativar conversa com LLM;
- URL base;
- Modelo;
- Variável da chave;
- Temperatura;
- Máx. tokens;
- Timeout;
- Histórico enviado.

## Interface

Quando o cérebro está habilitado e configurado:

1. clique com o botão direito na personagem;
2. escolha **Conversar**;
3. escreva a mensagem;
4. a chamada roda em uma thread de trabalho;
5. a interface, o avatar e o monitoramento continuam responsivos;
6. a resposta é mostrada no chat e falada pelo TTS, se a voz estiver habilitada.

## Falhas

Se o servidor estiver desligado, URL incorreta, modelo ausente ou ocorrer timeout:

- a aplicação não deve fechar;
- a janela de chat apresenta uma mensagem de falha;
- o monitoramento de estudo continua funcionando;
- nenhuma intervenção de desktop é disparada pelo erro.

## Próximas evoluções

- STT/push-to-talk;
- resumo automático de sessões;
- memória de fatos do usuário;
- recuperação semântica de memórias;
- geração contextual de sugestões;
- planejamento assistido;
- personalidade mais rica e estados de humor;
- streaming opcional das respostas.


## Proteção contra raciocínio exposto

A conversa deve exibir somente a resposta final destinada ao usuário.

Na dev15:

- Ollama local usa `/api/chat`;
- `think` é enviado como `false`;
- o prompt inclui `/no_think`;
- o system prompt proíbe metarraciocínio;
- saídas com padrões fortes de raciocínio interno são bloqueadas.

O detector não tenta reconstruir nem expor o raciocínio. Ele apenas impede que conteúdo claramente metalinguístico seja tratado como fala final.
