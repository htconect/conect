# HUMIAT Conect — Versão 1.0.69

## Atualizações
- Categorias bancárias podem ser ajustadas em várias linhas e confirmadas de uma só vez.
- Relatório mensal por categoria com Entrou, Saiu, Saldo e quantidade de lançamentos, também no Excel/PDF.
- Datas financeiras passam a respeitar o fuso local do Rio de Janeiro.
- Registro de pagamento manual ganhou código idempotente para impedir duplicidade por duplo envio.
- InfinitePay evita duplicidade pela transação e registra o valor efetivo recebido sem ultrapassar o valor esperado da cobrança.
- Correção automática de registros InfinitePay legados cujo valor registrado ficou acima do valor efetivamente informado pela cobrança.
