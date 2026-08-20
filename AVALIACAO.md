# Como a sua entrega vai ser avaliada

Pode usar AI. O que a gente mede não é se você escreveu cada linha na mão — é se a mudança está correta, se você entendeu o que fez, e se consegue explicar.

Não existe uma implementação “certa” que a gente compara linha a linha. Não precisamos de um pattern específico. Olhamos **propriedades** da solução.

## O que importa

1. **O contrato do README.** Os 7 itens de comportamento esperado. O teste que já vem vermelho é só o começo — tem requisito sem teste apontando para ele.
2. **Idempotência de verdade.** O mesmo `event_id` credita uma vez só: em sequência, depois de restart, com duas threads, e com duas instâncias no mesmo arquivo.
3. **Testes que provam.** Um teste novo só vale se ele **falha no código original** e passa depois da correção. Se passa nos dois, não está testando o bug.
4. **Simplicidade.** Diff pequeno que resolve o problema ganha de refatoração que ninguém pediu.
5. **Uso crítico de AI.** Declarar a ferramenta no PR. No vídeo, o que ela sugeriu, o que você aceitou e o que você **descartou**.
6. **Comunicação.** Branch no padrão, commits que explicam o porquê, PR preenchido, vídeo de 3 a 5 minutos.

## O que a gente não está medindo

- Se você decorou SQL, SQLite ou um livro de concorrência
- Se o código “parece de sênior”
- Se você evitou AI
- Se a solução é igual a alguma implementação interna nossa

## Testes que você não vê

Além do `pytest` deste repositório, rodamos testes extras que chamam as mesmas funções e atributos que o README pede para não mudar (`CreditLedger`, `apply_credit`, `balance`, etc.).

Eles cobrem os 7 itens de comportamento esperado — inclusive casos que os testes daqui não exercitam. Escrever código só para deixar o teste vermelho verde não basta.

## Como se preparar para o vídeo

Se você conseguir responder isto com as suas palavras, a entrega está no caminho certo:

- Quais problemas você encontrou, e **como** encontrou (teste, CLI, leitura do README)?
- Por que a correção de concorrência funciona — inclusive se o serviço tiver mais de um processo?
- Como você provou? O teste novo falhou antes de corrigir?
- A AI sugeriu algo que você não usou? Por quê?

Se alguma dessas perguntas você só consegue responder lendo o próprio diff na hora, vale voltar no código antes de gravar.
