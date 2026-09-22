# v1.0.49 — Financeiro: filtro de datas, semana automática e títulos sem banco

## Regras

1. O mês/ano superior continua sendo o período mestre.
2. Data inicial e final só podem ficar dentro desse mês.
3. A receber e A pagar respeitam exatamente essas duas datas.
4. Ao trocar o mês, a semana é escolhida automaticamente: semana atual no mês corrente ou primeira semana válida nos demais meses.
5. A receber e A pagar manuais não recebem `conta_id`; a conta surge somente quando uma baixa real é vinculada.
6. Movimentos reais continuam exigindo banco.
7. O cálculo acumulado dos bancos não foi alterado.
