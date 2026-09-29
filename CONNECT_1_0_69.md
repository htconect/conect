# Connect 1.0.69

## Financeiro: categorias em lote
- Lançamentos bancários continuam com categoria individual, mas agora podem ser alterados em várias linhas e salvos com um único botão **Salvar categorias**.
- Lançamentos já vinculados que não podem mudar de categoria são preservados e informados como bloqueados.

## Relatório mensal por categoria
- Novo resumo mensal por categoria no Financeiro.
- Exibe quantidade de lançamentos, **Entrou**, **Saiu** e **Saldo**.
- O mesmo resumo passa a integrar os relatórios Excel e PDF mensais.

## Datas locais
- Datas operacionais e financeiras passam a usar a data civil do Rio de Janeiro (UTC-3), evitando virar o dia antes da hora no servidor.
- Lançamento manual e registro manual de pagamento abrem com a data local correta.

## Pagamentos sem duplicidade
- Cada registro manual recebe um código idempotente único.
- Dois envios do mesmo formulário/código não criam dois pagamentos.
- Pagamentos InfinitePay usam o `transaction_nsu` como chave de idempotência.

## InfinitePay: valor efetivamente pago
- O Connect preserva o valor esperado da cobrança (`amount`) para validação.
- Para registrar o pagamento, utiliza o valor efetivamente informado pela InfinitePay, limitado ao valor esperado da cobrança. Assim acréscimos/taxas não aumentam o valor do contrato e pagamentos menores não quitam indevidamente o saldo.
- Pagamentos legados já vinculados à InfinitePay são corrigidos no startup quando o valor pago armazenado na cobrança é menor que o valor registrado no contrato.
- Movimento financeiro espelhado acompanha a correção do pagamento.
