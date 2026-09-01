# Atualização — fluxo público v1.0.16

Pente-fino nas telas que o cliente utiliza pelo celular, com foco em confirmação de pagamento, quitação, fechamento de aba e consistência visual dos botões.

A confirmação do primeiro pagamento continua ligada à efetivação da reserva e ao envio do contrato. Pagamentos posteriores não repetem esse processo: quando o saldo chega a zero, a tela informa apenas que o contrato está quitado e agradece o pagamento.

Todas as ações **Fechar** das telas públicas usam a mesma rotina. O navegador continua sendo respeitado: a rotina tenta fechar somente a aba atual e, se o navegador bloquear, mostra orientação para o cliente fechá-la manualmente.
