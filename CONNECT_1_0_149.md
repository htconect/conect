# Connect 1.0.149 — Otimização de consultas PostgreSQL

Base: Connect 1.0.148. Sem alteração de esquema de banco e sem mudança de regras de contrato, estoque, desconto, opcionais ou pagamento.

## Alterações

- Duração de produtos por tipo de evento calculada em lote, sem uma consulta de ProdutoPrecoEvento por produto/tipo. Consulta apenas os tipos da empresa e preços dos produtos em lote, mantendo a regra de somar horas adicionais quando `horas_modo = adicionar`.
- Preços do contrato reutilizam os tipos de evento já carregados na mesma sessão HTTP.
- Vitrine reutiliza, dentro da requisição, as categorias e o bloqueio da data, evitando consultas idênticas.
- Comprometimento de estoque reutiliza o mapa de recursos e reservas da data fornecidos pelo chamador, evitando repetir consultas; quando empresa desativa estoque, a API de produto não consulta recursos.
- InfinitePay: leitura das taxas em uma única consulta, gerando somente parcelas padrão que ainda não existem. Taxas customizadas e inativas permanecem preservadas.
- Contrato público: reutiliza os itens carregados para o template sem disparar segundo SELECT para a mesma relação. Não altera o conteúdo do contrato.

## Evidências

- Relatório 08/10: `/painel/solicitacao/184/editar-completo`: 40 SELECT, dos quais 22 em `produto_precos_evento`, cerca de 5,36 s total.
- Teste local de 16 equipamentos com ambos os tipos: 41 consultas na função original, 2 consultas na função em lote, com resultado idêntico.
- Outros testes SQLite: preço, categorias, bloqueios, taxas InfinitePay, estoque sem módulo e comprometimento pré-carregado.
- Não foi feita medição de tempo em produção nesta versão. O banco remoto apresenta ~115 ms por SELECT mesmo em consultas simples; validar localização/região e reutilização de conexões.

## Reavaliação pós-deploy

1. Limpar o monitor em `/admin/performance/limpar` com a sessão administrativa apropriada, se disponível.
2. Abrir editar contrato, contrato público, vitrine e consulta de estoque nas mesmas condições.
3. Coletar `/admin/performance/dados` e comparar `sql_count`, `sql_ms` e `total_ms` com o relatório anterior.
4. Verificar se Render e o banco PostgreSQL/Neon estão na mesma região (sem mudar credenciais nem migrar dados automaticamente).
