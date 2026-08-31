# InfinitePay no HUMIAT Conect — v1.0.3

## Fluxo automático
1. Responsável envia o contrato para aceite ao cliente pelo fluxo normal do Conect.
2. O primeiro usuário que faz esse envio fica fixado como responsável do contrato, com seu WhatsApp.
3. Cliente aceita o contrato.
4. Se a empresa estiver com InfinitePay ativa, o contrato muda para `aceite_pagamento_pendente` e ainda não é aprovado.
5. Cliente escolhe apenas **Sinal** ou **Valor integral**.
6. Conect mostra a simulação de parcelas usando a tabela InfinitePay da empresa.
7. Conect cria o checkout e redireciona para a InfinitePay.
8. Webhook/`payment_check` confirma o pagamento e valida o valor esperado.
9. Conect cria o pagamento, lança o recebimento na conta **InfinitePay**, vincula e concilia automaticamente.
10. Contrato é aprovado e os eventos operacionais são criados.
11. No retorno do checkout, a tela informa: **Pagamento autorizado. Estou preparando seu contrato para envio. Na próxima tela, basta clicar em Enviar.**
12. O navegador abre automaticamente o WhatsApp do responsável do contrato com a mensagem e o link do contrato prontos. Não há botão intermediário obrigatório no Conect.

## Regra multiempresa
- `empresa.infinitepay_ativa` define se a empresa usa ou não o fluxo.
- `empresa.infinitepay_handle` define a InfiniteTag/handle da empresa.
- Taxas são armazenadas por `empresa_id`.
- Cobranças, pagamentos e lançamentos financeiros são sempre vinculados ao `empresa_id` do contrato.
- Empresas com InfinitePay desativada continuam exatamente no processo manual.

## Responsável do contrato
- O Conect já possui telefone em `usuarios_empresa.telefone`.
- Ao primeiro envio para aceite, o sistema grava no contrato `responsavel_contrato` e `responsavel_contrato_telefone`.
- Esse telefone é usado no retorno do pagamento para abrir o WhatsApp correto para o cliente.
