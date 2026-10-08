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
├── config/           # configuração tipada
├── memory/           # persistência local
├── personality/      # perfil comportamental
├── study/            # sessões, metas e estados de foco
├── ui/               # personagem/janela desktop
├── voice/            # contratos STT/TTS
└── app.py            # composição da aplicação
```

A intenção é evitar um núcleo monolítico e permitir que voz, LLM, memória, avatar e políticas de cobrança possam evoluir ou ser substituídos independentemente.

Veja [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). O funcionamento de sessões, rotinas, compromissos, regras permanentes e escalada está detalhado em [docs/ACCOUNTABILITY.md](docs/ACCOUNTABILITY.md). As intervenções opcionais no Windows estão documentadas em [docs/DESKTOP-INTERVENTIONS.md](docs/DESKTOP-INTERVENTIONS.md). A memória comportamental local e os indicadores estão descritos em [docs/BEHAVIORAL-MEMORY.md](docs/BEHAVIORAL-MEMORY.md).

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

Para testar a versão atual no Windows, siga [docs/TUTORIAL-INSTALACAO-WINDOWS.md](docs/TUTORIAL-INSTALACAO-WINDOWS.md). As limitações atuais estão documentadas em [docs/KNOWN-LIMITATIONS.md](docs/KNOWN-LIMITATIONS.md).

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

**v0.1.0-dev5 — MVP com escalada automática opt-in e lockdown limitado em validação no Windows.**

Já estão implementados monitor de janela ativa, sessões de estudo, compromissos persistentes, regras permanentes, rotinas proativas, escalada fala → minimizar → fechar, lockdown limitado e reversível, widget flutuante, persistência local, TTS do Windows e testes automatizados. Todas as ações de desktop permanecem opt-in. O avatar final, STT e LLM ainda não fazem parte desta versão.

A reutilização direta de componentes do bonziPONY está autorizada pelo criador do projeto, com obrigação de atribuição. A integração será feita seletivamente para preservar a arquitetura modular deste repositório.
