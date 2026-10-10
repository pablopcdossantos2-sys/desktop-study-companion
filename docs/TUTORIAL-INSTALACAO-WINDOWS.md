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

Quando a aplicação iniciar, deverá aparecer a personagem 3D Sendagaya Shino em uma janela transparente, com o balão de fala acima dela. Se o renderer 3D falhar, o programa usa temporariamente um ícone de livro como fallback.

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

A voz é fornecida pelo SAPI do Windows. Agora você também pode escolher a voz instalada em **Configurações > Voz**, além de ajustar velocidade e volume.

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


## 21. Testar intervenções no desktop com segurança

As intervenções são **desativadas por padrão**. Faça o primeiro teste somente com minimizar.

### 21.1 Habilitar apenas minimizar

1. Inicie a aplicação.
2. Clique com o botão direito no personagem.
3. Abra **Intervenções no desktop > Configurar permissões**.
4. Marque:
   - **Permitir intervenções no desktop**;
   - **Permitir minimizar janelas**.
5. Deixe **Permitir fechar janela/aba** desmarcado.
6. Salve.

### 21.2 Criar uma regra de teste

1. Abra **Regras permanentes > Adicionar regra**.
2. Em **Regra**, escreva:

```text
Minimizar o YouTube durante o teste
```

3. Em **Padrões**, escreva:

```text
youtube
```

4. Em **Resposta**, escolha **Minimizar e cobrar**.
5. Use um cooldown de 10 segundos.
6. Confirme.
7. Abra uma aba do YouTube.

O comportamento esperado é:

```text
YouTube detectado
→ Standing Rule registra o flagrante
→ janela do navegador é minimizada
→ personagem reclama
→ ação fica registrada no SQLite
```

### 21.3 Testar a trava de permissão

Sem alterar a mesma regra:

1. abra **Intervenções no desktop > Configurar permissões**;
2. desmarque **Permitir minimizar janelas**;
3. salve;
4. volte ao YouTube depois do cooldown.

A personagem deverá reclamar, mas a janela **não** deverá ser minimizada.

Isso confirma que a ação da regra e a permissão global são independentes.

## 22. Testar fechamento de aba

Faça este teste somente depois que o teste de minimizar estiver funcionando.

1. Em **Intervenções no desktop > Configurar permissões**, habilite:
   - **Permitir intervenções no desktop**;
   - **Permitir fechar janela/aba**.
2. Crie uma nova Standing Rule para `youtube`.
3. Em **Resposta**, escolha **Fechar e cobrar**.
4. Abra o navegador com pelo menos duas abas.
5. Deixe uma aba do YouTube ativa.

Em Chrome, Edge, Firefox, Brave, Opera e Vivaldi, a aplicação tenta usar `Ctrl+W` para fechar **somente a aba ativa**, em vez de encerrar o navegador inteiro.

Use uma aba sem conteúdo importante nesse teste.

## 23. Testar o botão de emergência

Com intervenções habilitadas:

1. clique com o botão direito no personagem;
2. abra **Intervenções no desktop**;
3. clique em **DESATIVAR INTERVENÇÕES AGORA**.

A personagem deverá informar que não minimizará nem fechará outras janelas.

Depois disso, mesmo uma regra configurada como **Fechar e cobrar** deverá apenas reclamar.

O arquivo:

```text
data\intervention_permissions.json
```

deverá mostrar as permissões desligadas.

## 24. Processos protegidos

O sistema possui uma camada de proteção que não pode ser removida pela configuração comum.

Entre os processos críticos estão:

```text
explorer.exe
taskmgr.exe
powershell.exe
pwsh.exe
cmd.exe
conhost.exe
python.exe
pythonw.exe
```

Você pode acrescentar outros processos à lista de proteção.

Se uma regra coincidir com um processo protegido, a personagem pode reclamar, mas a ação de minimizar/fechar é recusada.

## 25. O que enviar se uma intervenção falhar

Se a regra for detectada, mas a janela não minimizar/fechar, informe:

1. qual navegador/programa estava aberto;
2. o texto completo do título da janela;
3. qual resposta a Standing Rule estava usando;
4. quais permissões estavam habilitadas;
5. se apareceu alguma mensagem de erro no PowerShell.

Não é necessário enviar o banco `companion.db`.


## 26. Testar a escalada automática da sessão

Faça este teste primeiro **somente com minimizar**.

### 26.1 Preparar tempos curtos

Feche a aplicação e abra:

```text
config\default.json
```

Para o teste, use:

```json
"gentle_after_seconds": 5,
"firm_after_seconds": 10,
"direct_after_seconds": 15,
"insistent_after_seconds": 20
```

Salve e reinicie.

### 26.2 Autorizar a escalada

1. Abra **Intervenções no desktop > Configurar permissões**.
2. Marque:
   - **Permitir intervenções no desktop**;
   - **Permitir minimizar janelas**;
   - **Permitir escalada automática durante sessão de estudo**.
3. Deixe **Permitir fechar janela/aba** desmarcado.
4. Deixe o lockdown desmarcado neste primeiro teste.
5. Salve.

### 26.3 Executar

1. Inicie uma sessão de estudo.
2. Abra uma janela classificada como distração, por exemplo YouTube.
3. Permaneça nela.

Com os tempos de teste:

```text
5 s  → fala
10 s → fala mais firme
15 s → a janela pode ser minimizada
20 s → continua usando a ação máxima autorizada
```

Se minimizar funcionar, o encadeamento básico está validado.

## 27. Testar escalada até fechamento

Somente depois do teste anterior:

1. habilite **Permitir fechar janela/aba**;
2. mantenha **Permitir escalada automática durante sessão de estudo** ligado;
3. use uma aba descartável do navegador;
4. inicie uma sessão;
5. abra o YouTube e permaneça nele até o nível máximo.

No nível máximo, o navegador deve tentar fechar apenas a aba ativa.

Se fechar estiver desativado, a aplicação não pode ultrapassar a ação de minimizar.

## 28. Testar o lockdown limitado

O lockdown só pode ser ativado se estas opções estiverem habilitadas:

- **Permitir intervenções no desktop**;
- **Permitir escalada automática durante sessão de estudo**;
- **Permitir modo de foco limitado (lockdown)**;
- pelo menos uma ação entre minimizar/fechar.

Para um teste seguro:

1. habilite apenas **minimizar**;
2. habilite escalada automática;
3. habilite lockdown;
4. configure **Duração do lockdown = 2 min**;
5. mantenha os limites de 5/10/15/20 segundos;
6. inicie uma sessão;
7. permaneça em uma distração até atingir a severidade máxima.

A personagem deverá informar que o modo de foco limitado foi ativado.

Durante os dois minutos seguintes:

- abra outra distração;
- ela deverá ser minimizada rapidamente, sem esperar novamente os 15 segundos;
- aplicativos produtivos devem continuar funcionando normalmente.

### Encerrar antes do tempo

Clique:

```text
Intervenções no desktop
→ Encerrar lockdown atual
```

A personagem deverá confirmar o encerramento.

### Testar emergência

Ative o lockdown novamente e clique:

```text
Intervenções no desktop
→ DESATIVAR INTERVENÇÕES AGORA
```

Isso deve:

- encerrar o lockdown;
- desativar minimizar;
- desativar fechar;
- desativar escalada automática;
- desativar permissão de lockdown.

As Standing Rules e sessões continuam existindo, mas voltam a apenas cobrar verbalmente.

## 29. Restaurar os tempos normais

Depois dos testes, restaure:

```json
"gentle_after_seconds": 60,
"firm_after_seconds": 180,
"direct_after_seconds": 300,
"insistent_after_seconds": 600
```

Assim a aplicação não ficará excessivamente agressiva no uso diário.


## 30. Opção mais simples: versão portátil sem instalar Python

A partir da v0.1.0-dev6, o GitHub Actions gera automaticamente uma versão portátil para Windows.

Essa opção é recomendada para o primeiro teste porque não exige:

- instalar Python;
- criar ambiente virtual;
- usar `pip`;
- executar comandos no PowerShell.

### Como baixar

1. Abra o repositório no GitHub.
2. Clique na aba **Actions**.
3. Abra a execução mais recente chamada:

```text
build-windows-portable
```

4. Role a página até **Artifacts**.
5. Baixe:

```text
DesktopStudyCompanion-Windows-Portable
```

6. O GitHub baixará um arquivo ZIP.
7. Extraia o ZIP para uma pasta normal, por exemplo:

```text
C:\Users\SEU_USUARIO\Documents\Programas\DesktopStudyCompanion
```

8. Entre na pasta extraída.
9. Execute:

```text
DesktopStudyCompanion.exe
```

### Importante

Não execute o programa diretamente de dentro do ZIP. Extraia todo o conteúdo primeiro.

A pasta portátil contém o executável e arquivos auxiliares necessários.

Os seus dados serão criados em:

```text
data\
```

dentro da própria pasta da versão portátil.

Isso facilita copiar a instalação inteira para outro local e também torna claro onde o histórico está armazenado.

## 31. Configurar pela própria interface

Não é mais necessário editar `config/default.json` para as configurações principais.

1. Clique com o botão direito no personagem.
2. Escolha **Configurações**.

A janela possui sete áreas: Atividade, Cobrança, Personalidade, Voz, Microfone, Cérebro e Avatar.

### Atividade

Permite editar, uma palavra-chave por linha:

- aplicativos/contextos produtivos;
- neutros;
- distrações.

### Cobrança

Permite editar:

- tempo até lembrete gentil;
- tempo até cobrança firme;
- tempo até cobrança direta;
- tempo até cobrança insistente;
- cooldown.

Os tempos de severidade devem permanecer em ordem crescente.

### Personalidade

Permite alterar:

- nome;
- calor humano;
- sarcasmo;
- rigor;
- paciência;
- humor;
- iniciativa.

### Voz

Permite:

- ligar/desligar TTS;
- escolher uma voz SAPI instalada no Windows;
- alterar velocidade;
- alterar volume.

### Microfone

Permite:

- ativar/desativar push-to-talk local;
- escolher modelo Whisper;
- definir idioma;
- escolher CPU/auto/CUDA;
- escolher o microfone;
- definir o tempo máximo de gravação;
- decidir se a transcrição é enviada automaticamente.

### Cérebro

Permite:

- ativar/desativar conversa com LLM;
- configurar endpoint OpenAI-compatible;
- escolher modelo;
- definir variável de ambiente da chave;
- controlar temperatura, tokens, timeout e histórico enviado.

### Avatar

Permite:

- ligar/desligar o avatar VRM;
- alterar largura e altura da janela;
- ligar/desligar o olhar que acompanha o cursor;
- ligar/desligar a animação da boca durante a fala.

As alterações são salvas em `config/default.json` e aplicadas à sessão em execução sem precisar reiniciar a aplicação.

## 32. Consultar histórico e insights

Depois que você tiver realizado algumas sessões:

1. clique com o botão direito no personagem;
2. abra **Histórico e dados**;
3. clique em **Histórico e insights**.

A aba **Resumo** mostra indicadores dos últimos 30 dias.

A aba **Sessões** mostra até 100 registros recentes com:

- horário;
- objetivo;
- estado;
- duração planejada;
- foco;
- distração;
- percentual de foco.

Com poucas sessões, alguns indicadores ficam indisponíveis de propósito para evitar conclusões frágeis.

## 33. Exportar dados para CSV

Abra:

```text
Histórico e dados
→ Exportar CSV
```

Escolha uma pasta.

Serão criados:

```text
study_sessions.csv
activity_events.csv
interventions.csv
conversation_messages.csv
```

Esses arquivos podem ser abertos no Excel, LibreOffice Calc ou importados no Google Sheets.

## 34. Criar um backup

Abra:

```text
Histórico e dados
→ Criar backup ZIP
```

Escolha onde salvar.

O ZIP inclui:

- banco SQLite;
- compromissos;
- rotinas;
- regras permanentes;
- permissões de intervenção;
- configuração principal;
- metadados da versão.

O banco é copiado usando o mecanismo de backup do SQLite, evitando snapshots incompletos mesmo com a aplicação aberta.

## 35. Qual forma de instalação devo usar?

Para testar a aplicação:

**Use primeiro a versão portátil.**

Use `INICIAR-DEV.bat` apenas se você quiser:

- desenvolver o projeto;
- alterar código-fonte;
- rodar testes;
- experimentar mudanças ainda não empacotadas.

A meta futura continua sendo disponibilizar um instalador Windows convencional, mas a versão portátil já remove a necessidade de terminal para o uso comum.


## 36. Se o arquivo portátil tiver expirado

Os artefatos automáticos do GitHub não são binários permanentes do repositório.

A configuração atual mantém a build por até **90 dias**.

Se você abrir o projeto depois disso e o artefato não estiver mais disponível:

1. abra a aba **Actions**;
2. na lateral, escolha **build-windows-portable**;
3. clique em **Run workflow**;
4. confirme **Run workflow** usando a branch `main`;
5. quando a execução terminar com um indicador verde, abra a execução;
6. em **Artifacts**, baixe **DesktopStudyCompanion-Windows-Portable**.

O GitHub recompilará a versão atual da `main`, executará os testes antes do empacotamento e publicará um novo ZIP portátil.


## 37. Testar o avatar VRM 1.0

A versão atual usa **Sendagaya Shino** como personagem 3D.

Na versão portátil, o arquivo VRM e o renderer já vêm incluídos. Não é necessário baixar o modelo manualmente.

Ao abrir `DesktopStudyCompanion.exe`, o esperado é:

1. aparecer a personagem 3D no lugar do antigo ícone de livro;
2. o fundo ao redor dela permanecer transparente;
3. a personagem piscar automaticamente;
4. o olhar acompanhar suavemente a posição do cursor;
5. o balão de fala continuar acima da personagem.

O carregamento inicial do modelo pode levar alguns segundos.

## 38. Testar expressões do avatar

As expressões são ligadas aos estados que já existem no sistema.

Faça estes testes em sequência:

### Iniciar uma sessão

Ao confirmar uma nova sessão, a personagem deve usar uma expressão positiva (`happy`) por alguns segundos e depois retornar a `neutral`.

### Encerrar uma sessão

Ao concluir uma sessão, deve ocorrer novamente uma expressão positiva.

### Cobrança leve

As primeiras cobranças usam expressão neutra ou relaxada.

### Cobrança forte

Cobranças diretas/insistentes usam `angry`.

As expressões temporárias retornam automaticamente para `neutral`, para evitar que a personagem fique permanentemente sorrindo ou irritada.

## 39. Testar fala e boca

Quando a voz estiver habilitada:

1. inicie uma sessão;
2. observe a boca enquanto a personagem fala;
3. provoque uma cobrança curta.

O avatar usa os visemes do próprio VRM:

```text
aa
ih
ou
ee
oh
```

Nesta fase, o movimento da boca acompanha aproximadamente a duração da fala. A sincronização ainda não é baseada nos fonemas reais do áudio SAPI.

## 40. Testar o olhar

Mova o cursor lentamente:

- para a esquerda da personagem;
- para a direita;
- acima;
- abaixo.

O `lookAt` do VRM deverá acompanhar o cursor de forma limitada.

Esse movimento não interfere nos cliques: o renderer do avatar é transparente aos eventos do mouse e o menu continua pertencendo ao widget principal.

## 41. Se aparecer apenas o ícone de livro

O ícone de livro agora é um **fallback de segurança**.

Ele aparece quando:

- o arquivo VRM está ausente;
- o renderer web está ausente;
- Qt WebEngine não consegue iniciar;
- o VRM gera erro durante o carregamento;
- o carregamento excede o limite esperado.

Na versão portátil oficial, os dois primeiros casos não deveriam ocorrer porque o CI verifica a presença de:

```text
avatar\renderer\index.html
assets\avatar\Sendagaya_Shino.vrm
```

Se o livro aparecer, informe:

1. sua versão do Windows;
2. sua placa de vídeo, se souber;
3. se o balão de fala aparece normalmente;
4. se o restante da aplicação funciona;
5. qualquer mensagem mostrada ao iniciar pela versão de desenvolvimento.

## 42. Integridade do modelo

O avatar oficial desta versão possui SHA-256:

```text
fab70124f0025e444a6eef84d6ab3a04e78c0adb626099e54b55287d0f083a47
```

O GitHub Actions verifica:

- hash do arquivo;
- formato glTF binário;
- VRM 1.x;
- esqueleto humanoide;
- presença das expressões usadas pelo aplicativo;
- presença dos visemes usados para fala.

Assim, uma alteração inesperada do arquivo deve fazer a build falhar em vez de produzir silenciosamente um executável incompatível.


## 43. Ativar push-to-talk

A versão dev10 permite conversar falando ao microfone.

O reconhecimento é local e vem **desativado por padrão**.

1. Clique com o botão direito na personagem.
2. Abra **Configurações**.
3. Abra a aba **Microfone**.
4. Marque **Ativar push-to-talk local**.

Para o primeiro teste, mantenha:

```text
Modelo Whisper: base
Idioma: pt
Dispositivo de inferência: cpu
Compute type: int8
Microfone: Microfone padrão do Windows
Máx. gravação: 30 s
Enviar automaticamente: marcado
```

Clique em **Salvar**.

## 44. Primeiro uso do Whisper

A build portátil já contém o mecanismo `faster-whisper`, mas não inclui os pesos do modelo.

Na primeira transcrição, o aplicativo poderá baixar o modelo selecionado.

O modelo fica armazenado em:

```text
data\models\faster-whisper\
```

Esse download acontece apenas quando necessário.

O modelo `base` é recomendado para o primeiro teste.

Se o computador for mais lento, experimente:

```text
tiny
```

Se desejar mais precisão e tiver memória/CPU suficientes, posteriormente experimente:

```text
small
```

## 45. Conversar por voz

O cérebro conversacional deve estar habilitado conforme o tutorial do Ollama.

Depois:

1. clique com o botão direito na personagem;
2. escolha **Conversar**;
3. localize **Segure para falar**;
4. pressione e mantenha o botão;
5. diga uma frase;
6. solte o botão.

Fluxo esperado:

```text
pressionar
→ TTS atual é interrompido
→ microfone começa a gravar
→ soltar
→ áudio é transcrito localmente
→ texto aparece na conversa
→ texto é enviado ao cérebro
→ personagem responde
→ resposta é falada
```

Na primeira tentativa, a etapa de transcrição pode demorar mais devido ao download/carregamento do modelo.

## 46. Revisar a transcrição antes de enviar

Se preferir não enviar automaticamente o que foi reconhecido:

1. abra **Configurações > Microfone**;
2. desmarque **Enviar automaticamente após transcrever**;
3. salve.

Agora:

```text
fala
→ transcrição
→ texto aparece na caixa de entrada
→ você pode corrigir
→ clique em Enviar
```

Esse modo é recomendado durante os primeiros testes de precisão.

## 47. Escolher outro microfone

Abra:

```text
Configurações
→ Microfone
→ Microfone
```

A lista mostra dispositivos de entrada encontrados pelo Windows/PortAudio.

Para evitar problemas no primeiro teste, use:

```text
Microfone padrão do Windows
```

Se o programa estiver usando o dispositivo errado, selecione explicitamente o microfone desejado.

## 48. Selecionar a voz da personagem

Abra:

```text
Configurações
→ Voz
```

Agora existem:

- Ativar voz do Windows;
- Voz;
- Velocidade;
- Volume.

Em **Voz**, você pode escolher uma das vozes SAPI instaladas.

Se escolher **Voz padrão do Windows**, o sistema usa a voz padrão disponível.

## 49. Testar interrupção da fala

1. Faça a personagem produzir uma resposta relativamente longa.
2. Enquanto ela estiver falando, pressione **Segure para falar**.

O comportamento esperado é:

```text
fala da personagem é interrompida
→ microfone começa a gravar
```

Isso reduz a chance de o microfone transcrever a própria personagem.

## 50. Onde o áudio é armazenado

O aplicativo não mantém gravações de voz como histórico.

Durante a transcrição é criado temporariamente:

```text
data\temp\ptt-....wav
```

Depois que a transcrição termina — inclusive em caso de erro — o worker tenta apagar o WAV.

O histórico permanente armazena somente o texto da conversa.

## 51. Se o microfone não funcionar

No Windows, confira:

```text
Configurações
→ Privacidade e segurança
→ Microfone
```

Confirme que o acesso ao microfone para aplicativos de desktop está permitido.

Depois:

1. volte a **Configurações > Microfone**;
2. tente **Microfone padrão do Windows**;
3. salve;
4. abra **Conversar**;
5. faça um teste curto.

Se ainda falhar, envie a mensagem exibida na própria janela de conversa.

## 52. Se a transcrição estiver ruim

Tente, nesta ordem:

1. falar mais perto do microfone;
2. reduzir ruído de fundo;
3. confirmar `Idioma = pt`;
4. mudar de `tiny` para `base`;
5. posteriormente testar `small`.

Não é necessário usar GPU para o teste inicial.

## 53. Privacidade do push-to-talk

O áudio é processado pelo faster-whisper localmente.

O arquivo de áudio não é enviado ao LLM.

Depois da transcrição, somente o **texto** segue para o cérebro conversacional.

Se estiver usando Ollama local, o fluxo completo pode permanecer no computador:

```text
microfone
→ Whisper local
→ texto
→ Ollama local
→ resposta
→ SAPI local
```

Se você configurar um cérebro remoto, apenas a parte textual passa a seguir as regras de privacidade daquele provedor.


## 54. Se o avatar cair no fallback

A partir da dev11, não é mais necessário tentar adivinhar o erro.

Clique com o botão direito na personagem/fallback:

```text
Diagnóstico
→ Abrir pasta de logs
```

Abra:

```text
desktop-study-companion.log
```

Procure nas últimas linhas por:

```text
avatar-ready
avatar-fit
avatar-fatal
Avatar renderer error
WebGL
```

Você também pode usar:

```text
Diagnóstico
→ Copiar resumo do diagnóstico
```

Cole esse resumo junto com as últimas linhas do log ao relatar o problema.

O log fica em:

```text
data\logs\desktop-study-companion.log
```

A dev11 também amplia o tempo de carregamento inicial do avatar para aproximadamente 40 segundos e usa um novo enquadramento que considera largura + altura + margem para evitar mãos ou pés cortados.


## 55. Ajuda e tutoriais dentro do aplicativo

A partir da dev12, clique com o botão direito na personagem e abra:

```text
Ajuda e tutoriais
```

Existem atalhos para:

- Primeiros passos;
- Configurar Cérebro / Ollama;
- Configurar voz e microfone;
- Diagnóstico do avatar.

Quando você tenta usar uma função ainda não configurada, o aplicativo também pode oferecer diretamente os botões **Abrir Configurações** e **Abrir tutorial**.

## 56. Testar a animação natural

Ao iniciar a dev12, observe a personagem por alguns segundos.

O esperado é:

- braços em postura relaxada, não na pose em cruz/T-pose;
- respiração visível;
- pequeno balanço do corpo;
- movimento discreto de cabeça, ombros e mãos;
- piscadas;
- olhar seguindo o cursor;
- movimento um pouco mais expressivo durante a fala.

## 57. Se a personagem sumir e voltar

A dev12 mantém o renderer ativo mesmo quando a janela perde foco e verifica sua saúde periodicamente.

Se ainda ocorrer desaparecimento:

1. abra **Diagnóstico > Abrir pasta de logs**;
2. procure por `renderer unhealthy`, `WebGL`, `context lost` ou `Restarting avatar renderer`;
3. envie essas linhas junto com o resumo do diagnóstico.


## 58. Roteiro de validação da dev14

Para testar a dev14 sem misturar causas diferentes, use esta ordem.

### Etapa A — menu e janelas

1. Clique com o botão direito na personagem.
2. Clique fora do menu sem escolher nada.
3. Confirme que o menu desaparece.
4. Abra novamente o menu.
5. Escolha **Configurações**.
6. Confirme que a janela de Configurações fica totalmente acima da personagem e pode ser clicada livremente.
7. Feche a janela.
8. Repita o clique direito algumas vezes e confirme que não ficam menus antigos acumulados.

### Etapa B — cérebro por texto

Antes do microfone, confirme no PowerShell:

```powershell
ollama --version
ollama list
ollama run qwen3:4b
```

Se estiver usando outro modelo, troque `qwen3:4b` pelo nome exato mostrado por `ollama list`.

No aplicativo:

1. Abra **Configurações > Cérebro**.
2. Habilite o cérebro.
3. Use `http://127.0.0.1:11434/v1`.
4. Informe o nome exato do modelo.
5. Salve.
6. Abra **Conversar**.
7. Digite uma mensagem simples.

A dev14 reconhece automaticamente o Ollama local e usa a API nativa com thinking desativado.

### Etapa C — voz

Somente depois que a Etapa B funcionar:

1. Abra **Configurações > Microfone**.
2. Ative push-to-talk.
3. Use inicialmente CPU + INT8 + modelo `base`.
4. Abra **Conversar**.
5. Segure o botão de microfone, fale e solte.

A dev14 inclui PyAV abaixo da versão 19 para manter compatibilidade com faster-whisper 1.2.1.

### Etapa D — se algo falhar

Abra:

```text
Diagnóstico
→ Abrir pasta de logs
```

Procure por:

```text
Brain request
Brain response
Brain chat worker failed
Starting local transcription
Local transcription failed
STT worker failed
```

O resumo de diagnóstico também informa as versões instaladas de PySide6, faster-whisper e PyAV.
