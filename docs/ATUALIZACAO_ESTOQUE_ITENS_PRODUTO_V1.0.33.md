# Estoque compartilhado de itens — v1.0.33

## Itens iniciais por empresa

Todos são criados com quantidade de estoque igual a 0, sem sobrescrever quantidades que já tenham sido informadas:

- TV
- Som JBL
- BOMBOX JBL
- Microfone sem fio
- Pedestal
- Mesa de apoio
- Spot de LED
- Mesa de som

## Produto/Serviço

No cadastro do produto, cada item pode ser marcado como utilizado e recebe uma quantidade por unidade do produto.

## Contrato

O consumo padrão é calculado pela quantidade de produtos no contrato. O usuário pode desmarcar um recurso ou alterar sua quantidade apenas naquela locação, sem alterar o cadastro padrão do produto.

## Disponibilidade

A disponibilidade real é o menor limite entre o estoque do próprio produto e os recursos compartilhados necessários naquela data. Contratos cancelados, rejeitados ou em crédito não consomem o estoque compartilhado.
