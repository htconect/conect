# Connect 1.0.130

## Evolução de vendas integrada ao Organiza

- Novo endpoint `POST /api/integracoes/organiza/evolucao-vendas` para receber do Organiza o consolidado trimestral de um ano.
- A sincronização atualiza somente o relatório de evolução de vendas e não cria títulos a receber nem movimentações financeiras.
- O ano é substituído pelos quatro trimestres enviados pelo Organiza, inclusive trimestres zerados.
- Dados sincronizados pelo Organiza passam a ter prioridade sobre lançamentos antigos/fragmentados do mesmo período.
- O histórico manual continua disponível para anos antigos não sincronizados.
