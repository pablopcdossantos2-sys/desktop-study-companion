# Tutorial — Configurar e diagnosticar a voz Piper

## 1. Como testar a voz

Na **v0.1.0-dev23**, o procedimento recomendado é:

1. clique com o botão direito na personagem;
2. abra **Configurações**;
3. entre na aba **Voz**;
4. em **Motor**, escolha **Piper neural local (recomendado)**;
5. escolha uma voz em **Voz Piper**;
6. mantenha inicialmente a velocidade em **1,00**;
7. clique em **Testar voz Piper**.

Não é necessário digitar nenhum ID manualmente.

O resultado do teste aparece na própria aba **Voz**. Enquanto o teste está em
andamento, o botão fica temporariamente desativado para impedir downloads ou
sínteses concorrentes sobre os mesmos arquivos.

## 2. Vozes disponíveis

A interface oferece:

- Faber — `pt_BR-faber-medium`;
- Jeff — `pt_BR-jeff-medium`;
- Cadu — `pt_BR-cadu-medium`;
- Edresson — `pt_BR-edresson-low`.

As variantes `medium` são maiores e normalmente oferecem melhor qualidade.
`Edresson low` é menor e pode ser útil em máquinas mais limitadas.

## 3. O que mudou na dev22

Um log real da dev20 mostrou que o modelo era baixado e a síntese começava,
mas o componente nativo do pacote Python tentava abrir:

```text
D:/a/piper1-gpl/.../espeak-ng-data\phontab
```

Esse caminho pertence à máquina do GitHub Actions que compilou o wheel, não ao
computador do usuário.

Por isso, apenas reinstalar a voz ou escolher outro modelo não resolve esse
tipo de falha.

Na dev22, o executável portátil Windows deixa de depender desse componente
problemático para a etapa principal de síntese. A build inclui o runtime
standalone oficial legado do Piper para Windows (`rhasspy/piper
2023.11.14-2`), junto com o respectivo `espeak-ng-data`.

O pacote Python moderno continua presente para gerenciamento/download das
vozes e para compatibilidade em desenvolvimento.

## 4. Como funciona no portátil

O fluxo principal da dev22 é:

```text
Desktop Study Companion
        ↓
prepara/baixa o modelo de voz
        ↓
copia runtime + modelo para caminho temporário nativo compatível
        ↓
piper.exe standalone
        ↓
WAV
        ↓
winsound do Windows
```

A cópia temporária existe porque algumas bibliotecas nativas de voz/ONNX podem
se comportar mal com caminhos longos ou caracteres especiais. A pasta original
do programa pode continuar onde está; o usuário não precisa mover manualmente
a aplicação.

## 5. Primeiro teste

Use inicialmente:

```text
Motor: Piper neural local (recomendado)
Voz Piper: Faber
Velocidade Piper: 1,00
Volume: 90%
Usar voz do Windows se o Piper falhar: marcado
```

Clique uma vez em **Testar voz Piper** e aguarde o próprio campo
**Resultado do teste** mudar.

O primeiro uso de uma voz pode precisar baixar o arquivo ONNX.

Os modelos continuam armazenados em:

```text
data\models\piper\
```

## 6. WAV de diagnóstico

Quando a síntese termina com sucesso, o último WAV é salvo em:

```text
data\temp\piper-last.wav
```

Se desejar confirmar o áudio independentemente da aplicação:

1. abra a pasta da instalação;
2. entre em `data\temp`;
3. abra `piper-last.wav` pelo Windows.

### Se o WAV toca

A síntese funcionou. Se você não ouviu o som automaticamente, verifique
dispositivo de saída, Mixer de Volume e volume geral do Windows.

### Se o WAV não existe

A síntese não foi concluída. Consulte o campo **Resultado do teste** e o log.

## 7. O que procurar no log da dev22

Abra:

```text
Diagnóstico
→ Abrir pasta de logs
→ desktop-study-companion.log
```

Procure por:

```text
Queued Piper utterance
Piper model preparation
Starting bundled standalone Piper
Standalone Piper synthesis completed
Starting native Windows Piper playback
Native Windows Piper playback completed
Piper synthesis/playback failed
```

Em execução por código-fonte, o fallback de desenvolvimento ainda pode mostrar:

```text
Starting isolated Piper synthesis
Piper worker: stage=load
Piper worker: stage=synthesize
```

## 8. Se aparecer D:/a/piper1-gpl

Se o log ainda mostrar algo semelhante a:

```text
D:/a/piper1-gpl/piper1-gpl/_skbuild/...
```

você está usando uma build anterior ao mecanismo standalone da dev22 ou o
runtime standalone não foi encontrado no pacote.

Na versão portátil da dev22 deve existir:

```text
piper-runtime\piper.exe
piper-runtime\espeak-ng-data\phontab
```

Não crie esses arquivos manualmente.

## 9. Validação feita pela própria build

A build Windows da dev22 só é publicada depois de:

1. baixar o runtime standalone;
2. verificar `piper.exe`;
3. verificar `espeak-ng-data\phontab`;
4. baixar uma voz brasileira de teste;
5. sintetizar uma frase real;
6. confirmar que o WAV resultante possui áudio;
7. empacotar o mesmo runtime no ZIP final.

Portanto a presença do runtime deixa de ser apenas uma suposição de
empacotamento.

## 10. Fallback para voz do Windows

A opção:

```text
Usar voz do Windows se o Piper falhar
```

continua disponível.

Ela é útil para que a personagem permaneça capaz de falar mesmo se uma voz
específica não puder ser carregada.

O botão **Testar voz Piper** não usa o fallback para mascarar o resultado: ele
informa se o Piper propriamente dito funcionou ou falhou.

## 11. Testar outra voz

Depois que um teste terminar, o botão é reativado. Então você pode escolher:

```text
Faber
Jeff
Cadu
Edresson
```

e executar um novo teste.

Evite iniciar vários testes ao mesmo tempo; a interface agora impede isso
automaticamente.

## 12. O que enviar ao relatar uma falha

Se a dev22 ainda apresentar problema, envie:

- a voz selecionada;
- a mensagem exibida em **Resultado do teste**;
- se `data\temp\piper-last.wav` existe;
- se esse WAV toca manualmente;
- as últimas linhas do log contendo `Piper`;
- **Diagnóstico > Copiar resumo do diagnóstico**.

Esses dados permitem separar download, carregamento de modelo, runtime,
síntese e reprodução do Windows.


## 13. Robustez adicional da dev23

A dev23 mantém o runtime standalone introduzido na dev22 e acrescenta quatro
proteções:

1. **Volume Piper real:** o volume configurado passa a escalar as amostras
   PCM do WAV produzido pelo runtime standalone antes da reprodução.
2. **Cópia atômica do runtime:** a pasta temporária é copiada para um nome
   intermediário, validada por fingerprint e só então promovida. Uma cópia
   interrompida deixa de ser reutilizada.
3. **Estado explícito do teste:** o preview acompanha `pending`,
   `running`, `done` e `failed`. Depois de dois minutos ele pode informar
   que ainda está trabalhando, mas não declara falso erro enquanto o download
   continua. A preparação inicial do modelo possui um limite próprio maior.
4. **Arquivo do runtime fixado:** o CI compara o SHA-256 de
   `piper_windows_amd64.zip` com o valor esperado antes de extrair o
   executável. Uma alteração inesperada do asset faz a build falhar.

As cópias temporárias das vozes também são comparadas por SHA-256, e não
apenas pelo tamanho do arquivo.
