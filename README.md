# Desktop Study Companion

Companhia virtual para Windows voltada a **estudo, foco e accountability**.

A proposta é manter uma personagem persistente na área de trabalho que possa conversar por voz, acompanhar sessões de estudo, perceber distrações, lembrar compromissos, adaptar a própria personalidade e intervir de forma progressiva quando o usuário abandonar uma meta assumida.

## Objetivo do projeto

O Desktop Study Companion deverá ser capaz de completar o seguinte ciclo:

1. O usuário define uma intenção: “vou estudar por 60 minutos”.
2. A aplicação registra a sessão e passa a observar o contexto local do computador.
3. O sistema identifica aplicativos/janelas produtivos, neutros ou distrativos.
4. A personagem reage de acordo com a duração e a gravidade da distração.
5. A cobrança pode escalar de um lembrete gentil até intervenções previamente autorizadas.
6. Ao final, a sessão é registrada e o resultado alimenta memória, histórico e futuras interações.

## Referência principal

O projeto toma **bonziPONY** como principal referência funcional:

- https://github.com/maresmaremares/bonziPONY

Recursos especialmente relevantes observados no projeto de referência incluem presença persistente no desktop, voz, monitoramento da janela ativa, diretivas, regras permanentes, rotinas, visão e mecanismos progressivos de cobrança.

> **Atribuição:** este projeto utiliza e adapta código e arquivos do projeto **bonziPONY**, de [maresmaremares](https://github.com/maresmaremares/bonziPONY). O criador do bonziPONY autorizou pessoalmente a reutilização livre do código e dos arquivos, solicitando apenas que o uso seja citado no README deste projeto. Consulte [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) e [docs/UPSTREAM-LICENSE.md](docs/UPSTREAM-LICENSE.md).

## Arquitetura inicial

O núcleo foi deliberadamente separado em módulos pequenos:

```text
src/desktop_study_companion/
├── accountability/   # regras, severidade e intervenções
├── activity/         # contexto do computador e janela ativa
├── brain/            # conversa LLM isolada das permissões de desktop
├── config/           # configuração tipada
├── memory/           # persistência local
├── personality/      # perfil comportamental
├── study/            # sessões, metas e estados de foco
├── ui/               # personagem/janela desktop
├── voice/            # contratos STT/TTS
└── app.py            # composição da aplicação
```

A intenção é evitar um núcleo monolítico e permitir que voz, LLM, memória, avatar e políticas de cobrança possam evoluir ou ser substituídos independentemente.

Veja [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). O funcionamento de sessões, rotinas, compromissos, regras permanentes e escalada está detalhado em [docs/ACCOUNTABILITY.md](docs/ACCOUNTABILITY.md). As intervenções opcionais no Windows estão documentadas em [docs/DESKTOP-INTERVENTIONS.md](docs/DESKTOP-INTERVENTIONS.md). A memória comportamental local e os indicadores estão descritos em [docs/BEHAVIORAL-MEMORY.md](docs/BEHAVIORAL-MEMORY.md). O avatar e o renderer VRM estão documentados em [docs/AVATAR-VRM.md](docs/AVATAR-VRM.md). A conversa com LLM e sua separação da camada de controle estão descritas em [docs/CONVERSATIONAL-BRAIN.md](docs/CONVERSATIONAL-BRAIN.md). O pipeline de voz e push-to-talk local está documentado em [docs/VOICE-CONVERSATION.md](docs/VOICE-CONVERSATION.md), e o diagnóstico passo a passo do Piper está em [docs/TUTORIAL-PIPER.md](docs/TUTORIAL-PIPER.md). Para usar um modelo local gratuitamente no Windows, consulte [docs/TUTORIAL-CEREBRO-LOCAL-OLLAMA.md](docs/TUTORIAL-CEREBRO-LOCAL-OLLAMA.md). Proatividade e gestos espontâneos estão descritos em [docs/PROACTIVITY.md](docs/PROACTIVITY.md), e o comportamento programável de coach em [docs/COACH-MODE.md](docs/COACH-MODE.md).

## Escopo da v0.1

A primeira versão deverá validar a essência do produto:

- janela/companheira transparente e sempre visível;
- monitoramento local da janela ativa no Windows;
- início e encerramento de sessão de estudo;
- classificação configurável de aplicações;
- detecção de distração;
- níveis progressivos de cobrança;
- registro local de sessões e intervenções;
- personalidade configurável;
- contratos para TTS/STT e LLM, mesmo que inicialmente alguns sejam stubs.

O roadmap completo está em [docs/ROADMAP.md](docs/ROADMAP.md).

Para testar a versão atual no Windows, siga [docs/TUTORIAL-INSTALACAO-WINDOWS.md](docs/TUTORIAL-INSTALACAO-WINDOWS.md). As limitações atuais estão documentadas em [docs/KNOWN-LIMITATIONS.md](docs/KNOWN-LIMITATIONS.md). Para diagnosticar falhas de avatar, WebEngine, voz ou inicialização, consulte [docs/DIAGNOSTICS.md](docs/DIAGNOSTICS.md).

## Princípios

- **Local first:** atividade e histórico devem permanecer locais por padrão.
- **Consentimento:** ações invasivas, como fechar ou bloquear aplicativos, devem exigir autorização explícita.
- **Explicabilidade:** a interface deve conseguir informar por que classificou algo como distração e por que interveio.
- **Personalidade separada de política:** “ser sarcástica” não deve alterar regras de segurança.
- **Modularidade:** monitoramento, memória, voz, LLM e UI não devem depender diretamente uns dos outros.
- **Sem vigilância secreta:** o usuário deve conseguir pausar facilmente o monitoramento.

## Desenvolvimento inicial

Requisitos planejados:

- Windows 10/11;
- Python 3.11 ou superior;
- ambiente virtual recomendado.

Quando o primeiro protótipo executável estiver concluído:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
desktop-study-companion
```

## Estado

**v0.1.0-dev23 — correções da quinta auditoria: coach, diálogos, Piper e configuração protegidos.**

Já estão implementados monitor de janela ativa, sessões de estudo, compromissos persistentes, regras permanentes, rotinas proativas, escalada fala → minimizar → fechar, lockdown limitado e reversível, memória comportamental local, histórico/insights, configuração pela interface, exportação CSV, backup ZIP, build portátil do Windows, TTS com seleção de voz SAPI, avatar VRM 1.0 Sendagaya Shino, cérebro conversacional opcional e STT local por push-to-talk usando faster-whisper. A **dev17** introduziu o diagnóstico de encerramento anormal, o isolamento do Piper/ONNX em processo auxiliar, seleção de voz Piper sem IDs manuais, WAV de diagnóstico e gestos espontâneos mais intencionais. A **dev18** endureceu a persistência e a segurança operacional: quarentena de JSON corrompido, escrita atômica, instância única, reconciliação de sessões órfãs, proteção contra falsos positivos de classificação, CSV seguro e filas de voz limitadas. A **dev19** acrescentou fallback automático para configuração inválida, compatibilidade com Ollama em LAN sem segredo, regras permanentes com matcher seguro, tolerância de conclusão de sessão, rotinas completas pela interface, STT com idioma automático e analytics apenas com sessões encerradas. A **dev20** corrigiu os efeitos colaterais encontrados na quarta auditoria: testes independentes de fuso, preservação integral da configuração quando apenas o transporte do cérebro é inseguro, retry de leitura sem quarentena indevida, deduplicação de snapshots JSON, renderer compilado dentro do wheel e rotina on-wake somente após pelo menos 10 minutos de ausência. A **dev21** transforma a personagem em uma coach de estudo mais presente: repertório de cobrança ampliado, cinco bancos de frases programáveis, intervenções periódicas contextuais, marcos de 25/50/75% da sessão, reforço de retomada após distração, comemoração de consistência, recomeço após sessão interrompida e um prompt conversacional explicitamente orientado a accountability. A **dev22** corrige a ergonomia das janelas e a voz Piper no portátil Windows: diálogos e seletores deixam de bloquear a personagem, são posicionados longe do avatar, permanecem fecháveis, e o Piper portátil passa a preferir um runtime standalone Windows empacotado e testado por síntese real no CI, evitando o bug nativo do wheel que apontava para caminhos de build do GitHub Actions. O teste de voz também informa sucesso ou falha diretamente na aba Voz e evita testes concorrentes. A **dev23** fecha os achados da quinta auditoria: o coach descarta marcos intermediários atrasados, o volume do Piper standalone passa a ser aplicado às amostras PCM, só um diálogo síncrono pode ficar aberto por vez, o runtime e as vozes Piper são copiados atomicamente e validados por hash, o preview usa estados explícitos e tolera downloads longos, o ZIP do runtime é fixado por SHA-256 no CI e configurações carregadas por fallback são preservadas em `.bak` antes de qualquer sobrescrita. O LLM continua sem ferramentas nem permissões de desktop; intervenções permanecem numa camada determinística separada e opt-in.

A reutilização direta de componentes do bonziPONY está autorizada pelo criador do projeto, com obrigação de atribuição. A integração será feita seletivamente para preservar a arquitetura modular deste repositório.
