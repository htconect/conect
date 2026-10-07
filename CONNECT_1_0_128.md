# Connect 1.0.128

## Relatórios — Evolução de vendas

- Adiciona o novo relatório **Relatórios → Evolução de vendas**.
- Compara três anos em visão trimestral: JAN/FEV/MAR, ABR/MAI/JUN, JUL/AGO/SET e OUT/NOV/DEZ.
- Mostra por ano e trimestre:
  - quantidade de vendas;
  - faturamento;
  - ticket médio;
  - saldo a receber informado pelo Organiza;
  - crescimento anual.
- O gráfico pode alternar entre **Quantidade** e **Faturamento**.
- Exibe destaques do ano: melhor trimestre, média trimestral, ticket e quantidade de vendas identificadas no Organiza.

## Integração Organiza

- O relatório lê os registros já sincronizados na tabela `lancamentos_organiza` com `tipo=venda`.
- Títulos/parcelas que pertencem à mesma venda são consolidados antes da contagem, evitando contar uma venda várias vezes.
- A consolidação reconhece o padrão histórico de integração `VENDA-<id>-<parcela/titulo>` e também o número da venda na descrição quando disponível.
- O relatório é somente leitura sobre os dados automáticos do Organiza; não altera lançamentos financeiros nem pagamentos.

## Histórico anterior

- Inclui tabela `evolucao_vendas_historico` para informar períodos antigos que não estejam disponíveis no Organiza.
- Dados automáticos do Organiza têm prioridade sobre qualquer histórico manual do mesmo trimestre.

## Organização dos relatórios

- A antiga "Evolução financeira" passa a ser identificada como **Evolução de aluguéis** dentro da aba Relatórios.
- O botão de retorno da evolução de aluguéis agora volta para **Relatórios**.
