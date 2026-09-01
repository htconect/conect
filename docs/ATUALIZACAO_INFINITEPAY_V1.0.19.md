# InfinitePay / WhatsApp — v1.0.19

- Cancelamento local de checkout aberto sem apagar histórico.
- Expiração automática local após 24h, configurável por `INFINITEPAY_CHECKOUT_TTL_HOURS`.
- Liberação de nova cobrança no mesmo link permanente da reserva.
- Fechamento local de outras cobranças abertas após confirmação de pagamento.
- Link permanente destacado na mensagem final; cláusulas deixam de ser enviadas como link separado; PDF permanece no final.

Observação: a documentação pública do Checkout InfinitePay consultada na implementação documenta criação (`POST /links`), verificação (`POST /payment_check`) e webhook, mas não endpoint para excluir ou expirar um checkout não pago.
