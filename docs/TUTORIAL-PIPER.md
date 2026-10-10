# Tutorial — Configurar e diagnosticar a voz Piper

## 1. Preciso digitar um ID Piper manualmente?

Não.

A partir da **v0.1.0-dev17**, o caminho recomendado é:

1. clique com o botão direito na personagem;
2. abra **Configurações**;
3. entre na aba **Voz**;
4. em **Motor**, escolha **Piper neural local (recomendado)**;
5. em **Voz Piper**, escolha uma voz da lista;
6. clique em **Testar voz Piper**.

A interface salva internamente o ID técnico correto.

Os IDs continuam aparecendo neste documento apenas para diagnóstico e para
manter compatibilidade com configurações antigas.

## 2. Vozes em português do Brasil disponíveis na interface

A versão atual oferece:

- Faber — `pt_BR-faber-medium`;
- Jeff — `pt_BR-jeff-medium`;
- Cadu — `pt_BR-cadu-medium`;
- Edresson — `pt_BR-edresson-low`.

As variantes `medium` ocupam mais espaço, mas normalmente são a primeira
escolha para qualidade. A variante `low` é menor e pode ser útil em máquinas
mais limitadas.

## 3. Primeiro teste

Mantenha inicialmente:

```text
Motor: Piper neural local (recomendado)
Voz Piper: Faber, Jeff ou Cadu
Velocidade Piper: 1,00
Volume: 90%
Usar voz do Windows se o Piper falhar: marcado
```

Depois clique em:

```text
Testar voz Piper
```

O primeiro teste pode demorar mais porque o modelo de voz é baixado
automaticamente.

Os modelos ficam em:

```text
data\models\piper\
```

## 4. Como saber se o Piper realmente sintetizou

A dev17 mantém o último WAV criado pelo Piper em:

```text
data\temp\piper-last.wav
```

Depois de clicar em **Testar voz Piper**:

1. abra a pasta da instalação;
2. entre em `data\temp`;
3. procure `piper-last.wav`;
4. dê dois cliques no arquivo.

### Caso A — o WAV toca manualmente

Se o arquivo toca ao abrir pelo Windows, o Piper sintetizou corretamente.

Nesse caso, o problema está na reprodução automática dentro do aplicativo ou
no dispositivo de saída usado pelo Windows.

### Caso B — o WAV existe, mas está mudo ou inválido

Isso aponta para problema de síntese/modelo. Abra os logs e procure por linhas
contendo `Piper`.

### Caso C — o WAV não foi criado

O fluxo não chegou ao fim da síntese. O log deverá indicar download, carregamento
ou erro do modelo.

## 5. Onde olhar os logs

Clique com o botão direito na personagem:

```text
Diagnóstico
→ Abrir pasta de logs
```

Abra:

```text
desktop-study-companion.log
```

Procure, nesta ordem:

```text
Queued Piper utterance
Downloading Piper voice
Piper voice download completed
Piper voice loaded
Piper synthesis completed
Starting native Windows Piper playback
Native Windows Piper playback completed
Piper synthesis/playback failed
```

## 6. Se o modelo não baixar

Confirme que o computador possui acesso à internet no primeiro uso.

Depois tente outra voz da lista. Não é necessário baixar o arquivo ONNX
manualmente para o uso normal.

## 7. Se o modelo baixar e carregar, mas continuar sem som

Verifique:

1. se `data\temp\piper-last.wav` existe;
2. se o arquivo toca ao ser aberto manualmente;
3. se o Windows está usando o dispositivo de saída esperado;
4. se o volume do sistema não está em zero;
5. se o aplicativo não está silenciado no Mixer de Volume.

Mantenha **Usar voz do Windows se o Piper falhar** marcado enquanto o problema
estiver sendo investigado.

## 8. Testar outra voz

Repita o botão **Testar voz Piper** com:

```text
Faber
Jeff
Cadu
Edresson
```

Não é necessário reiniciar a aplicação entre os testes.

## 9. Por que existe um ID técnico?

O Piper identifica cada modelo por uma chave como:

```text
pt_BR-faber-medium
```

Esse identificador combina:

- idioma/região: `pt_BR`;
- nome do conjunto/voz: `faber`;
- qualidade: `medium`.

Na dev17, a interface cuida disso automaticamente para que o usuário não precise
decorar ou digitar essas chaves.

## 10. O que enviar ao relatar uma falha

Se a voz continuar sem funcionar, envie:

- a voz selecionada;
- se `piper-last.wav` foi criado;
- se esse WAV toca manualmente;
- as últimas linhas do log contendo `Piper`;
- o resumo de **Diagnóstico > Copiar resumo do diagnóstico**.

Com essas informações é possível saber se a falha está no download, no modelo,
na síntese ou na reprodução do Windows.
