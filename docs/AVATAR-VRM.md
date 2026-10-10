# Avatar VRM

## Modelo adotado

**Sendagaya Shino** — VRM 1.0.

Página oficial:

https://hub.vroid.com/en/characters/4593660874193246717/models/7956589129305596116

A coleção é declarada CC0 no VRoid Hub. A página do modelo também permite uso como avatar, uso comercial/corporativo, redistribuição, alterações e redistribuição de alterações, sem exigir atribuição.

## Arquitetura

```text
PySide6 / CompanionWidget
        │
        ▼
AvatarWidget (Qt WebEngine)
        │
        ▼
servidor HTTP local 127.0.0.1
        │
        ├── renderer Vite/Three.js
        └── Sendagaya_Shino.vrm
```

O renderer web é construído em `avatar_web/` usando:

- Three.js;
- `@pixiv/three-vrm`;
- GLTFLoader;
- VRMLoaderPlugin.

Node.js é necessário apenas para construir o renderer. A build portátil inclui os arquivos prontos e funciona offline em runtime.

## Recursos já conectados

- VRM 1.0;
- transparência;
- avatar sempre no topo junto ao widget;
- piscar automático;
- `lookAt` seguindo o cursor;
- expressões `neutral`, `happy`, `relaxed` e `angry` ligadas ao estado do companion;
- visemes `aa`, `ih`, `ou`, `ee`, `oh` usados para lip-sync aproximado enquanto a personagem fala;
- spring bones atualizados pelo loop do VRM;
- fallback para ícone simples caso o renderer ou modelo não esteja disponível.

## Integridade do modelo

Arquivo esperado:

`assets/avatar/Sendagaya_Shino.vrm`

SHA-256:

`fab70124f0025e444a6eef84d6ab3a04e78c0adb626099e54b55287d0f083a47`

`scripts/fetch-avatar.ps1` baixa e valida o arquivo antes de aceitá-lo.

## Empacotamento

O GitHub Actions:

1. baixa e valida o VRM;
2. instala Node;
3. compila o renderer;
4. executa a suíte Python;
5. empacota PySide6 + Qt WebEngine com PyInstaller;
6. inclui o renderer e o VRM no ZIP portátil.

## Próximas melhorias

- animações corporais/VRMA;
- idle breathing mais elaborado;
- expressões compostas e intensidade variável;
- sincronização labial baseada no áudio real do TTS;
- gestos de cobrança e comemoração;
- configuração de escala/enquadramento;
- possível importação de outros modelos VRM pela interface.


## Configuração pela interface

A aba **Configurações > Avatar** permite alterar:

- ativar/desativar o avatar VRM;
- largura da janela;
- altura da janela;
- acompanhamento do cursor com `lookAt`;
- animação aproximada da boca durante a fala.

Essas opções são persistidas em `config/default.json` e aplicadas sem reiniciar o aplicativo.

Desativar o avatar não desativa o Study Accountability Engine, TTS, histórico ou monitoramento. Apenas substitui a renderização 3D pelo fallback visual.


## Enquadramento full-body

A dev11 passou a enquadrar a câmera pela bounding box completa do VRM.

O cálculo considera:

- altura do modelo;
- largura do modelo;
- aspect ratio atual do canvas;
- profundidade aproximada;
- margem adicional de 16%.

A distância final usa a maior exigência entre o encaixe vertical e horizontal. Isso evita que uma janela estreita preserve cabeça/pés, mas corte as mãos lateralmente.

O enquadramento é recalculado quando o renderer muda de tamanho.

## Diagnóstico do renderer

O console JavaScript do avatar é espelhado em:

`data/logs/desktop-study-companion.log`

O renderer registra:

- progresso do VRM;
- dimensões da bounding box;
- posição/FOV/distância da câmera;
- disponibilidade de WebGL;
- conclusão do carregamento;
- erros JavaScript/WebGL.

O timeout inicial foi ampliado para cerca de 40 segundos para reduzir fallbacks falsos durante a primeira inicialização do Qt WebEngine.


## Idle procedural da dev12

A dev12 deixa de apresentar o modelo como uma estátua em pose de referência.

Ao carregar o VRM, o renderer cria uma pose de descanso a partir dos ossos humanoides normalizados e baixa os braços para uma postura natural. Em seguida aplica continuamente movimentos pequenos de:

- respiração;
- transferência de peso;
- quadril;
- coluna e tórax;
- pescoço e cabeça;
- ombros;
- braços;
- antebraços;
- mãos.

Durante fala e algumas expressões, a amplitude aumenta discretamente.

Essa animação é procedural e não depende de arquivos VRMA externos. VRMA continua planejado para gestos complexos.

## Estabilidade do renderer

A dev12 também:

- desabilita throttling/backgrounding do Chromium para a janela transparente;
- monitora a saúde do renderer a cada 5 segundos;
- detecta perda persistente do contexto WebGL;
- tenta recarregar o renderer após três verificações consecutivas com falha;
- registra todo o processo nos logs.

Isso reduz casos em que a personagem some e volta sem explicação.
