# Atualização — fluxo público v1.0.17

- Corrige `aceite_em` criado automaticamente em rascunhos e remove o default no PostgreSQL.
- O painel administrativo só mostra **Contrato aceito** para estados explicitamente aceitos.
- `aceite_pagamento_pendente` passa a aparecer corretamente como contrato aceito aguardando pagamento.
- O sinal InfinitePay usa o cadastro da empresa antes do aceite e é congelado no contrato no aceite real.
- Corrige contratos legados em que o sinal havia ficado igual ao valor total, priorizando o sinal válido da empresa.
- PIX esconde a simulação de parcelas; Cartão exibe a simulação.
- A descrição enviada à InfinitePay inclui contrato, tipo de cobrança, cliente, data do evento e empresa.
