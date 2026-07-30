# Ajuste — previsão e leitura de retiradas pela Inteligência

## O que mudou

- A Inteligência passa a prever a retirada antes da entrega ser concluída.
- A previsão usa primeiro a data/hora da Operação da entrega.
- Para retirada obrigatória, mantém a data/hora definida no contrato.
- Para retirada normal, soma o prazo de retirada configurado no produto.
- A retirada prevista entra na roteirização mesmo sem existir ainda um card BUSCAR na Agenda.
- Ao concluir uma entrega pela Inteligência, o card BUSCAR é criado na Operação.
- Ao concluir uma retirada prevista pela Inteligência, o card BUSCAR é materializado e encerrado corretamente.
- Ao encerrar ou alterar entrega/retirada na Operação, todas as rotas inteligentes ainda abertas relêem os dados e são reconstruídas sem novo consumo de Humiat.

## Fonte da verdade

A Operação continua sendo a fonte da verdade. A Inteligência apenas prevê o que ainda não foi materializado e passa a obedecer qualquer intervenção feita pelo operador.
