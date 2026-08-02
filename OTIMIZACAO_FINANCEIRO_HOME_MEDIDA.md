# Otimização medida — Home e Financeiro

## Base do diagnóstico

O monitor mostrou que o tempo era dominado pela quantidade de viagens ao Neon, e não por uma única consulta lenta.

## Home

- Reaplicada a versão agregada da Home.
- Contagens de solicitações, operação e cadastros são consolidadas.
- Relacionamentos necessários são carregados antecipadamente.

## Financeiro

- Cliente e solicitação são carregados junto com contratos e pagamentos.
- Pagamento e Organiza vinculados aos lançamentos são carregados antecipadamente.
- Vínculos de repasse carregam cliente e empresa transferida em lote.
- Saldos anuais de todas as contas são calculados em duas consultas agrupadas, em vez de duas consultas por conta.
- Uma única consulta mensal de contratos alimenta cards, relatório semanal e semana selecionada.
- Registros e vínculos do Organiza são carregados uma única vez e reutilizados.

## Validação após deploy

1. Limpar o painel de performance.
2. Abrir `/painel` uma vez.
3. Abrir `/painel/financeiro` uma vez.
4. Comparar `sql_count`, `sql_ms`, `total_ms` e `sql_groups`.

Metas iniciais:

- Home: cerca de 11 consultas ou menos.
- Financeiro: redução expressiva das 48 consultas, idealmente para menos de 20 nesta etapa.
