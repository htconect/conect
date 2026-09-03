# HUMIAT Conect — Versão 1.0.26

## Compra automática de Humiats pela InfinitePay

- Pacotes: 5 H = R$ 35,00; 10 H = R$ 65,00; 25 H = R$ 150,00; 50 H = R$ 275,00; 100 H = R$ 500,00.
- Todas as empresas compram pela conta InfinitePay da HUMIAT, independentemente da InfinitePay usada nos próprios contratos.
- A descrição enviada à InfinitePay identifica a empresa compradora e a quantidade de Humiats.
- Webhook credita os Humiats automaticamente e de forma idempotente.
- O retorno da compra é separado do retorno de pagamentos de contratos: `/humiats/pagamento-retorno`.
- Se houver contratos aguardando saldo, os créditos recém-comprados quitam as pendências automaticamente.
- Checkout recente do mesmo pacote é reutilizado para reduzir risco de cobrança duplicada.

## Commit sugerido

`v1.0.26 - compra Humiats pela InfinitePay com retorno exclusivo e credito automatico`
