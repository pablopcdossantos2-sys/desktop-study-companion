# Diagnóstico e logs

A partir da **v0.1.0-dev11**, o Desktop Study Companion mantém logs persistentes para facilitar a investigação de erros que não aparecem na interface.

## Onde ficam os logs

Na versão portátil:

```text
data\logs\desktop-study-companion.log
```

O arquivo fica dentro da própria pasta do aplicativo.

O sistema usa rotação automática:

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
