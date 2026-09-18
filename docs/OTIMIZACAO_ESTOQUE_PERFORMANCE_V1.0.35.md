# Otimização de estoque — v1.0.35

O monitor mostrou 196 consultas SQL em `/painel`, com repetição das tabelas `solicitacoes`, `reserva_itens`, `produtos_servicos_recursos`, `solicitacoes_recursos`, `itens_produto_servico_estoque` e `produtos_servicos`.

A rotina de análise de estoque passou a operar em lote: carrega as reservas das datas envolvidas, itens, produtos, vínculos de recursos, ajustes por contrato e estoques uma única vez por empresa e calcula os conflitos em memória.

Também foram adicionados índices idempotentes para as consultas mais frequentes.
