# Intervenções no desktop

A camada de intervenção permite que uma regra permanente vá além da cobrança verbal.

Ela foi inspirada/adaptada das ações direcionadas de janela do bonziPONY, especialmente `robot/desktop_controller.py`.

## Princípio central

**Nada invasivo fica habilitado por padrão.**

Uma Standing Rule pode solicitar:

- `nag` — apenas cobrar;
- `minimize_and_nag` — minimizar e cobrar;
- `close_and_nag` — fechar e cobrar.

Mas a solicitação só é executada se a permissão global correspondente estiver habilitada.

## Dupla autorização

Para uma janela ser minimizada ou fechada, duas coisas precisam coincidir:

1. a regra precisa pedir aquela ação;
2. o usuário precisa ter habilitado a permissão correspondente em **Intervenções no desktop**.

Exemplo:

```text
Regra: não usar YouTube durante foco
Resposta: fechar e cobrar
```

Se `allow_close` estiver desativado:

```text
regra detectada
→ personagem reclama
→ nenhuma janela é fechada
```

## Fechamento de navegador

Seguindo o comportamento útil do bonziPONY, navegadores recebem tratamento especial.

Quando possível:

```text
Chrome / Edge / Firefox / Brave / Opera / Vivaldi
→ Ctrl+W
→ fecha somente a aba ativa
```

A intenção é evitar fechar o navegador inteiro.

Para outros programas, é enviado um pedido padrão de fechamento de janela do Windows. O próprio programa ainda pode exibir uma confirmação de salvamento.

## Processos críticos protegidos

Alguns processos nunca recebem ações invasivas, mesmo se forem removidos da lista editável:

- `explorer.exe`;
- `taskmgr.exe`;
- `powershell.exe`;
- `pwsh.exe`;
- `cmd.exe`;
- `conhost.exe`;
- `python.exe`;
- `pythonw.exe`;
- executável do Desktop Study Companion.

A lista configurável pode **acrescentar** outros programas protegidos.

## Botão de emergência

No menu da personagem:

```text
Intervenções no desktop
└── DESATIVAR INTERVENÇÕES AGORA
```

Essa ação:

- desliga o controle geral;
- revoga permissão de minimizar;
- revoga permissão de fechar;
- salva imediatamente o novo estado.

As regras permanecem cadastradas, mas voltam a funcionar apenas como cobranças.

## Persistência

As permissões ficam em:

```text
data\intervention_permissions.json
```

As regras continuam em:

```text
data\standing_rules.json
```

## Auditoria

Toda intervenção realmente executada é registrada em:

```text
data\companion.db
```

A tabela `interventions` registra, entre outros dados:

- tipo da ação;
- regra responsável;
- processo;
- título da janela;
- resposta configurada;
- resultado da tentativa.

## Separação do LLM

Mesmo quando um LLM for conectado:

- ele poderá sugerir linguagem;
- poderá sugerir regras;
- poderá pedir uma intervenção permitida;

mas não poderá:

- habilitar permissões sozinho;
- remover as proteções críticas;
- ignorar o botão de emergência;
- transformar uma regra `nag` em `close_and_nag` fora da política configurada.
