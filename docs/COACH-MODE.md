# Modo Coach

## Objetivo

O Modo Coach transforma a personagem de uma presença principalmente reativa
em uma companheira de estudo que acompanha o comportamento ao longo do tempo.

A intenção não é criar uma personagem punitiva. O objetivo é aumentar
**accountability, consistência e capacidade de retomada**, usando firmeza sem
humilhação.

## Quando a personagem age como coach

A partir da **v0.1.0-dev21**, existem cinco momentos comportamentais principais:

1. **Ativação** — quando não há sessão, a personagem pode incentivar o usuário
   a escolher uma tarefa e iniciar um bloco curto.
2. **Ancoragem de foco** — durante uma sessão, ela lembra o objetivo atual e
   pede uma próxima ação concreta.
3. **Retomada** — depois que uma distração termina, ela reforça a volta rápida
   ao objetivo em vez de apenas dizer "você voltou".
4. **Comemoração** — ao concluir uma sessão ou compromisso, ela reforça o
   comportamento que vale repetir.
5. **Recomeço** — quando uma sessão é interrompida, ela evita dramatização e
   propõe uma meta menor ou uma próxima tentativa concreta.

Além disso, sessões ativas recebem marcos de progresso em aproximadamente
**25%, 50% e 75%** do tempo planejado, desde que a atividade naquele momento
esteja classificada como produtiva.

## Frases periódicas

Em **Configurações > Coach** é possível:

- habilitar ou desabilitar iniciativas espontâneas;
- habilitar ou desabilitar as intervenções periódicas;
- habilitar ou desabilitar o comportamento persistente de coach;
- definir o intervalo mínimo e máximo;
- programar frases próprias para diferentes situações.

O padrão da dev21 é um intervalo sorteado entre **6 e 12 minutos**.

A personagem continua evitando uma intervenção periódica quando:

- o monitoramento está pausado;
- o microfone está gravando;
- existe uma consulta ao cérebro em andamento;
- ela já está falando.

## Bancos de frases personalizáveis

Cada campo aceita uma frase por linha.

Os cinco bancos são:

- **Ativação (sem sessão)**;
- **Foco (sessão ativa)**;
- **Retomada após distração**;
- **Comemoração**;
- **Recomeço/interrupção**.

Se um banco ficar vazio, a personagem usa o repertório padrão incluído no
programa. Se houver frases personalizadas, elas substituem o repertório padrão
daquela categoria.

### Marcadores disponíveis

As frases podem usar:

- `{name}` — nome da personagem;
- `{goal}` — objetivo atual;
- `{minutes}` — duração planejada da sessão;
- `{focused_minutes}` — minutos classificados como foco;
- `{distracted_minutes}` — minutos classificados como distração.

Exemplos:

```text
{name}, lembra do combinado: agora é {goal}.
Você já fez {focused_minutes} minutos de foco. Continua.
Voltou para {goal}. Protege só os próximos cinco minutos.
```

## Personalidade e insistência

Os sliders em **Configurações > Personalidade** continuam influenciando o tom:

- **Rigor** aumenta a objetividade das cobranças;
- **Sarcasmo** permite respostas mais provocativas, sem insultos;
- **Calor humano** aumenta acolhimento e reforço positivo;
- **Paciência** influencia quão tolerante é a linguagem;
- **Humor** modula leveza;
- **Iniciativa** também influencia a cadência: valores altos tendem a escolher intervalos mais próximos do limite mínimo configurado.

A política de tempo e severidade continua separada da personalidade. A
personagem não ganha permissão para fechar janelas ou alterar regras apenas
porque possui rigor alto.

## Insistência durante distrações

A cobrança por distração continua usando os níveis determinísticos do
`AccountabilityEngine`:

1. gentil;
2. firme;
3. direta;
4. insistente.

Na dev21, cada nível possui um repertório maior. Em níveis altos, a personagem
pode lembrar que a decisão de estudar já havia sido tomada e pedir retorno
imediato ao material.

Isso não muda os limites configurados pelo usuário nem as permissões para
intervenções no desktop.

## Cérebro conversacional

Quando Ollama ou outro cérebro compatível está habilitado, o prompt também
define explicitamente a personagem como **coach de estudo e accountability**.

Ela recebe as seguintes orientações:

- não confundir empatia com passividade;
- desafiar racionalizações de forma respeitosa;
- transformar metas vagas em próxima ação observável;
- valorizar retorno após distração;
- reforçar consistência em vez de perfeição;
- não incentivar privação de sono, excesso de estudo ou autocastigo.

O cérebro continua sem ferramentas de desktop. Ele não pode conceder
permissões nem executar ações no computador.

## Como deixar a personagem mais insistente

Uma configuração inicial razoável para quem quer uma coach ativa é:

- rigor: **80–90**;
- iniciativa: **80–90**;
- paciência: **35–50**;
- sarcasmo: **40–60**;
- intervalo de coach: **6–10 minutos**.

Para reduzir a presença da personagem, aumente o intervalo ou desative
**Falar intervenções de coach periodicamente**.

## Princípio de segurança

O Modo Coach deve cobrar comportamento, não atacar identidade.

Exemplos adequados:

> "Você saiu do plano. Volta para a próxima ação."

> "Não transforme alguns minutos perdidos em uma sessão perdida."

Exemplos que o sistema deve evitar:

> "Você é preguiçoso."

> "Você fracassou de novo."

> "Continue estudando mesmo sem dormir."

A firmeza deve servir para ajudar o usuário a executar uma decisão consciente,
não para produzir culpa ou coerção.


## Marcos atrasados — dev23

Os marcos de 25%, 50% e 75% representam o ponto atual da sessão, não uma fila
de notificações históricas. Se o usuário retornar ao foco depois de já ter
ultrapassado vários marcos, a personagem anuncia somente o **maior marco
atingido** e marca os anteriores como consumidos. Isso evita receber três
falas desatualizadas em sequência ao voltar de uma distração longa.
