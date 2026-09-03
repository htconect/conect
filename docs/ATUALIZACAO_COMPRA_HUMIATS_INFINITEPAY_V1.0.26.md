# Atualização v1.0.26 — Compra de Humiats via InfinitePay

A carteira Humiat passa a permitir compra automática de créditos por qualquer empresa. A cobrança usa a conexão InfinitePay da HUMIAT, não a configuração InfinitePay da empresa compradora.

## Pacotes

- 5 Humiats — R$ 35,00 (R$ 7,00/H)
- 10 Humiats — R$ 65,00 (R$ 6,50/H)
- 25 Humiats — R$ 150,00 (R$ 6,00/H)
- 50 Humiats — R$ 275,00 (R$ 5,50/H)
- 100 Humiats — R$ 500,00 (R$ 5,00/H)

## Identificação InfinitePay

Cada item é enviado como `HUMIAT - <empresa> - <quantidade> Humiats`, com `order_nsu` iniciado por `HUMIAT-`.

## Retorno exclusivo

A compra usa `/humiats/pagamento-retorno`, isolada do retorno de contratos. O webhook continua único, mas identifica se o `order_nsu` pertence a uma compra de Humiats ou a um contrato.

## Crédito

O crédito é idempotente. Webhook e retorno podem chegar em qualquer ordem sem duplicar Humiats.
