# Desafio Young Gun — Aplicar crédito sem duplicar

Este repositório faz parte do processo seletivo. Você vai trabalhar em um serviço Python que **aplica créditos em contas** a partir de eventos enviados por um provedor de pagamentos.

**Pode usar AI** (ChatGPT, Copilot, Cursor, etc.). O que importa é você entender o que mudou, conseguir explicar no vídeo e entregar um PR organizado.

Tempo estimado: **2 a 3 horas**.

## O contexto

O provedor externo envia eventos assim:

```
event_id = "evt-abc123"   # identificador estável do evento
account_id = "acc-42"     # conta que recebe o crédito
amount_cents = 1000       # R$ 10 em centavos
```

O provedor garante que o `event_id` é estável, mas **não** garante entrega única. O mesmo evento pode chegar:

- duas vezes seguidas (retry depois de um timeout)
- depois que o serviço reiniciou (redeploy, crash)
- **duas vezes ao mesmo tempo**, em threads diferentes

Em nenhum desses casos o cliente pode receber o crédito em dobro. Dinheiro a mais na conta errada é um incidente, não um detalhe.

O saldo fica em um arquivo SQLite (`ledger.db`). O módulo `sqlite3` já vem com o Python — não é preciso instalar nem subir nenhum servidor.

```bash
python cli.py evt-abc123 acc-42 1000
```

Saída:

```
Evento evt-abc123: aplicado
Saldo de acc-42: 1000 centavos
```

## Comportamento esperado

Leia com atenção — o código atual **não** cumpre tudo isso.

1. **Idempotência.** Aplicar o mesmo `event_id` de novo devolve `applied=False` e deixa o saldo como está.
2. **Idempotência no restart.** Se o processo cair e subir de novo, um `event_id` já aplicado ainda é tratado como duplicado.
3. **Concorrência.** Se o mesmo `event_id` chegar em duas ou mais threads ao mesmo tempo, o crédito é aplicado **uma única vez**.
4. **Várias instâncias, mesmo banco.** Em produção o serviço roda em mais de um worker usando o **mesmo** `ledger.db`. Duas instâncias de `CreditLedger` apontando para o mesmo arquivo, recebendo o mesmo evento ao mesmo tempo, também creditam **uma única vez**.
5. **Validação de input.** Evento inválido levanta `InvalidCreditError` (já definida em `ledger.py`), **não** muda o saldo e **não** grava o evento. Um `event_id` recusado ainda pode ser usado depois, num evento válido. São inválidos: `event_id` ou `account_id` vazios, e `amount_cents` menor ou igual a zero.
6. **Eventos diferentes somam.** A correção não pode bloquear demais: dois `event_id` distintos, mesmo em paralelo, geram dois créditos.
7. **Testes isolados.** Cada teste usa o próprio arquivo de banco — a fixture `database_path` já faz isso.

Você pode mudar o schema do banco. Se mudar, apague o `ledger.db` local antes de rodar o CLI de novo.

### Duas restrições importantes

**Não mude o jeito de chamar o código.** Você pode reescrever o que quiser por dentro, mas estas funções e atributos precisam continuar funcionando:

```python
ledger = CreditLedger(database_path)              # caminho do arquivo SQLite
result = ledger.apply_credit(event_id, account_id, amount_cents)
result.applied        # bool
result.balance_cents  # int
ledger.balance(account_id)                        # int
InvalidCreditError                                # exceção de validação
```

**Vamos rodar testes que você não vê.** Além dos testes deste repositório, sua solução passa por testes extras que chamam as funções acima e checam os 7 itens de comportamento esperado. Não escreva código só para o teste vermelho — cubra o que está descrito aqui.

## O que você precisa entregar

Repositório: https://github.com/pipe-challenge/young-guns-2026

1. **Fazer um fork** deste repositório (botão *Fork* no GitHub) e **clonar o seu fork**
2. **Criar uma branch** a partir de `main` — use o padrão `fix/<seu-primeiro-nome>`
3. **Corrigir o código** para cumprir o comportamento esperado
4. **Fazer os testes existentes passarem** — não apague nem altere as asserções dos testes que já estão no repositório; você pode **adicionar** testes novos
5. **Escrever pelo menos 2 testes novos**, sendo que um deles precisa cobrir **concorrência** (item 3 acima). O módulo `threading` já vem com o Python.
6. **Fazer commits** claros (vários commits pequenos > um commit gigante "fix all")
7. **Abrir um Pull Request** do seu fork para `pipe-challenge/young-guns-2026`, branch `main`
8. **Gravar um vídeo curto** (3 a 5 minutos) e **colar o link na descrição do PR**

Não envie o arquivo de vídeo no GitHub. Use Loom, YouTube (não listado) ou Google Drive com acesso liberado.

### Dica importante sobre o teste de concorrência

Esse teste só vale se ele **falha no código original**. Antes de corrigir, escreva o teste e veja ele falhar — depois corrija e veja passar. Se o teste passa nos dois casos, ele não está testando nada.

Mostrar esses dois momentos no vídeo conta muito a seu favor.

### O que o vídeo precisa cobrir

- Quais problemas você encontrou e **como** encontrou
- Por que a sua correção funciona (principalmente a de concorrência)
- Como você provou que funciona
- Se usou AI: o que ela sugeriu, o que você aceitou e o que você descartou
- Uma coisa que você faria diferente com mais tempo

## Setup

Python **3.11+**. Sem dependências externas além do pytest.

```bash
git clone https://github.com/<seu-usuario>/young-guns-2026.git
cd young-guns-2026
git checkout -b fix/<seu-primeiro-nome>

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

No estado atual do repositório, `pytest` **não passa**. Isso é proposital.

## Regras

- Pode usar AI. Conte no PR quais ferramentas usou e no que elas ajudaram.
- Não altere as asserções dos testes existentes.
- Não adicione dependências novas sem justificar no PR.
- Mantenha a solução simples. Não estamos pedindo para reorganizar o projeto.
- Commits em português ou inglês, desde que descrevam **por quê**, não só "fix".
- O PR precisa do link do vídeo para ser considerado completo.

## O que vamos avaliar

O detalhe está em [`AVALIACAO.md`](AVALIACAO.md). Em resumo: o teste vermelho é o começo, não o fim; os testes novos precisam falhar no código original; e o vídeo precisa mostrar que você entendeu a correção — inclusive se usou AI.

Boa sorte.
