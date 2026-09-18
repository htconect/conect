# HUMIAT Conect — Versão 1.0.35

## Otimização de performance do estoque e do painel

- Eliminado o padrão N+1 na análise de Produto/Serviço e Recursos.
- Painel, Agenda e Operação agora carregam produtos, recursos, ajustes e reservas em lote.
- A pendência **Item / Produto / Serviço** continua funcionando, mas sem recalcular o mesmo estoque contrato por contrato.
- Adicionados índices de apoio para solicitações, agenda, clientes, produtos, itens da reserva e recursos.
- Adicionada medição específica `home.pendencias_estoque` no monitor de performance.
- Não altera regras de estoque, quantidades, contratos ou recursos cadastrados.

`v1.0.35 - otimiza consultas de estoque no painel agenda e operacao`
