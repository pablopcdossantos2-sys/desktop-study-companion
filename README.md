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

Veja [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). O funcionamento de sessões, rotinas, compromissos, regras permanentes e escalada está detalhado em [docs/ACCOUNTABILITY.md](docs/ACCOUNTABILITY.md). As intervenções opcionais no Windows estão documentadas em [docs/DESKTOP-INTERVENTIONS.md](docs/DESKTOP-INTERVENTIONS.md). A memória comportamental local e os indicadores estão descritos em [docs/BEHAVIORAL-MEMORY.md](docs/BEHAVIORAL-MEMORY.md). O avatar e o renderer VRM estão documentados em [docs/AVATAR-VRM.md](docs/AVATAR-VRM.md). A conversa com LLM e sua separação da camada de controle estão descritas em [docs/CONVERSATIONAL-BRAIN.md](docs/CONVERSATIONAL-BRAIN.md). O pipeline de voz e push-to-talk local está documentado em [docs/VOICE-CONVERSATION.md](docs/VOICE-CONVERSATION.md), e o diagnóstico passo a passo do Piper está em [docs/TUTORIAL-PIPER.md](docs/TUTORIAL-PIPER.md). Para usar um modelo local gratuitamente no Windows, consulte [docs/TUTORIAL-CEREBRO-LOCAL-OLLAMA.md](docs/TUTORIAL-CEREBRO-LOCAL-OLLAMA.md). Proatividade, motivação e gestos espontâneos estão descritos em [docs/PROACTIVITY.md](docs/PROACTIVITY.md).

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

**v0.1.0-dev17 — diagnóstico de encerramento anormal, Piper testável sem IDs manuais e gestos espontâneos intencionais.**

Já estão implementados monitor de janela ativa, sessões de estudo, compromissos persistentes, regras permanentes, rotinas proativas, escalada fala → minimizar → fechar, lockdown limitado e reversível, memória comportamental local, histórico/insights, configuração pela interface, exportação CSV, backup ZIP, build portátil do Windows, TTS com seleção de voz SAPI, avatar VRM 1.0 Sendagaya Shino, cérebro conversacional opcional e STT local por push-to-talk usando faster-whisper. A dev11 acrescentou logs rotativos de diagnóstico, captura de erros Qt/JavaScript do renderer, resumo técnico copiável e enquadramento full-body do avatar com margem. A dev12 corrige o empilhamento do menu/janelas sobre o WebEngine, adiciona pose de descanso e idle procedural visível, health check do renderer e tutoriais contextuais dentro do aplicativo. A dev13 corrige o bridge de controle JavaScript→PySide6: readiness e health check agora retornam JSON serializado em string, evitando o falso timeout observado em máquina real. A dev14 corrige o empilhamento e ciclo de vida dos menus/diálogos, fixa PyAV em versão compatível com faster-whisper 1.2.1 e usa automaticamente a API nativa do Ollama local com thinking desativado. A dev15 acrescentou TTS neural local Piper com fallback SAPI, frases motivacionais periódicas configuráveis, microgestos espontâneos e bloqueio explícito de saídas que pareçam raciocínio interno do LLM. A dev16 troca o playback Piper por WAV reproduzido pela API nativa do Windows, adiciona presets de vozes brasileiras e reforça o caminho Ollama/Qwen3 com `/no_think` na última mensagem, retry estrito e recomendação do modelo `qwen3:4b-instruct`. A dev17 acrescenta marcador de encerramento limpo/anormal, `faulthandler` persistente, recuperação explícita do processo renderer do Qt WebEngine, contenção de falhas nos ciclos periódicos, seleção Piper sem digitação manual de IDs, botão **Testar voz Piper**, WAV diagnóstico em `data/temp/piper-last.wav` e gestos espontâneos mais intencionais — dança curta, mão no cabelo e pequeno salto. O LLM continua sem ferramentas nem permissões de desktop; intervenções permanecem numa camada determinística separada e opt-in.

A reutilização direta de componentes do bonziPONY está autorizada pelo criador do projeto, com obrigação de atribuição. A integração será feita seletivamente para preservar a arquitetura modular deste repositório.
