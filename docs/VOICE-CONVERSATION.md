# Voz e conversa por push-to-talk

## Visão geral

A partir da v0.1.0-dev10, o Desktop Study Companion possui um ciclo de conversa por voz local:

```text
pressionar microfone
        ↓
captura PCM 16 kHz mono
        ↓
soltar botão
        ↓
WAV temporário
        ↓
faster-whisper
        ↓
texto
        ↓
BrainService / LLM
        ↓
resposta
        ↓
Windows SAPI + avatar
```

O reconhecimento de voz vem **desativado por padrão**.

## Por que faster-whisper

A build portátil atual não usa as APIs modernas de reconhecimento do Windows porque elas dependem de identidade de pacote/MSIX em cenários que conflitam com nosso executável portátil.

O projeto usa `faster-whisper` como backend local, executado no próprio computador.

Configuração padrão:

```text
model = base
language = pt
device = cpu
compute_type = int8
```

Essa configuração prioriza compatibilidade com computadores sem GPU dedicada.

## Primeira utilização

O runtime do STT vem dentro da build portátil, mas o modelo Whisper **não**.

Na primeira transcrição, o faster-whisper poderá baixar o modelo configurado.

O cache é mantido dentro da instalação do Desktop Study Companion:

```text
data\models\faster-whisper\
```

Depois que o modelo estiver em cache, as transcrições podem ser executadas localmente sem novo download.

O cache do modelo não entra nos backups comuns do aplicativo para evitar ZIPs muito grandes.

## Áudio temporário

Durante o push-to-talk:

1. o microfone é aberto;
2. o áudio é capturado em 16 kHz mono;
3. quando o botão é solto, é criado um WAV temporário;
4. o worker de STT lê esse WAV;
5. o arquivo é apagado no bloco `finally`, tanto em sucesso quanto em erro.

Arquivos temporários ficam em:

```text
data\temp\
```

O objetivo é não manter gravações de voz como histórico.

## Privacidade

O `faster-whisper` transcreve localmente.

O áudio capturado **não é enviado ao LLM**. Apenas o texto resultante é entregue ao `BrainService`.

Se o cérebro estiver configurado para Ollama local, tanto a transcrição quanto o processamento de texto podem permanecer no computador.

Se o cérebro apontar para um provedor remoto, o texto transcrito e o contexto do prompt poderão ser enviados a esse serviço conforme a configuração existente.

## Push-to-talk

Na janela **Conversar** existe o botão:

```text
Segure para falar
```

Comportamento:

- pressionar: interrompe TTS em andamento e abre o microfone;
- manter pressionado: continua gravando;
- soltar: encerra a gravação e inicia a transcrição;
- o limite máximo configurado encerra a gravação automaticamente.

O TTS é interrompido antes da captura para reduzir a chance de a personagem transcrever a própria voz.

## Envio automático ou revisão

Em **Configurações > Microfone**:

### Enviar automaticamente

Quando habilitado:

```text
fala → transcrição → mensagem enviada ao LLM
```

### Revisar antes de enviar

Quando desabilitado:

```text
fala → transcrição → texto colocado na caixa de entrada
```

O usuário pode corrigir o reconhecimento antes de clicar em **Enviar**.

## Microfone

A tela lista dispositivos de entrada disponíveis via PortAudio/sounddevice.

Há sempre uma opção:

```text
Microfone padrão do Windows
```

Quando selecionada, a decisão do dispositivo fica com a configuração de áudio do sistema operacional.

## Modelos

O campo **Modelo Whisper** aceita identificadores suportados pelo faster-whisper.

Para os primeiros testes:

- `tiny`: menor e mais rápido, menor precisão;
- `base`: padrão do projeto;
- `small`: maior precisão, maior consumo e download.

Modelos maiores podem tornar o primeiro uso lento em CPU.

## CPU e GPU

Padrão recomendado:

```text
device = cpu
compute_type = int8
```

A interface também expõe:

- `auto`;
- `cuda`.

CUDA só deve ser usada quando o computador possuir ambiente NVIDIA compatível.

## Voz da personagem

A aba **Voz** agora lista as vozes SAPI instaladas no Windows.

O usuário pode selecionar:

- voz padrão do Windows;
- uma voz instalada específica;
- velocidade;
- volume.

Se a voz selecionada deixar de existir, o SAPI permanece com a voz padrão disponível.

## Interrupção

O TTS passou a usar fala assíncrona SAPI com possibilidade de purge.

Isso permite:

- interromper uma resposta longa;
- evitar eco antes do push-to-talk;
- futuramente implementar barge-in mais completo.

A v0.1.0-dev10 ainda exige pressionar explicitamente o botão para falar; escuta contínua/wake word não está implementada.

## Limites atuais

- não há streaming parcial da transcrição;
- não há wake word;
- não há detecção automática de fim de fala;
- não há diarização;
- a primeira transcrição pode exigir download do modelo;
- a qualidade depende do microfone, ruído e tamanho do modelo;
- o lip-sync do avatar ainda segue duração aproximada, não o áudio real.


## Erro metadata_errors — corrigido na dev14

Se uma build anterior apresentava:

```text
open() got an unexpected keyword argument 'metadata_errors'
```

o problema era uma incompatibilidade de dependências:

- faster-whisper 1.2.1 ainda usa o parâmetro `metadata_errors`;
- PyAV 19 removeu esse parâmetro.

A dev14 fixa explicitamente:

```text
av >= 14 e < 19
```

O usuário não precisa instalar ou alterar PyAV manualmente na versão portátil.

Os logs agora registram início, sucesso e traceback de falhas do STT. Procure por:

```text
desktop_study_companion.voice.stt
desktop_study_companion.voice.stt_worker
```
