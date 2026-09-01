# Fluxo de trabalho para a entrega do desafio

## 0) Visão geral da tarefa

Este repositório é um desafio de engenharia de software focado em idempotência e concorrência. O objetivo é corrigir um serviço Python que aplica créditos em contas a partir de eventos enviados por um provedor externo.

A regra principal é: o mesmo evento não pode gerar crédito duas vezes, nem em sequência, nem após reinício, nem quando vários workers ou threads tentam processá-lo ao mesmo tempo.

A entrega deve seguir os requisitos declarados em [README.md](../README.md), [AVALIACAO.md](../AVALIACAO.md) e o template de PR em [.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md).

---

## 1) Configuração inicial do ambiente

### 1.1 Verificar estrutura do projeto

Antes de qualquer modificação, confirmar que os arquivos essenciais existem:

- [README.md](../README.md)
- [ledger.py](../ledger.py)
- [cli.py](../cli.py)
- [requirements.txt](../requirements.txt)
- [tests/test_ledger.py](tests/test_ledger.py)
- [tests/conftest.py](tests/conftest.py)
- [AVALIACAO.md](../AVALIACAO.md)

### 1.2 Criar ambiente virtual

No terminal, dentro da pasta do projeto:

```bash
cd /home/bfelipef/Pipefy/young-guns-2026
python3 -m venv .venv
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
cd C:\caminho\para\young-guns-2026
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 1.3 Instalar dependências

Este projeto exige apenas pytest:

```bash
pip install -r requirements.txt
```

Verificar a instalação:

```bash
python -V
pip show pytest
```

### 1.4 Rodar os testes iniciais

Antes de corrigir, confirmar o estado atual do projeto:

```bash
pytest
```

Se o ambiente estiver configurado corretamente, os testes já devem falhar no ponto esperado, reproduzindo o problema real do desafio.

### 1.5 Comandos básicos para o projeto

Executar a CLI manualmente:

```bash
python cli.py evt-abc123 acc-42 1000
```

Saída esperada:

```text
Evento evt-abc123: aplicado
Saldo de acc-42: 1000 centavos
```

Ver o saldo por conta usando o código Python:

```bash
python - <<'PY'
from ledger import CreditLedger
ledger = CreditLedger('ledger.db')
print(ledger.apply_credit('evt-1', 'acc-1', 1000))
print(ledger.balance('acc-1'))
PY
```

Limpar o banco local quando necessário:

```bash
rm -f ledger.db
```

Se houver necessidade de remover também arquivos temporários do ambiente:

```bash
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
```

---

## 2) Revisão dos arquivos do projeto

### `README.md`

É a fonte oficial do comportamento esperado. Ele define os 7 itens principais de comportamento que precisam ser atendidos: idempotência, reboot, concorrência, múltiplas instâncias, validação, soma de eventos distintos e isolamento de testes.

### `AVALIACAO.md`

Descreve como a entrega será avaliada. A parte importante é que a correção precisa funcionar além dos testes visíveis, incluindo casos escondidos de concorrência e múltiplos workers usando o mesmo banco.

### `ledger.py`

Arquivo central da lógica:

- `CreditLedger` representa a interface de persistência do crédito
- `apply_credit()` deve aplicar um crédito apenas uma vez por `event_id`
- `balance()` deve consultar o saldo da conta
- `InvalidCreditError` deve sinalizar entrada inválida
- o schema do SQLite precisa ser suficiente para garantir a deduplicação de verdade

### `cli.py`

É a interface de execução via terminal. O comando deve continuar funcionando da mesma forma, respondendo com mensagem de evento aplicado ou ignorado.

### `tests/test_ledger.py`

Contém os testes existentes. Esses testes servem como base para entender o comportamento esperado atual e o que precisa ser preservado.

### `tests/conftest.py`

Cria um banco isolado por teste. Isso é relevante porque cada teste deve ter o seu próprio arquivo SQLite e não compartilhar estado.

### `.github/PULL_REQUEST_TEMPLATE.md`

Define o formato do PR e quais informações devem estar presentes na entrega final.

---

## 3) Entendimento do problema em termos de negócio

O provedor externo dá eventos com este formato:

```python
event_id = "evt-abc123"
account_id = "acc-42"
amount_cents = 1000
```

O risco é que o mesmo evento pode chegar mais de uma vez por diversas razões:

- retry após timeout
- reinicialização do serviço
- execuções simultâneas em threads
- múltiplas instâncias acessando o mesmo banco

### Requisitos de negócio

- mesmos `event_id` não podem duplicar crédito
- saldo de conta deve refletir apenas uma aplicação por evento
- eventos diferentes devem somar corretamente
- entradas inválidas devem ser rejeitadas sem alterar saldo
- deduplicação deve sobreviver a reinício do processo
- solução deve funcionar no mesmo banco SQLite com múltiplos acessos concorrentes

---

## 4) Processo recomendado de implementação

### Etapa A — reproduzir a falha

1. Ler o README e a avaliação para entender o contrato completo.
2. Rodar `pytest` para observar o estado inicial.
3. Confirmar que o problema principal é a deduplicação em memória.
4. Entender que a correção precisa estar no banco e não apenas em Python.

### Etapa B — escrever testes de regressão antes da correção

Adicionar pelo menos 2 testes novos, sendo que um deles precisa cobrir concorrência.

#### Teste 1: validação de input

Cobrir:

- `event_id` vazio
- `account_id` vazio
- `amount_cents <= 0`

Garantir:

- `InvalidCreditError` é levantada
- saldo da conta não muda
- evento inválido não fica gravado
- o mesmo `event_id` pode ser reutilizado em um evento válido depois

#### Teste 2: concorrência para o mesmo evento

Cobrir:

- múltiplas threads invocando o mesmo `event_id`
- apenas um crédito deve ser aplicado
- saldo final deve refletir apenas uma aplicação

Este teste precisa falhar no código original para ser válido.

### Etapa C — corrigir a camada de persistência

O ajuste principal deve estar em [ledger.py](../ledger.py).

O que a correção precisa fazer:

- persistir eventos processados no SQLite
- usar unicidade em nível de banco para `event_id`
- garantir que duas threads ou processos não apliquem o mesmo evento duas vezes
- separar validação de entrada da persistência
- manter a lógica de saldo por conta

A deduplicação não pode depender apenas de um `set` em memória, porque isso é perdido em reinício.

### Etapa D — manter o comportamento correto

Depois da correção, confirmar:

- eventos distintos somam corretamente
- o mesmo `event_id` nunca duplica saldo
- contas diferentes continuam independentes
- conta inexistente continua retornando 0
- CLI continua funcionando sem alterar a interface pública

---

## 4.1) Alterações reais aplicadas no projeto

Durante a execução do desafio, foram feitas as mudanças abaixo para atender ao contrato do README e ao comportamento esperado do sistema.

### 4.1.1 Ajuste do schema do SQLite

No arquivo [ledger.py](../ledger.py), a tabela `applied_events` foi alterada para usar `event_id` como chave primária.

Isso foi essencial para que o banco guardasse a identidade do evento de forma persistente, sobrevivendo a reinícios e a múltiplas instâncias do mesmo processo.

Antes:

```sql
CREATE TABLE IF NOT EXISTS applied_events (
    event_id     TEXT    NOT NULL,
    account_id   TEXT    NOT NULL,
    amount_cents INTEGER NOT NULL
);
```

Depois:

```sql
CREATE TABLE IF NOT EXISTS applied_events (
    event_id     TEXT    PRIMARY KEY,
    account_id   TEXT    NOT NULL,
    amount_cents INTEGER NOT NULL
);
```

### 4.1.2 Validação de entrada do crédito

Foi adicionada a rotina `_validate_credit()` em [ledger.py](../ledger.py).

Ela valida:

- `event_id` vazio ou nulo
- `account_id` vazio ou nulo
- `amount_cents` nulo, booleano ou menor ou igual a zero

Se qualquer condição for inválida, é lanzada `InvalidCreditError`.

Essa validação foi crucial para cumprir o item 5 do README, que exige que eventos inválidos não mudem o saldo e não gravem o evento.

### 4.1.3 Idempotência persistente em SQLite

A lógica de `apply_credit()` foi ajustada para verificar primeiro no banco se o `event_id` já existe antes de inserir o crédito.

Se o evento já tiver sido processado:

- retorna `CreditResult(applied=False, ...)`
- preserva o saldo atual
- evita duplicidade mesmo após reinício do processo

Essa mudança resolve a falha de restart e também evita duplicidade em duas instâncias acessando o mesmo banco.

### 4.1.4 Tratamento de concorrência em nível de banco

A operação foi ajustada para usar a persistência do SQLite como fonte de verdade. Em vez de depender apenas de um `set` da memória, a lógica agora consulta e grava no banco.

Isso reduz o risco de duas threads ou workers aplicarem o mesmo evento simultaneamente, porque a exclusividade do `event_id` está garantida na tabela.

### 4.1.5 Proteção contra `IntegrityError`

Quando duas chamadas concorrentes tentam inserir o mesmo `event_id` ao mesmo tempo, o banco pode lançar `sqlite3.IntegrityError`.

Foi incluído tratamento para esse cenário, retornando `applied=False` de forma segura e sem duplicar saldo.

### 4.1.6 Reuso do `event_id` em evento válido depois de rejeição

A validação foi separada da persistência, permitindo que um `event_id` rejeitado por entrada inválida continue sendo reutilizado em um evento válido posteriormente.

Isso cumpre o requisito de que um evento recusado ainda pode ser usado depois, em um caso válido.

---

## 5) Alterações nos testes

Além dos testes já existentes, foram adicionados novos testes em [tests/test_ledger.py](../tests/test_ledger.py) para garantir que a correção realmente cubra os cenários críticos.

### 5.1 Teste de evento inválido

Foi adicionado o teste `test_invalid_credit_raises_and_keeps_balance`.

Ele verifica:

- `event_id` vazio
- `account_id` vazio
- `amount_cents` zero ou negativo
- `InvalidCreditError` é lançado
- saldo permanece sem alteração
- mesmo `event_id` rejeitado pode ser usado em um evento válido depois

### 5.2 Teste de concorrência

Foi adicionado o teste `test_concurrent_duplicate_event_is_applied_only_once`.

Ele cria várias threads que tentam aplicar o mesmo evento ao mesmo tempo. O objetivo é garantir que:

- apenas uma aplicação resulte em `applied=True`
- o saldo final seja exatamente um único crédito
- a lógica funcione sem depender apenas da memória do processo

Esses testes foram importantes porque o README exige que o teste de concorrência falhe antes da correção e passe depois.

---

## 6) Critérios de validação

Antes de concluir, validar todos estes pontos:

- `pytest` passa
- testes antigos continuam intactos
- pelo menos 2 testes novos foram adicionados
- um deles cobre concorrência
- a falha original foi reproduzida antes da correção
- o comportamento funciona mesmo em múltiplas threads
- o comportamento funciona mesmo com instâncias diferentes acessando o mesmo banco
- a CLI continua funcionando com o mesmo contrato esperado

---

## 7) Fluxo de commits e organização da entrega

### Commit 1 — diagnóstico e reprodução do bug

Descreve o problema principal:

- deduplicação apenas em memória
- ausência de controle persistente em SQLite
- risco de concorrência e reinicialização

### Commit 2 — testes de regressão

Adicionar:

- teste de evento inválido
- teste de concorrência

### Commit 3 — correção principal

Implementar a lógica de deduplicação segura e persistente no SQLite.

### Commit 4 — validação final e preparação do PR

- rodar `pytest`
- revisar diff
- confirmar checklist do PR
- preparar link do vídeo

---

## 8) Checklist de entrega final

### Código

- [ ] `ledger.py` resolve a idempotência persistente
- [ ] `apply_credit()` rejeita entradas inválidas com `InvalidCreditError`
- [ ] saldo não muda quando o evento é inválido
- [ ] deduplicação funciona após reinício do processo
- [ ] concorrência para o mesmo `event_id` não duplica o crédito
- [ ] múltiplas instâncias no mesmo banco não duplicam o crédito

### Testes

- [ ] testes existentes não foram alterados na asserção
- [ ] pelo menos 2 testes novos foram adicionados
- [ ] um teste novo cobre concorrência
- [ ] houve evidência da falha antes da correção

### PR e documentação

- [ ] branch criada no padrão `fix/<nome>`
- [ ] commits claros e pequenos
- [ ] PR preenchido conforme template
- [ ] vídeo incluído no PR
- [ ] uso de IA declarado no PR

---

## 9) Sequência final recomendada

1. ler [README.md](../README.md) e [AVALIACAO.md](../AVALIACAO.md)
2. criar o ambiente virtual e instalar as dependências
3. rodar `pytest` para reproduzir a falha atual
4. escrever os testes novos de regressão
5. implementar a correção na persistência SQLite
6. validar com `pytest`
7. revisar o diff e ajustar os commits
8. preparar o PR e o link do vídeo

---

## 10) Comandos úteis para a rotina do projeto

### Ambiente

```bash
cd /home/bfelipef/Pipefy/young-guns-2026
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Testes

```bash
pytest
pytest -q
```

### Execução manual do CLI

```bash
python cli.py evt-abc123 acc-42 1000
```

### Limpeza do banco

```bash
rm -f ledger.db
```

### Verificação do saldo em Python

```bash
python - <<'PY'
from ledger import CreditLedger
ledger = CreditLedger('ledger.db')
print(ledger.apply_credit('evt-1', 'acc-1', 1000))
print(ledger.balance('acc-1'))
PY
```

### Revisão geral do projeto antes do PR

```bash
git status
git diff --stat
```

Esses comandos devem ser usados como fluxo inicial de setup e validação para garantir que a entrega seja feita de forma correta, organizada e com evidência de funcionamento.

Antes de concluir, validar todos estes pontos:

- `pytest` passa
- testes antigos continuam intactos
- pelo menos 2 testes novos foram adicionados
- um deles cobre concorrência
- a falha original foi reproduzida antes da correção
- o comportamento funciona mesmo em múltiplas threads
- o comportamento funciona mesmo com instâncias diferentes acessando o mesmo banco
- a CLI continua funcionando com o mesmo contrato esperado

---

## 6) Fluxo de commits e organização da entrega

### Commit 1 — diagnóstico e reprodução do bug

Descreve o problema principal:

- deduplicação apenas em memória
- ausência de controle persistente em SQLite
- risco de concorrência e reinicialização

### Commit 2 — testes de regressão

Adicionar:

- teste de evento inválido
- teste de concorrência

### Commit 3 — correção principal

Implementar a lógica de deduplicação segura e persistente no SQLite.

### Commit 4 — validação final e preparação do PR

- rodar `pytest`
- revisar diff
- confirmar checklist do PR
- preparar link do vídeo

---

## 7) Checklist de entrega final

### Código

- [ ] `ledger.py` resolve a idempotência persistente
- [ ] `apply_credit()` rejeita entradas inválidas com `InvalidCreditError`
- [ ] saldo não muda quando o evento é inválido
- [ ] deduplicação funciona após reinício do processo
- [ ] concorrência para o mesmo `event_id` não duplica o crédito
- [ ] múltiplas instâncias no mesmo banco não duplicam o crédito

### Testes

- [ ] testes existentes não foram alterados na asserção
- [ ] pelo menos 2 testes novos foram adicionados
- [ ] um teste novo cobre concorrência
- [ ] houve evidência da falha antes da correção

### PR e documentação

- [ ] branch criada no padrão `fix/<nome>`
- [ ] commits claros e pequenos
- [ ] PR preenchido conforme template
- [ ] vídeo incluído no PR
- [ ] uso de IA declarado no PR

---

## 8) Sequência final recomendada

1. ler [README.md](../README.md) e [AVALIACAO.md](../AVALIACAO.md)
2. criar o ambiente virtual e instalar as dependências
3. rodar `pytest` para reproduzir a falha atual
4. escrever os testes novos de regressão
5. implementar a correção na persistência SQLite
6. validar com `pytest`
7. revisar o diff e ajustar os commits
8. preparar o PR e o link do vídeo

---

## 9) Comandos úteis para a rotina do projeto

### Ambiente

```bash
cd /home/bfelipef/Pipefy/young-guns-2026
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Testes

```bash
pytest
pytest -q
```

### Execução manual do CLI

```bash
python cli.py evt-abc123 acc-42 1000
```

### Limpeza do banco

```bash
rm -f ledger.db
```

### Verificação do saldo em Python

```bash
python - <<'PY'
from ledger import CreditLedger
ledger = CreditLedger('ledger.db')
print(ledger.apply_credit('evt-1', 'acc-1', 1000))
print(ledger.balance('acc-1'))
PY
```

### Revisão geral do projeto antes do PR

```bash
git status
git diff --stat
```

Esses comandos devem ser usados como fluxo inicial de setup e validação para garantir que a entrega seja feita de forma correta, organizada e com evidência de funcionamento.
