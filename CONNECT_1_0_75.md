# Connect 1.0.75

## Pendências financeiras entre meses

- A Pagar e A Receber passam a carregar saldos anteriores ainda em aberto para o mês selecionado.
- A data original e a competência do título são preservadas; não há duplicação nem alteração automática de vencimento.
- Pendências anteriores são identificadas na tela com o mês/ano de origem.
- Títulos a pagar de mês anterior continuam com o botão **Pagar**.
- Títulos a receber passam a ter o botão **Receber**, com o mesmo fluxo simplificado do pagamento:
  - banco vindo do filtro atual, com combo editável;
  - data real do recebimento;
  - saldo em aberto preenchido automaticamente;
  - suporte a baixa parcial.
- A baixa cria a entrada/saída no mês em que efetivamente ocorreu e mantém o vínculo com o título original.
- Saldos anteriores de contratos, Organiza, repasses internos e repasses a pagar permanecem visíveis até serem liquidados.
