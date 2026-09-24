# Connect 1.0.58 — Clientes de Aluguel no Organiza

- Sincronização da lista de aluguel agora é exclusiva da empresa com slug `karaokerj`.
- Empresas Vivioke, Karaoke do Bonito ou qualquer outro slug não enviam clientes para essa lista.
- Novo endpoint autenticado de snapshot em lote para o botão **Atualizar pelo Connect** do Organiza.
- O snapshot retorna um único registro por cliente, sempre usando o contrato válido mais recente da Karaokê RJ.
- A sincronização automática em cada confirmação/alteração continua ativa para manter a lista atualizada depois da carga em lote.
