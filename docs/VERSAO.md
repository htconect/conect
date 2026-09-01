# HUMIAT Conect — Versão 1.0.17

## Correção de estado de aceite e primeiro pagamento

- O painel administrativo não usa mais um `else` genérico para declarar **Contrato aceito**. Somente estados explicitamente aceitos recebem esse rótulo.
- O estado `aceite_pagamento_pendente` aparece como **Contrato aceito — aguardando pagamento**.
- Rascunho e aguardando aceite nunca exibem ações de contrato final.
- Corrigido o campo `aceite_em`, que em bases anteriores podia receber data automaticamente ao criar o rascunho. O PostgreSQL perde esse `DEFAULT` e rascunhos/contratos aguardando aceite têm o timestamp limpo.
- O primeiro pagamento InfinitePay volta a priorizar o **sinal configurado na empresa**. Contratos legados em que o sinal ficou igual ao total deixam de esconder a opção de sinal quando existe um sinal válido menor configurado.
- Após qualquer pagamento, permanece somente o saldo restante.
- Ao selecionar **PIX**, a simulação de parcelas fica escondida. Ao selecionar **Cartão**, a simulação aparece.
- O item enviado à InfinitePay agora identifica melhor a venda com **contrato, tipo de cobrança, nome do cliente, data do evento e empresa**.
- A proteção de cobrança pendente continua ativa para evitar duas cobranças simultâneas.

## Fluxos preservados

- Empresa com InfinitePay: aceite → sinal/total → checkout → primeiro pagamento → contrato → saldo → quitação.
- Empresa sem InfinitePay: aceite → PIX da empresa.
- O mesmo link continua atendendo aceite, pagamento, saldo e consulta final.

Commit sugerido:

`v1.0.17 - corrige estados de aceite, sinal InfinitePay e identificação da cobrança`
