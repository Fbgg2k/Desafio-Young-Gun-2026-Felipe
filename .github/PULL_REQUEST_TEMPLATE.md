## O que foi feito

Encontrei a causa raiz do problema na lógica de deduplicação: o código original usava um `set` em memória para rastrear `event_id`, o que não sobrevive a reinício do processo e não resolve concorrência entre threads ou instâncias diferentes acessando o mesmo SQLite.

Para corrigir isso, houve ajustes do schema no banco em `ledger.py` para tornar `event_id` único e persistente, e passei a validar entradas inválidas antes de aplicar qualquer crédito. Também tratei o caso de `sqlite3.IntegrityError` para garantir que, quando duas chamadas concorrentes tentarem processar o mesmo evento ao mesmo tempo, apenas uma delas aplique o crédito e a outra retorne `applied=False` sem duplicar o saldo.

Além disso, mantivemos a API pública intacta (`CreditLedger`, `apply_credit`, `balance`, `InvalidCreditError`) e preservei o comportamento esperado para eventos diferentes, que continuam somando corretamente.

## Como você provou que funciona

Foram aplicados dois testes novos em `tests/test_ledger.py` antes da correção: um para validação de entrada inválida e outro para concorrência do mesmo `event_id` em múltiplas threads.

A falha real foi reproduzida no código original antes da correção. Depois da correção, executei a suíte localmente com `pytest -q` e ela passou com sucesso.

Evidência final:

- `8 passed in 0.20s`

Esse é o ciclo de prova exigido pelo README: teste falhando no código original, correção implementada e testes verdes após a correção.

## Uso de AI

A AI para diagnosticar a causa raiz do problema e validar a estratégia de correção. A sugestão aceita foi mover a deduplicação para o banco SQLite e tratar a concorrência em nível de persistência, porque a solução em memória era insuficiente para reinício e múltiplas threads.

Para descarte foi manter a deduplicação somente em memória e tentar “blindar” o problema com Python puro sem persistência, porque isso não satisfazia os requisitos de restart, concorrência e múltiplas instâncias usando o mesmo arquivo de banco.

## Checklist

- [x] `pytest` passa localmente
- [x] Adicionei pelo menos 2 testes novos, um deles de concorrência
- [x] Não alterei as asserções dos testes existentes

## Vídeo

<!-- Cole o link (Loom, YouTube não listado, Google Drive). Não anexe o arquivo no PR. -->

- Link: 
