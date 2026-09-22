# HUMIAT Conect — Versão 1.0.39

## Financeiro — posição mensal dinâmica de A receber / A pagar

- **A receber** passa a considerar todos os contratos aprovados até o último dia do mês selecionado, inclusive contratos do próprio mês que ainda não foram entregues/realizados.
- Saldos pendentes de contratos de meses anteriores continuam carregados até serem quitados.
- Contratos de meses futuros não entram antecipadamente na posição do mês selecionado.
- O saldo do contrato é dinâmico: valor do contrato menos tudo que já foi recebido.
- Ao registrar um pagamento, a parte recebida deixa imediatamente de compor **A receber**; o pagamento fica disponível em **Vincular** para conciliação com o movimento bancário.
- Pagamento parcial mantém somente o saldo restante em **A receber** e exibe o valor já recebido.
- Pagamento total retira o contrato de **A receber**.
- O registro do pagamento do contrato não é somado como novo saldo bancário; somente o movimento real do banco compõe **No banco**, evitando duplicidade.
- **A pagar** segue a mesma lógica mensal para títulos manuais e repasses: mês selecionado + saldos anteriores em aberto, sem antecipar meses futuros.
- Relatórios Excel/PDF usam o corte do mês selecionado para a posição financeira.

`v1.0.39 - financeiro mensal dinamico e conciliacao sem duplicidade`
