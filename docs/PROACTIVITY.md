# Proatividade, coach e gestos espontâneos

## Objetivo

A personagem não deve parecer um boneco que só reage quando o usuário fala com
ela. Ela deve sustentar uma presença ativa, especialmente quando o usuário
declarou que pretende estudar.

A evolução ocorreu em três etapas:

- **dev15:** frases motivacionais periódicas e gestos espontâneos;
- **dev17:** gestos corporais mais reconhecíveis;
- **dev21:** comportamento contextual de coach, repertório ampliado e frases
  programáveis pelo usuário.

A camada de coach funciona localmente mesmo sem Ollama.

## Modo Coach

Em **Configurações > Coach** é possível:

- habilitar/desabilitar iniciativas espontâneas;
- habilitar/desabilitar intervenções periódicas;
- habilitar/desabilitar o comportamento persistente de coach;
- definir intervalo mínimo e máximo;
- escrever frases próprias por contexto.

O intervalo padrão da dev21 fica entre **6 e 12 minutos**. O slider **Iniciativa** influencia o sorteio: iniciativa alta tende ao limite menor, sem ultrapassar os limites escolhidos pelo usuário.

Os contextos programáveis são:

- ativação quando não há sessão;
- foco durante sessão ativa;
- retomada após distração;
- comemoração;
- recomeço após sessão interrompida.

Se um campo de frases ficar vazio, o repertório padrão é usado.

Consulte [COACH-MODE.md](COACH-MODE.md) para os marcadores disponíveis,
exemplos e regras de comportamento.

## Comportamentos de coach durante uma sessão

Além das falas periódicas, a dev21 adiciona intervenções contextuais:

- mensagem de início que transforma a sessão em um compromisso claro;
- marcos em aproximadamente 25%, 50% e 75% do tempo planejado;
- reforço imediato quando o usuário retorna de uma distração;
- linguagem mais variada nos níveis de cobrança;
- reforço positivo ao concluir sessão ou compromisso;
- mensagem de recomeço quando a sessão termina antes do planejado.

Os marcos só são anunciados quando a atividade naquele momento está
classificada como produtiva.

## Quando a personagem evita interromper

Uma intervenção periódica não é disparada quando:

- o monitoramento está pausado;
- o microfone está gravando;
- uma consulta ao cérebro está em andamento;
- a personagem já está falando.

Isso reduz sobreposição entre voz, chat e cobrança.

## Relação com o cérebro conversacional

O cérebro LLM continua separado da política de desktop.

Na dev21, o prompt define explicitamente a personagem como **coach de estudo e
accountability**. Ela deve:

- transformar intenção em próxima ação;
- desafiar racionalizações com respeito;
- reforçar retomadas;
- valorizar consistência em vez de perfeição;
- evitar vergonha, ameaça, culpa ou incentivo a comportamento prejudicial.

O LLM não controla quando uma cobrança determinística acontece e não recebe
permissões para fechar ou minimizar aplicativos.

## Gestos espontâneos

Em **Configurações > Avatar** é possível habilitar os gestos e definir os
intervalos.

O conjunto procedural inclui:

- pequena dança de dois tempos;
- passar a mão no cabelo/lado da cabeça;
- pequeno salto;
- alongamento;
- aceno;
- postura pensativa.

Eles são combinados com respiração, transferência de peso, piscadas, look-at
e pequenos movimentos corporais.

Quando a personagem está falando, novos gestos espontâneos ficam
temporariamente suspensos para evitar sobreposição excessiva.

## Próximos passos

Evoluções futuras possíveis:

- gestos específicos para comemoração e cobrança;
- estados persistentes de humor;
- metas diárias e sequências de consistência;
- revisão semanal conduzida pela personagem;
- seleção de perfis prontos de coach;
- VRMA/Motion Capture.
