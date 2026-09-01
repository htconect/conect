# HUMIAT Conect — Versão 1.0.19

## Cobranças InfinitePay abertas
- A tela do atendente mostra as cobranças InfinitePay do contrato com valor, tipo, status, pedido e data.
- Uma cobrança aberta pode ser cancelada no Conect para liberar imediatamente uma nova escolha de sinal/valor total/saldo.
- O registro não é apagado fisicamente: fica preservado para auditoria e para aceitar webhook tardio de um pagamento real.
- Cobranças ainda abertas expiram localmente após 24 horas por padrão (configurável por `INFINITEPAY_CHECKOUT_TTL_HOURS`).
- Depois que um pagamento é confirmado, outras cobranças ainda abertas do mesmo contrato deixam de ser reutilizadas.
- A API pública documentada do Checkout InfinitePay não expõe endpoint de exclusão/expiração do checkout; portanto o Conect encerra o vínculo local, mas não promete revogar uma URL antiga na InfinitePay.

## WhatsApp / contrato final
- O link permanente usado no aceite passa a aparecer em destaque como **PAGAMENTO E ACOMPANHAMENTO**.
- Esse mesmo link continua levando o cliente ao estado atual da reserva e ao próximo pagamento quando houver saldo.
- O link separado de cláusulas foi removido da mensagem final do contrato, pois as cláusulas já ficam dentro do link permanente.
- Ao final da mensagem permanece apenas o link do **Contrato em PDF**, separado do link de pagamento/acompanhamento.

## Commit sugerido
`v1.0.19 - libera nova cobrança InfinitePay e destaca link permanente no contrato`
