# Proatividade, motivação e gestos espontâneos

## Objetivo

A personagem não deve parecer um boneco que só reage quando o usuário fala com ela.

A partir da **v0.1.0-dev15**, existem duas camadas de comportamento espontâneo:

1. **microgestos do avatar**;
2. **frases motivacionais periódicas**.

Essas camadas são independentes do cérebro LLM.

## Frases motivacionais

Em **Configurações > Proatividade** é possível:

- habilitar/desabilitar iniciativas espontâneas;
- habilitar/desabilitar frases motivacionais;
- definir intervalo mínimo;
- definir intervalo máximo.

O intervalo padrão é sorteado entre **8 e 16 minutos**.

A personagem evita interromper quando:

- o monitoramento está pausado;
- o microfone está gravando;
- uma consulta ao cérebro está em andamento;
- ela já está falando.

Se houver uma sessão de estudo ativa, as frases podem mencionar o objetivo atual.
Sem sessão ativa, as mensagens incentivam o usuário a iniciar um pequeno bloco de trabalho.

As frases desta camada são locais e determinísticas. Elas não precisam de Ollama, internet ou API.

## Gestos espontâneos

Em **Configurações > Avatar** é possível habilitar os gestos e definir os intervalos.

A dev15 inclui quatro microgestos procedurais:

- olhar ao redor;
- alongamento discreto;
- pequeno aceno;
- postura pensativa.

Eles são combinados com:

- respiração;
- transferência de peso;
- piscadas;
- look-at;
- movimento de cabeça, tórax, ombros e mãos.

O objetivo não é reproduzir uma animação cinematográfica, mas quebrar a repetição da mesma pose.

## Relação com fala

Quando a personagem está falando:

- o movimento de boca continua ativo;
- o idle corporal continua;
- novos gestos espontâneos ficam temporariamente suspensos para evitar sobreposição excessiva.

## Próximos passos

Ainda podem ser adicionados:

- gestos específicos para comemoração;
- gestos específicos para cobrança;
- VRMA/Motion Capture;
- estados persistentes de humor;
- seleção de conjuntos de animação pela interface.
