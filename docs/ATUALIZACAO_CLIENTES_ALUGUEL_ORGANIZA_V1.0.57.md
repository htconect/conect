# Connect 1.0.57 — Clientes de Aluguel no Organiza

- Contratos confirmados atualizam automaticamente a Lista de Clientes de Aluguel do Organiza.
- Envia nome, telefone, data do evento, cliente_id e solicitacao_id.
- Alterações posteriores em nome, telefone ou data de um contrato confirmado também disparam nova sincronização.
- A chamada é assíncrona e não bloqueia o fluxo do contrato.
- Usa ORGANIZA_API_KEY e, opcionalmente, ORGANIZA_CLIENTES_ALUGUEL_URL.
