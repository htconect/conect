# HUMIAT Conect — Versão 1.0.36

## Correção do cálculo do valor do contrato

- Corrigido o salvamento dos equipamentos/serviços no contrato.
- O valor total agora é calculado a partir dos novos itens gravados na própria requisição.
- Evita o uso da coleção antiga de `ReservaItem` que permanecia carregada na sessão SQLAlchemy após a regravação dos itens.
- Corrige o cenário em que **Total**, **Falta / valor a pagar** e a base da cobrança InfinitePay ficavam em **R$ 0,00** mesmo com itens com valor preenchido.
- A rotina de inicialização existente continua corrigindo contratos legados cujo total possa ter ficado zerado, desde que os itens tenham `valor_total` preenchido.

`v1.0.36 - corrige calculo do valor total e saldo do contrato`
