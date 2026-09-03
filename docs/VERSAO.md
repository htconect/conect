# HUMIAT Conect — Versão 1.0.25

## Alteração principal

- No primeiro pagamento via InfinitePay, a tela do Conect mostra um aviso grande antes de abrir o checkout.
- O aviso orienta o cliente a tocar em **Continuar** na tela da InfinitePay após concluir o pagamento.
- Explica que esse retorno é necessário para o Conect abrir automaticamente o WhatsApp com o contrato pronto para envio.
- O aviso aparece tanto para cobrança nova quanto para cobrança já iniciada, mas somente no primeiro pagamento.
- Pagamento de saldo não recebe esse texto para não sugerir novo envio do contrato.
- O retorno continua passando pelo Conect e redirecionando diretamente ao WhatsApp do responsável, sem botão intermediário.
- Empresas sem InfinitePay permanecem sem alteração.

Commit sugerido:

`v1.0.25 - destaca retorno da InfinitePay e orienta envio automatico do contrato`
