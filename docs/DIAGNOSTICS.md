# Diagnóstico e logs

A partir da **v0.1.0-dev11**, o Desktop Study Companion mantém logs persistentes para facilitar a investigação de erros que não aparecem na interface.

Desde a **v0.1.0-dev17** — e mantido na **dev19** — o diagnóstico também registra encerramentos
anormais e falhas nativas que podem fazer o executável desaparecer sem uma
mensagem Python visível.

## Onde ficam os logs

Na versão portátil:

```text
data\logs\desktop-study-companion.log
```

O arquivo fica dentro da própria pasta do aplicativo.

Além do log principal, o mecanismo introduzido na dev17 e mantido na dev19 mantém:

```text
data\logs\desktop-study-companion-fatal.log
data\logs\run-state.json
```

- `desktop-study-companion-fatal.log` recebe traces do `faulthandler` quando
  Python consegue observar uma falha fatal/nativa;
- `run-state.json` marca a execução como aberta no início e como encerrada
  corretamente no fechamento normal. Se o processo morrer abruptamente, a
  próxima inicialização detecta que a execução anterior não marcou saída limpa.

O sistema usa rotação automática no log principal:

- arquivo atual: `desktop-study-companion.log`;
- arquivos antigos podem aparecer como `.1`, `.2` etc.;
- cada arquivo é limitado a aproximadamente 2 MB;
- até cinco arquivos anteriores são mantidos.

## Abrir os logs pela interface

Clique com o botão direito na personagem:

```text
Diagnóstico
→ Abrir pasta de logs
```

O Windows abrirá diretamente a pasta correta.

Também existe:

```text
Diagnóstico
→ Copiar resumo do diagnóstico
```

Esse comando copia informações técnicas básicas, como:

- versão do Desktop Study Companion;
- versão do Python embutido;
- versão/plataforma do Windows;
- caminho da instalação;
- caminho do log;
- presença/tamanho do arquivo VRM;
- presença do renderer.

O resumo não inclui o histórico de janelas.

## O que é registrado

Os logs incluem, entre outros:

- inicialização do aplicativo;
- exceções Python não tratadas;
- exceções em threads;
- exceções em ciclos periódicos de monitoramento/proatividade sem encerrar o app;
- término do processo renderer do Qt WebEngine e tentativa automática de reload;
- detecção de execução anterior sem encerramento limpo;
- mensagens Qt/Qt WebEngine;
- inicialização e parada do servidor local do avatar;
- caminho/tamanho do arquivo VRM;
- console JavaScript do renderer;
- progresso e conclusão do carregamento do avatar;
- erros WebGL;
- erros JavaScript e promises rejeitadas;
- bounding box calculada para o VRM;
- parâmetros usados para posicionar a câmera;
- motivo exato de fallback para o ícone de livro.

## Linhas úteis para o avatar

Procure por:

```text
avatar-ready
avatar-fit
avatar-fatal
Avatar renderer error
Avatar failed
WebGL
```

A entrada `avatar-fit` contém as dimensões do modelo e da janela e permite verificar se cabeça, mãos e pés deveriam caber no frustum da câmera.

## Fallback do avatar

Se aparecer:

```text
Avatar 3D indisponível; usando fallback.
```

faça:

1. clique com o botão direito;
2. abra **Diagnóstico > Abrir pasta de logs**;
3. feche o aplicativo normalmente;
4. abra `desktop-study-companion.log`;
5. copie as últimas linhas que contenham `avatar`, `WebGL`, `error` ou `fatal`.

Você também pode usar **Copiar resumo do diagnóstico** e enviar o texto junto.

## Correção de enquadramento da dev11

A câmera do avatar deixou de usar um posicionamento baseado principalmente na altura.

Agora o renderer:

1. calcula a bounding box completa do VRM;
2. considera **altura e largura**;
3. considera o aspect ratio real da janela;
4. escolhe a maior distância necessária;
5. adiciona margem de 16%;
6. centraliza a câmera na bounding box;
7. recalcula o enquadramento quando a janela muda de tamanho.

Isso foi feito especificamente para evitar recorte de:

- mãos nas laterais;
- pés na parte inferior;
- cabelo/acessórios próximos às bordas.

O primeiro carregamento também passa a tolerar até aproximadamente **40 segundos** antes de considerar timeout. Isso evita falsos fallbacks em máquinas onde Qt WebEngine/WebGL demoram para inicializar.

## Privacidade

Os novos logs são locais.

O logger de diagnóstico não foi criado para registrar conteúdo integral de conversas nem áudio do microfone. Porém mensagens de bibliotecas e caminhos locais podem aparecer no arquivo.

Antes de publicar um log em fórum público, revise seu conteúdo.

Para suporte direto do projeto, normalmente bastam:

- as últimas linhas relacionadas ao erro;
- o resumo de diagnóstico;
- uma descrição do que estava visível na tela.


## Correção confirmada pelo log real — dev13

Um log real da dev11 mostrou esta sequência:

```text
avatar-load 100%
avatar-fit ...
avatar-ready ...
[~40 segundos]
avatar load timed out
```

Portanto, o VRM e o WebGL estavam prontos; o problema estava na comunicação de estado entre JavaScript e PySide6.

A dev13 serializa readiness/diagnostics/health como JSON textual antes de retornar pelo `QWebEnginePage.runJavaScript()`.

Após a correção, o esperado é aparecer no log:

```text
Avatar renderer reported ready
Avatar renderer diagnostics: {...}
```

sem um `avatar load timed out` posterior para a mesma instância.


## Se o programa fechar sozinho — diagnóstico introduzido na dev17 e mantido na dev19

1. Abra novamente o Desktop Study Companion.
2. Clique com o botão direito na personagem.
3. Abra **Diagnóstico > Abrir pasta de logs**.
4. Verifique primeiro `run-state.json`.
5. Depois abra `desktop-study-companion.log`.
6. Se existir conteúdo recente, confira também
   `desktop-study-companion-fatal.log`.

Procure no log principal por:

```text
Previous run did not record a clean exit
Monitoring cycle failed
Proactive motivation cycle failed
Avatar render process terminated
Fatal application startup/runtime error
```

Se `run-state.json` indicar `"clean_exit": false` depois de o programa ter
sumido, isso confirma que não foi usado o comando normal **Sair**.

O encerramento normal grava `"clean_exit": true`.
