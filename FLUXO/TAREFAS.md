# Fluxo de trabalho para a entrega do desafio

## 1) Entendimento do problema

Este desafio trata de um sistema de crédito que recebe eventos de pagamento com:

- `event_id`: identificador estável do evento
- `account_id`: conta que receberá o crédito
- `amount_cents`: valor em centavos

O risco principal é a entrega não única do mesmo evento. O mesmo `event_id` pode chegar:

- duas vezes em sequência
- depois de reinicialização do serviço
- em paralelo em múltiplas threads
- em múltiplas instâncias do mesmo processo usando o mesmo banco SQLite

A regra central é simples: o mesmo evento não pode creditar duas vezes. O sistema precisa ser idempotente e ainda permitir que eventos diferentes somem corretamente.

### Requisitos que precisam ser atendidos

- idempotência por `event_id`
- persistência da deduplicação mesmo após reinício
- concorrência segura com threads e múltiplos processos
- validação de entrada para eventos inválidos
- saldo por conta deve refletir apenas créditos válidos
- testes isolados por banco por teste

---

## 2) Arquivos que precisam ser revisados

### `README.md`

É a fonte oficial do comportamento esperado. Ele define o contrato do serviço e os 7 itens críticos de comportamento.

### `ledger.py`

É o coração da solução:

- `CreditLedger`
- `apply_credit()`
- `balance()`
- `InvalidCreditError`
- schema SQLite e transações

### `cli.py`

Valida a interação via terminal e mostra como o sistema deve se comportar na prática.

### `tests/test_ledger.py`

Contém os testes existentes que mostram o comportamento esperado básico.

### `tests/conftest.py`

Define a fixture que cria um banco isolado por teste.

### `AVALIACAO.md`

Explica que os testes escondidos também validam casos de concorrência, restart e múltiplas instâncias. Isso mostra que a correção precisa ser real e não apenas para os testes visíveis.

### `.github/PULL_REQUEST_TEMPLATE.md`

Define o formato do PR e os itens que precisam constar na entrega.

---

## 3) Processo recomendado para a implementação

### Etapa A — reproduzir a falha

1. Rodar `pytest` para confirmar o estado atual.
2. Ler o README e garantir que os requisitos estão claros.
3. Identificar a causa raiz do problema:
   - `event_id` não é persistido como identificador único
   - deduplicação está só em memória
   - concorrência não é tratada em nível de banco
   - entradas inválidas não são rejeitadas

### Etapa B — escrever testes que provem o bug real

Adicionar pelo menos 2 testes novos, incluindo um de concorrência.

#### Teste 1: rejeição de evento inválido

Cobrir:
- `event_id` vazio
- `account_id` vazio
- `amount_cents <= 0`

Garantir que:
- `InvalidCreditError` é levantada
- saldo não muda
- evento não é gravado
- o mesmo `event_id` pode ser usado depois em um evento válido

#### Teste 2: concorrência para o mesmo evento

Cobrir:
- múltiplas threads executando `apply_credit()` no mesmo `event_id`
- apenas um deve aplicar o crédito
- saldo final deve refletir exatamente uma vez

Esse teste precisa falhar antes da correção e passar depois.

### Etapa C — corrigir a camada de persistência

O ajuste principal deve estar em `ledger.py`.

Ideias esperadas para a solução correta:

- persistir `event_id` em tabela de eventos processados
- garantir unicidade no banco para `event_id`
- usar transação com controle de concorrência
- verificar existência do evento antes de registrar crédito
- tratar duplicatas mesmo quando duas instâncias acessam o mesmo arquivo SQLite ao mesmo tempo

A correção precisa ser feita em nível de banco para funcionar corretamente também em múltiplos processos e múltiplas threads.

### Etapa D — manter a regra de negócio correta

Ao ajustar a lógica, garantir que:

- eventos distintos somem corretamente
- o mesmo evento não pode dobrar saldo
- apenas contas válidas são atualizadas
- saldo inicial de conta inexistente continua em 0

---

## 4) Critérios de validação

Antes de finalizar, validar tudo isso:

- `pytest` roda sem falhas
- os testes já existentes continuam intactos
- pelo menos 2 testes novos foram adicionados
- um deles cobre concorrência
- o bug original foi provado pela falha antes da correção
- a solução funciona com múltiplas threads e instâncias do mesmo banco
- CLI continua funcionando com o mesmo contrato esperado

---

## 5) Fluxo de commits e entrega

### Commit 1 — diagnóstico e reprodução

Descrever:
- o problema de idempotência em memória
- o risco de concorrência e reinício
- a necessidade de persistir e validar no banco

### Commit 2 — testes de regressão

Adicionar:
- teste de evento inválido
- teste de concorrência

### Commit 3 — correção principal

Implementar a lógica de deduplicação segura no SQLite.

### Commit 4 — validação final e PR

- confirmar `pytest`
- revisar diff
- preparar resumo para o PR
- registrar link do vídeo

---

## 6) Checklist de entrega

### Código

- [ ] `ledger.py` corrige idempotência persistente
- [ ] `apply_credit()` rejeita eventos inválidos com `InvalidCreditError`
- [ ] saldo não muda em caso de evento inválido
- [ ] deduplicação funciona mesmo após reinício
- [ ] concorrência para o mesmo `event_id` não duplica crédito
- [ ] instâncias diferentes no mesmo banco também não duplicam

### Testes

- [ ] testes existentes intactos
- [ ] ao menos 2 testes novos adicionados
- [ ] um teste novo cobre concorrência
- [ ] um teste falha no código original e passa depois da correção

### PR e documentação

- [ ] branch criada no padrão `fix/<nome>`
- [ ] commits claros e pequenos
- [ ] PR preenchido conforme template
- [ ] vídeo com link incluído
- [ ] menciona uso de IA e decisão de aceitar/descartar sugestões

---

## 7) Sequência final recomendada

1. ler o contrato completo no README e no `AVALIACAO.md`
2. rodar pytest e confirmar falhas atuais
3. escrever testes de regressão
4. corrigir a lógica de deduplicação no banco
5. validar com pytest
6. revisar diff e preparar PR
7. gravar vídeo explicando problema, solução e prova
8. enviar PR com link do vídeo

Este é o caminho mais seguro para entregar a solução de forma correta, com entendimento real do problema e sem perder a parte de organização exigida pela avaliação.
