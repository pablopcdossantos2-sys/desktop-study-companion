# Tutorial de instalação e teste no Windows

Este tutorial foi escrito para quem não costuma trabalhar com terminal, Python ou GitHub.

A versão atual é um **protótipo de desenvolvimento da v0.1**. Ela já permite testar o ciclo básico:

> iniciar sessão → usar o computador → abrir uma distração reconhecida → receber cobrança → retornar ao estudo → encerrar e registrar a sessão.

## 1. O que você precisa

- Windows 10 ou Windows 11;
- conexão com a internet apenas para baixar o projeto e instalar as dependências;
- Python 3.11 ou 3.12.

Não é necessário instalar Node.js.

## 2. Instalar o Python

### Opção recomendada: pelo PowerShell

1. Clique no menu **Iniciar**.
2. Digite **PowerShell**.
3. Abra **Windows PowerShell** ou **Terminal**.
4. Cole este comando e pressione Enter:

```powershell
winget install --id Python.Python.3.12 -e
```

5. Ao terminar, feche o PowerShell.
6. Abra-o novamente.
7. Digite:

```powershell
py -3.12 --version
```

Você deverá ver algo semelhante a:

```text
Python 3.12.x
```

Se aparecer uma versão 3.12, esta etapa está concluída.

## 3. Baixar o projeto

Abra:

https://github.com/pablopcdossantos2-sys/desktop-study-companion

No GitHub:

1. clique no botão verde **Code**;
2. clique em **Download ZIP**;
3. aguarde o download;
4. abra a pasta **Downloads**;
5. clique com o botão direito no ZIP;
6. escolha **Extrair tudo**;
7. escolha uma pasta fácil de localizar, por exemplo:

```text
C:\Users\SEU_USUARIO\Documents\Programas\desktop-study-companion
```

### Importante

Depois de extrair, verifique se dentro da pasta aparecem arquivos como:

```text
README.md
pyproject.toml
INICIAR-DEV.bat
config
docs
src
tests
```

Se houver outra pasta `desktop-study-companion-main` dentro dela, entre nessa pasta. O arquivo `INICIAR-DEV.bat` deve estar no mesmo nível do `README.md`.

## 4. Iniciar pela primeira vez

A forma mais fácil é:

1. localize `INICIAR-DEV.bat`;
2. dê dois cliques nele;
3. uma janela do PowerShell será aberta.

Na primeira execução, o script irá automaticamente:

1. localizar o Python;
2. criar uma pasta chamada `.venv`;
3. instalar as dependências do projeto;
4. executar os testes automáticos;
5. iniciar a aplicação.

A primeira instalação baixa o PySide6 e pode exibir várias mensagens no terminal. Isso é esperado.

## 5. Como saber se funcionou

Quando a aplicação iniciar, deverá aparecer um pequeno elemento flutuante na área de trabalho com um ícone de livro e um balão de fala.

Ele fica acima das outras janelas.

Você pode arrastá-lo segurando o botão esquerdo do mouse.

Clique nele com o **botão direito** para abrir o menu.

## 6. Criar a primeira sessão

1. Clique com o botão direito no personagem.
2. Escolha **Iniciar sessão de estudo**.
3. Em **Objetivo**, escreva algo como:

```text
Testar o Desktop Study Companion
```

4. Para o primeiro teste, escolha uma duração pequena, como **5 minutos**.
5. Confirme.

O personagem deverá dizer que acompanhará a sessão.

## 7. Testar a detecção de distração sem esperar muito

Por padrão, a primeira cobrança acontece após 60 segundos de distração.

Para testar mais rapidamente:

1. feche a aplicação;
2. abra o arquivo:

```text
config\default.json
```

3. Você pode abrir com o Bloco de Notas.
4. Localize:

```json
"gentle_after_seconds": 60,
"firm_after_seconds": 180,
"direct_after_seconds": 300,
"insistent_after_seconds": 600
```

5. Temporariamente substitua por:

```json
"gentle_after_seconds": 5,
"firm_after_seconds": 10,
"direct_after_seconds": 15,
"insistent_after_seconds": 20
```

6. Salve.
7. Execute `INICIAR-DEV.bat` novamente.
8. Inicie uma sessão.
9. Abra, por exemplo, uma página do **YouTube**.

Em aproximadamente cinco segundos, a primeira cobrança deverá aparecer.

Depois de confirmar que funciona, você pode restaurar os valores originais.

## 8. Como a aplicação sabe que algo é distração

Abra:

```text
config\default.json
```

Você encontrará três listas.

### Produtivos

Exemplo:

```json
"productive_keywords": [
  "anki",
  "obsidian",
  "visual studio code"
]
```

### Neutros

Aplicações que não contam como estudo, mas também não geram cobrança.

### Distrações

Exemplo:

```json
"distraction_keywords": [
  "youtube",
  "netflix",
  "reddit",
  "instagram"
]
```

A versão atual compara essas palavras com:

- nome do programa;
- título da janela.

Assim, o Chrome inteiro não precisa ser classificado como distração. Uma aba cujo título contenha `YouTube`, por exemplo, pode ser identificada especificamente.

## 9. Personalizar a personalidade provisória

No mesmo arquivo há:

```json
"personality": {
  "name": "Companion",
  "warmth": 60,
  "sarcasm": 55,
  "strictness": 80,
  "patience": 40,
  "humor": 50,
  "initiative": 75
}
```

Nesta versão, apenas alguns desses valores já influenciam as mensagens. Eles serão expandidos nas próximas versões.

Todos devem ficar entre 0 e 100.

## 10. Onde os dados são armazenados

Depois da primeira execução, será criada:

```text
data\companion.db
```

Esse banco SQLite armazena localmente:

- sessões;
- eventos de atividade;
- intervenções.

Ele não é enviado automaticamente para nenhum serviço externo.

## 11. Pausar o monitoramento

Clique com o botão direito no personagem e escolha:

**Pausar monitoramento**

Para voltar:

**Retomar monitoramento**

Esse controle existe para que o monitoramento nunca seja silencioso ou inevitável.

## 12. Encerrar

Clique com o botão direito e escolha:

**Sair**

Se houver sessão registrada, seu estado mais recente será salvo.

## 13. Executar novamente em outro dia

Você não precisa reinstalar manualmente as dependências.

Basta dar dois cliques novamente em:

```text
INICIAR-DEV.bat
```

O script reutiliza o ambiente `.venv`. Ele ainda verifica/atualiza a instalação do projeto porque estamos em fase ativa de desenvolvimento.

## 14. Se algo der errado

Não feche imediatamente a janela do PowerShell.

Copie a mensagem de erro completa e envie no ChatGPT.

Também informe:

1. em qual passo ocorreu;
2. se o elemento flutuante chegou a aparecer;
3. qual versão do Windows você usa;
4. o resultado deste comando:

```powershell
py -3.12 --version
```

## 15. O que eu preciso que você teste

Para validar a v0.1 no Windows, faça quatro testes:

1. **Inicialização:** o personagem aparece?
2. **Movimento:** consegue arrastá-lo pela área de trabalho?
3. **Detecção:** com os limites reduzidos para 5/10/15/20 segundos, abrir YouTube durante uma sessão produz cobranças progressivas?
4. **Retorno:** ao sair do YouTube e voltar para um aplicativo classificado como produtivo, aparece a mensagem de retorno?

Se algum teste falhar, envie a mensagem exibida no PowerShell e descreva o comportamento observado.

Não é necessário fornecer nenhum dado pessoal do banco `companion.db`.


## 16. Testar a voz

A versão atual usa o sintetizador de fala que já existe no Windows.

Depois de iniciar uma sessão, a personagem deverá falar algumas mensagens, inclusive as cobranças.

Se você quiser testar sem som:

1. feche a aplicação;
2. abra `config\default.json`;
3. localize:

```json
"voice": {
  "enabled": true,
  "rate": 0,
  "volume": 90
}
```

4. troque `true` por `false`;
5. salve e execute novamente.

`rate` aceita valores entre -10 e 10.

`volume` aceita valores entre 0 e 100.

Nesta versão, a voz utilizada é uma das vozes SAPI configuradas no Windows. A seleção de voz pela própria interface será adicionada depois.

## 17. Informações úteis ao relatar um problema

Se a interface funcionar, mas a voz não sair, informe especificamente:

- se as mensagens aparecem no balão;
- se outras aplicações do Windows conseguem usar leitura em voz alta;
- se aparece algum erro no PowerShell;
- se `"voice": { "enabled": true ... }` continua habilitado.

Assim conseguiremos separar problemas de monitoramento, interface e voz.


## 18. Testar uma rotina proativa

A versão atual já incorpora uma adaptação do sistema de rotinas persistentes do bonziPONY.

Esse teste verifica se a personagem consegue falar com você **sem que uma sessão de estudo esteja ativa**.

1. Inicie o Desktop Study Companion.
2. Clique com o botão direito no personagem.
3. Escolha **Adicionar rotina diária**.
4. Em **Lembrete/meta**, escreva algo como:

```text
Começar a estudar matemática
```

5. Escolha um horário dois ou três minutos à frente do horário atual.
6. Em **Urgência**, escolha, por exemplo, `8`.
7. Confirme.
8. Não inicie nenhuma sessão de estudo.
9. Mantenha a aplicação aberta até chegar ao horário escolhido.

No horário da rotina, a personagem deverá exibir e falar espontaneamente algo semelhante a:

```text
Isso é importante. Hora da rotina. Começar a estudar matemática.
```

### Gerenciar ou remover uma rotina

1. Clique com o botão direito no personagem.
2. Escolha **Gerenciar rotinas**.
3. Selecione a rotina.
4. Escolha:
   - **Ativar/Desativar**, ou
   - **Remover**.

As rotinas ficam armazenadas localmente em:

```text
data\routines.json
```

Elas permanecem cadastradas mesmo depois que a aplicação é fechada e aberta novamente.


## 19. Testar um compromisso que insiste

Um **compromisso** é diferente de um lembrete: ele continua ativo até você marcar como concluído ou removê-lo.

1. Inicie a aplicação.
2. Clique com o botão direito no personagem.
3. Abra **Compromissos > Adicionar compromisso**.
4. Em **Compromisso**, escreva:

```text
Terminar o teste do sistema
```

5. Coloque **Urgência = 10**.
6. Coloque **Primeira cobrança em = 0 min**.
7. Confirme.

A primeira cobrança deverá ocorrer rapidamente. Se o compromisso permanecer aberto, novas cobranças acontecerão e ficarão progressivamente mais firmes.

### Testar a prorrogação única

1. Abra **Compromissos > Gerenciar compromissos**.
2. Selecione o compromisso.
3. Clique em **Adiar 5 min uma vez**.

Esse botão só pode ser usado uma vez para o mesmo compromisso.

Depois, volte ao gerenciamento e marque **Marcar como concluído**. As cobranças devem cessar imediatamente.

Os compromissos persistem em:

```text
data\directives.json
```

## 20. Testar uma regra permanente

Uma regra permanente observa continuamente o título e o processo da janela ativa.

1. Clique com o botão direito no personagem.
2. Abra **Regras permanentes > Adicionar regra**.
3. Em **Regra**, escreva:

```text
Não ficar no YouTube quando quero manter foco
```

4. Em **Padrões**, escreva:

```text
youtube
```

5. Para teste, use **Intervalo mínimo entre cobranças = 10 s**.
6. Confirme.
7. Abra uma página do YouTube cujo título da janela contenha a palavra `YouTube`.

A personagem deverá detectar a regra, falar com você e aumentar o contador de flagrantes.

Depois de pelo menos 10 segundos, permaneça ou volte a uma janela do YouTube. A nova ocorrência deverá produzir uma mensagem mais firme.

### Conferir o contador

1. Abra **Regras permanentes > Gerenciar regras**.
2. Selecione a regra.
3. Observe o campo **Flagrantes**.

Você também pode:

- desativar a regra sem apagá-la;
- reativá-la;
- removê-la.

As regras ficam em:

```text
data\standing_rules.json
```

### Relação com a sessão de estudo

Se uma regra permanente for acionada enquanto uma sessão estiver ativa, aquela janela também será contabilizada como distração, mesmo que ela não esteja em `distraction_keywords`.

Isso permite criar regras pessoais sem editar manualmente o classificador global.
