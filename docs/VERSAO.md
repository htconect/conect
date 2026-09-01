# HUMIAT Conect — Versão 1.0.10

## Retorno InfinitePay, endereço do contrato e reenvio do contrato

- Corrigida a colisão da rota `/pagamento/retorno` com `/pagamento/{solicitacao_id}` que gerava `int_parsing` com `solicitacao_id = retorno`.
- Novos checkouts usam a rota segura `/pagamento-retorno`.
- A rota antiga continua aceita e agora é registrada antes da rota dinâmica para compatibilidade com cobranças já criadas.
- O retorno aceita `transaction_nsu` e também `transaction_id` como compatibilidade.
- O checkout InfinitePay recebe o endereço congelado do contrato: CEP, logradouro, bairro, número e complemento.
- Após o pagamento confirmado, o WhatsApp continua abrindo automaticamente e o botão manual **Enviar contrato pelo WhatsApp** fica sempre visível para nova tentativa.
- Na tela interna da solicitação, a área Pagamento ganhou a ação **Enviar contrato** para reenvio manual.

Commit:

`v1.0.10 - corrige retorno InfinitePay e adiciona reenvio do contrato`
