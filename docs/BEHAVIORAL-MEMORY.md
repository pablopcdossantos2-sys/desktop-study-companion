# Memória comportamental e analytics

A partir da v0.1.0-dev6, o Desktop Study Companion começa a transformar o histórico bruto de uso em contexto comportamental.

Essa camada funciona inteiramente de forma local e **não depende de LLM**.

## Fontes

Os cálculos usam o banco:

```text
data\companion.db
```

As fontes principais são:

- `study_sessions`;
- `activity_events`;
- `interventions`.

## Indicadores atuais

A janela **Histórico e insights** calcula, para os últimos 30 dias:

- quantidade de sessões;
- sessões concluídas;
- sessões abandonadas;
- tempo classificado como produtivo;
- tempo classificado como distração;
- taxa de foco;
- taxa de conclusão;
- número de intervenções;
- processo mais recorrente entre distrações;
- tipo de intervenção mais comum;
- taxa estimada de retorno à atividade produtiva até cinco minutos depois de uma intervenção;
- melhor horário de início, quando há pelo menos duas sessões comparáveis;
- tendência das três sessões mais recentes contra as três anteriores.

## Exemplos de insights

Depois que houver histórico suficiente, o companion pode produzir fatos como:

> Nos últimos registros, 74% do tempo classificado foi produtivo.

> O processo mais recorrente entre as distrações foi chrome.exe.

> Após uma intervenção, houve retorno a atividade produtiva em até cinco minutos em 67% dos casos.

> As sessões iniciadas por volta das 20:00 tiveram a melhor taxa média de foco.

Essas frases são geradas por regras determinísticas a partir do histórico. Não são inferências livres de um modelo de linguagem.

## Integração futura com LLM

A classe `StudyAnalytics` possui uma representação estruturada preparada para ser enviada posteriormente ao cérebro conversacional:

```json
{
  "period_days": 30,
  "session_count": 12,
  "completion_rate": 0.83,
  "average_focus_rate": 0.74,
  "top_distraction_process": "chrome.exe",
  "return_after_intervention_rate": 0.67,
  "best_focus_hour": 20,
  "recent_trend": "improving"
}
```

Assim, o futuro LLM poderá personalizar a conversa sem precisar analisar diretamente milhares de linhas do histórico.

## Uso ao final da sessão

Depois de pelo menos três sessões, o encerramento de uma sessão pode anexar um insight comportamental curto à fala de conclusão.

Exemplo:

> Sessão encerrada. Foco classificado: 42 minutos; distração: 8 minutos. Nos últimos registros, 76% do tempo classificado foi produtivo.

## Exportação

O menu:

```text
Histórico e dados
├── Histórico e insights
├── Exportar CSV
└── Criar backup ZIP
```

permite consultar e retirar os dados da aplicação.

### CSV

São produzidos:

- `study_sessions.csv`;
- `activity_events.csv`;
- `interventions.csv`.

Os arquivos usam UTF-8 com BOM para facilitar abertura no Excel.

### Backup ZIP

O backup contém:

- snapshot consistente de `companion.db`;
- arquivos JSON persistentes existentes em `data\`;
- `config/default.json`, quando disponível;
- `backup-metadata.json` com data e versão do programa.

O snapshot SQLite é feito pela API de backup do próprio SQLite, para evitar copiar um banco parcialmente gravado.
