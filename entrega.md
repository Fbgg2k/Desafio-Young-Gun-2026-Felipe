# Roteiro de apresentação em vídeo

## Duração estimada: 3 a 5 minutos

Olá. Neste vídeo vou apresentar a correção do desafio de aplicação de créditos sem duplicidade, explicar os problemas encontrados, mostrar como a solução funciona, apresentar os testes realizados e comentar o uso de inteligência artificial durante o desenvolvimento.

## 1. Problema encontrado e como foi identificado

O projeto recebe eventos de pagamento com três informações: `event_id`, que identifica o evento, `account_id`, que identifica a conta beneficiada, e `amount_cents`, que representa o valor em centavos.

O provedor garante que o `event_id` é estável, mas não garante que o evento será entregue apenas uma vez. Por exemplo, um evento de 1000 centavos pode ser reenviado depois de um timeout, depois de um reinício do serviço ou pode chegar ao mesmo tempo em duas threads diferentes.

O problema principal estava em `ledger.py`. O código original usava um conjunto em memória para controlar os eventos processados. Essa abordagem falha porque o conjunto é perdido quando o processo reinicia e também não é compartilhado entre instâncias diferentes do `CreditLedger`.

Além disso, a tabela `applied_events` não garantia que `event_id` fosse único, a aplicação não validava corretamente os dados de entrada e não havia proteção suficiente para o caso de duas chamadas concorrentes.

Esses problemas foram identificados lendo o README, executando os testes existentes e adicionando testes para os comportamentos que ainda não estavam cobertos. O teste de restart já mostrava que o mesmo evento era aplicado novamente. Os novos testes também falharam no código original: o teste de validação não recebia `InvalidCreditError` e o teste de concorrência permitia várias aplicações do mesmo evento.

## 2. O que deveria ser feito

A solução precisava garantir que cada `event_id` válido fosse aplicado somente uma vez, independentemente de reinício, concorrência ou múltiplas instâncias usando o mesmo arquivo SQLite.

Também precisava rejeitar `event_id` ou `account_id` vazios e valores de `amount_cents` menores ou iguais a zero, sem alterar o saldo e sem gravar o evento inválido.

Ao mesmo tempo, eventos diferentes deveriam continuar somando normalmente e a interface pública do projeto não poderia mudar.

## 3. Correção implementada

A primeira mudança foi no schema do SQLite. A coluna `event_id` da tabela `applied_events` passou a ser chave primária. Assim, o banco passa a garantir a unicidade do evento de forma persistente.

Depois, foi criada a validação `_validate_credit()`. Ela verifica os campos antes de qualquer operação no banco. Quando os dados são inválidos, `InvalidCreditError` é levantada e nenhuma alteração é feita no saldo ou na tabela de eventos.

A função `apply_credit()` agora consulta o banco para identificar eventos já processados. Se encontrar o `event_id`, retorna `applied=False` e mantém o saldo atual. Se o evento ainda não existir, ele é inserido e o saldo é atualizado na mesma transação.

Também foi tratado `sqlite3.IntegrityError`. Se duas chamadas tentarem inserir o mesmo evento simultaneamente, o banco aceita apenas uma por causa da chave primária. A outra chamada é tratada como duplicada e retorna `applied=False`.

A API continua igual. Ainda é possível criar `CreditLedger`, chamar `apply_credit()`, consultar `result.applied`, consultar `result.balance_cents`, usar `balance()` e capturar `InvalidCreditError`.

## 4. Como a concorrência foi testada

O teste `test_concurrent_duplicate_event_is_applied_only_once`, em `tests/test_ledger.py`, cria oito threads. Todas usam uma barreira para começar praticamente ao mesmo tempo e tentam aplicar o mesmo evento, `evt-shared`, na mesma conta.

O teste verifica duas coisas: exatamente uma chamada deve retornar `applied=True` e o saldo final deve ser 100 centavos, e não 800 centavos.

A importância desse teste é que ele reproduz o risco financeiro descrito no desafio. A aplicação não pode depender apenas de uma variável local; a garantia precisa existir no banco SQLite, que é compartilhado pelas chamadas.

## 5. Como a solução foi provada

Foram adicionados dois testes novos.

O primeiro, `test_invalid_credit_raises_and_keeps_balance`, testa `event_id` vazio, `account_id` vazio e valores zero ou negativos. Ele confirma que `InvalidCreditError` é levantada, que o saldo permanece igual e que um evento válido continua podendo ser processado depois.

O segundo é o teste de concorrência descrito anteriormente.

Os testes novos foram escritos e executados antes da correção. Eles falharam no código original. Depois da implementação, a suíte foi executada novamente com:

```bash
pytest -q
```

O resultado final foi:

```text
8 passed
```

Também foi executado o teste de concorrência isoladamente:

```bash
pytest -q tests/test_ledger.py -k concurrent
```

Esse teste passou depois da correção. Portanto, o ciclo apresentado foi: teste vermelho no código original, implementação da solução e teste verde após a correção.

## 6. Uso de inteligência artificial

Usei o GitHub Copilot como apoio para analisar o código, entender a causa raiz, organizar os testes e revisar a estratégia de persistência e concorrência.

A sugestão aceita foi usar o SQLite como fonte persistente da deduplicação, transformar `event_id` em identificador único, validar as entradas antes da transação e tratar a violação de unicidade durante concorrência.

A abordagem descartada foi manter a deduplicação apenas em um conjunto em memória ou usar somente uma proteção local em Python. Essa alternativa não resolveria o reinício do processo e não funcionaria corretamente entre instâncias diferentes usando o mesmo banco.

A inteligência artificial foi usada como apoio. A decisão final foi baseada nos requisitos do README, na leitura do código e nos resultados dos testes.

## 7. O que eu faria diferente com mais tempo

Com mais tempo, eu adicionaria um teste específico usando duas instâncias independentes de `CreditLedger` apontando para o mesmo arquivo SQLite e processando o mesmo evento simultaneamente. Esse cenário corresponde diretamente ao requisito de múltiplos workers em produção.

Também avaliaria uma estratégia de transação mais explícita, como iniciar a transação com aquisição imediata de escrita, para tornar o comportamento de lock do SQLite ainda mais previsível sob alta concorrência.

## Encerramento

Em resumo, a correção tornou a deduplicação persistente, validou os dados de entrada e protegeu o crédito contra duplicidade em concorrência, mantendo a API original. A suíte final passou com oito testes, incluindo os dois novos testes de regressão exigidos pelo desafio.

Obrigado.
