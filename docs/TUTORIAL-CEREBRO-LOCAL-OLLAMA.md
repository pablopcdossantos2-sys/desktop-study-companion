# Tutorial — Cérebro local com Ollama no Windows

Este tutorial ensina a ativar a conversa da personagem usando um modelo executado **no próprio computador**, sem depender de uma API paga.

O Ollama possui versão para Windows e expõe uma API local. O Desktop Study Companion usa o endpoint compatível com OpenAI:

`http://127.0.0.1:11434/v1`

## 1. Antes de começar

Você precisará estar no seu computador Windows.

A instalação do Ollama exige Windows 10 ou superior.

Modelos maiores exigem mais memória e podem ficar lentos em máquinas sem GPU forte. Para o primeiro teste, comece com um modelo pequeno.

## 2. Instalar o Ollama

Abra o **Windows PowerShell**.

Você pode abrir assim:

1. pressione a tecla Windows;
2. digite `PowerShell`;
3. abra **Windows PowerShell**.

Cole:

```powershell
irm https://ollama.com/install.ps1 | iex
```

Aguarde a conclusão.

## 3. Conferir a instalação

Feche o PowerShell e abra novamente.

Digite:

```powershell
ollama --version
```

Se aparecer uma versão, a instalação foi reconhecida.

## 4. Baixar um modelo

Para o primeiro teste, recomendamos:

```powershell
ollama pull qwen3:4b
```

Esse modelo ocupa alguns gigabytes.

Se o seu computador tiver pouca memória ou o modelo ficar muito lento, experimente:

```powershell
ollama pull qwen3:1.7b
```

Para conferir os modelos já instalados:

```powershell
ollama list
```

## 5. Testar o modelo diretamente

Digite:

```powershell
ollama run qwen3:4b
```

Quando aparecer o campo de conversa, escreva algo como:

```text
Responda em português: diga apenas "O modelo está funcionando".
```

Para sair, use:

```text
/bye
```

## 6. Confirmar que o serviço local está ativo

Normalmente o Ollama mantém o serviço local disponível em:

`http://127.0.0.1:11434`

O Desktop Study Companion utilizará:

`http://127.0.0.1:11434/v1/chat/completions`

Não é necessário configurar uma chave de API para o Ollama local.

## 7. Abrir o Desktop Study Companion

Use a versão portátil ou o inicializador de desenvolvimento normalmente.

Na personagem:

1. clique com o botão direito;
2. escolha **Configurações**;
3. abra a aba **Cérebro**.

## 8. Configurar o cérebro local

Preencha:

```text
Ativar conversa com LLM: marcado

URL base:
http://127.0.0.1:11434/v1

Modelo:
qwen3:4b

Variável da chave:
DESKTOP_STUDY_COMPANION_LLM_API_KEY

Temperatura:
0,7

Máx. tokens:
500

Timeout:
45 s

Histórico enviado:
12 mensagens
```

A variável da chave pode permanecer com o nome padrão. Como o Ollama local não precisa dela, não é necessário criar essa variável.

Clique em **Salvar**.

## 9. Conversar

Clique com o botão direito na personagem.

Escolha:

**Conversar**

Escreva:

```text
Quero estudar por 30 minutos. Pode me ajudar a começar?
```

A resposta deve:

- aparecer na janela;
- aparecer/falar pela personagem;
- movimentar a boca se o lip-sync estiver habilitado;
- utilizar o nome/personalidade configurados.

## 10. Testar contexto da sessão

Inicie uma sessão normal no Desktop Study Companion.

Depois abra **Conversar** e pergunte:

```text
O que eu deveria estar fazendo agora?
```

O cérebro recebe um resumo da sessão ativa e deve conseguir responder levando o objetivo atual em consideração.

## 11. Testar a separação de segurança

Na conversa, peça algo como:

```text
Feche meu navegador agora.
```

O comportamento correto é a personagem explicar que ações no desktop pertencem aos controles próprios do aplicativo.

A conversa com LLM não possui ferramenta de fechamento/minimização de janelas.

As Standing Rules e intervenções continuam funcionando separadamente, apenas conforme permissões configuradas pelo usuário.

## 12. Apagar o histórico

Na janela de conversa, clique em:

**Limpar histórico**

Isso apaga as mensagens da tabela local de conversas.

Não apaga:

- sessões de estudo;
- histórico de atividades;
- Directives;
- Standing Rules;
- configurações.

## 13. Se aparecer erro de conexão

Primeiro confira:

```powershell
ollama list
```

Depois confira se o modelo existe exatamente com o mesmo nome configurado.

Você também pode testar:

```powershell
ollama run qwen3:4b
```

Se o modelo abrir normalmente, confirme no aplicativo:

```text
URL base = http://127.0.0.1:11434/v1
Modelo   = qwen3:4b
```

## 14. Se o computador ficar lento

Tente um modelo menor:

```powershell
ollama pull qwen3:1.7b
```

Depois altere apenas o campo **Modelo** para:

```text
qwen3:1.7b
```

## 15. Usar outro servidor compatível

O cérebro não depende especificamente do Ollama.

Qualquer servidor que implemente o endpoint OpenAI-compatible `/v1/chat/completions` pode ser configurado.

Se for um serviço remoto que exige chave, não grave a chave em `config/default.json`.

Em uma sessão do PowerShell, use:

```powershell
$env:DESKTOP_STUDY_COMPANION_LLM_API_KEY = "SUA_CHAVE"
```

Depois inicie o Desktop Study Companion a partir daquela mesma sessão do PowerShell.

A aplicação lê a chave da variável de ambiente.

## 16. Privacidade

Com Ollama local, o objetivo é manter o processamento da conversa no próprio computador.

Se você configurar uma URL de um serviço remoto, o texto da conversa e o contexto comportamental incluído no prompt serão enviados a esse serviço.

Use endpoints remotos somente quando aceitar os termos e a política de privacidade do provedor.


## Diagnóstico rápido do cérebro — dev14

Antes de testar pelo Desktop Study Companion, confirme que o Ollama e o modelo funcionam sozinhos.

No PowerShell:

```powershell
ollama --version
ollama list
```

Confirme que o nome configurado no aplicativo aparece exatamente em `ollama list`.

Exemplo:

```text
qwen3:4b
```

Depois teste diretamente:

```powershell
ollama run qwen3:4b
```

Digite:

```text
Olá. Responda com uma frase curta em português.
```

Se houver resposta, digite:

```text
/bye
```

### Configuração recomendada no aplicativo

```text
Ativar cérebro: marcado
URL base: http://127.0.0.1:11434/v1
Modelo: qwen3:4b
Chave/API: não necessária para Ollama local
```

A partir da dev14, você **não precisa trocar a URL para /api/chat**. O aplicativo reconhece automaticamente a porta padrão do Ollama e usa internamente a API nativa:

```text
http://127.0.0.1:11434/api/chat
```

com o modo de thinking desativado para a conversa normal da personagem.

Essa mudança evita uma classe de problemas em que modelos Qwen retornam raciocínio interno, mas deixam a resposta final vazia pelo endpoint compatível com OpenAI.

### Ordem recomendada de teste

1. Teste `ollama run <modelo>`.
2. Abra o Desktop Study Companion.
3. Em **Configurações > Cérebro**, habilite o cérebro e salve.
4. Abra **Conversar**.
5. Envie primeiro uma mensagem por texto.
6. Só depois teste o microfone.

Se a resposta por texto falhar, consulte:

```text
Diagnóstico
→ Abrir pasta de logs
```

e procure por:

```text
Brain request
Brain response
Brain chat worker failed
Ollama returned no final content
```
