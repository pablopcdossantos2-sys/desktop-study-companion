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


## Escalada automática durante uma sessão

Além das Standing Rules, a sessão de estudo agora pode solicitar ações automaticamente conforme a severidade da distração.

Esse recurso possui uma permissão própria:

```text
Permitir escalada automática durante sessão de estudo
```

Ele permanece desligado por padrão.

Com os limites padrão de accountability:

```text
< 1 min  → nenhuma ação
1 min    → cobrança gentil
3 min    → cobrança firme
5 min    → cobrança direta
10 min   → cobrança insistente
```

A política de intervenção automática é:

```text
severidade 1 → fala
severidade 2 → fala
severidade 3 → minimizar, se autorizado
severidade 4 → fechar, se autorizado
```

Se a permissão de fechar não estiver ativa, severidade 4 usa a ação mais forte ainda permitida. Se nenhuma ação invasiva estiver autorizada, continua somente falando.

A política é determinística; um LLM não decide quando minimizar ou fechar.

## Lockdown limitado

O lockdown do Desktop Study Companion é propositalmente diferente do comportamento mais agressivo encontrado no bonziPONY.

Ele **não**:

- bloqueia mouse;
- bloqueia teclado;
- trava a estação;
- impede acesso ao Task Manager;
- sobrevive a uma reinicialização da aplicação.

Quando explicitamente autorizado, uma distração de severidade máxima pode ativar temporariamente o modo de foco limitado.

Durante esse período:

1. a sessão continua normalmente;
2. atividades produtivas não sofrem nenhuma intervenção;
3. novas distrações recebem imediatamente a ação mais forte autorizada;
4. a mesma janela possui cooldown para não receber ações a cada segundo;
5. o modo expira automaticamente;
6. encerrar a sessão encerra o lockdown;
7. o botão de emergência encerra o lockdown;
8. existe também **Encerrar lockdown atual** no menu.

A duração é configurável de 1 a 60 minutos.

## Falha segura

Arquivos de permissão inválidos ou malformados fazem a aplicação voltar aos padrões seguros:

```text
intervenções = desligadas
minimizar = desligado
fechar = desligado
escalada automática = desligada
lockdown = desligado
```

Uma configuração corrompida nunca deve resultar em permissões mais amplas.
