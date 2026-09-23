# v1.0.51 — Vínculos parciais e múltiplos no Financeiro

- Um único movimento de banco/manual pode ser rateado entre várias vendas ou manutenções do Organiza.
- Exemplo validado: entrada de R$ 300,00 vinculada a duas manutenções de R$ 150,00 cada.
- Permite baixa parcial quando o saldo do movimento é menor que o saldo do lançamento do Organiza.
- Um lançamento do Organiza parcialmente baixado continua disponível apenas pelo saldo restante.
- O popup usa seleção múltipla por checkbox e mostra o saldo disponível de cada lançamento.
- Cada vínculo pode ser removido individualmente.
- Vínculos antigos 1:1 permanecem compatíveis.
- Movimentos com rateio do Organiza não podem ser misturados com aluguel, título manual ou repasse sem antes desvincular.
- Não altera cálculo bancário, InfinitePay, contratos, A receber/A pagar ou relatórios.
