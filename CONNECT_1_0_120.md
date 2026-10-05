# Connect 1.0.120 — filtros, performance, vitrine e link direto

- Restaura os filtros históricos da tela Contratos e reservas: busca, período, Ativos, Em crédito e Cancelados.
- A Agenda abre a mesma tela de Contratos já filtrada por data, sem esconder a barra de filtros.
- Corrige o N+1 da listagem de contratos com carregamento em lote de cliente, produto, itens e pagamentos.
- Otimiza a vitrine pública para evitar consultas repetidas por produto/opcional e reduz consultas no cálculo de recursos.
- Move a configuração de Fluxo da vitrine para Empresa > Vitrine.
- Remove o seletor Modelo visual (Clássico/Moderno/Divertido), mantendo uma única apresentação.
- Padroniza os botões de envio/ajuste/prompt de imagens no cadastro da empresa.
- Corrige a tela Diagnóstico de performance: menos registros por página, tabela responsiva, coluna inicial fixa e sem monitorar assets/mídias/o próprio diagnóstico.
- Resume o log de performance no Render para evitar linhas gigantes.
- Cria um link padrão direto da vitrine por empresa. Ele força Reserva direta sem alterar a regra da vitrine pública e funciona mesmo quando a vitrine pública está desativada.
- No link direto, o cliente segue pelo fluxo existente: vitrine > cadastro > aceite > pagamento.
- Ao digitar um WhatsApp já cadastrado, a vitrine identifica que existe cadastro. Por segurança, CPF/CNPJ é solicitado antes de carregar CEP e número salvos; o telefone sozinho nunca devolve endereço.
- Mantém o catálogo livre para consulta; WhatsApp/CEP/número continuam obrigatórios apenas ao adicionar item ao pedido.
