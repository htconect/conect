# Connect 1.0.119 — Vitrine usando o fluxo padrão do contrato

- Remove o fluxo paralelo para novos pedidos com aprovação da vitrine.
- Pedido da vitrine com análise nasce como o rascunho padrão `pre_reserva`, já com equipamentos, valores, frete, horários e endereço preenchidos.
- A observação visível registra `Origem: Vitrine`.
- `Atender e enviar cadastro` apenas libera o rascunho para o cliente completar os dados que faltam.
- Depois do cadastro, o pedido não volta para análise: segue pelo mesmo caminho da reserva direta para aceite e pagamento.
- A etapa de adicionar equipamento é pulada porque os itens já vieram da vitrine.
- `Indicar no LokaFest` cancela o rascunho no Connect e registra `Enviado para o LokaFest`.
- Contrato cancelado por indicação mantém o botão `Indicar novamente no LokaFest`, permitindo repetir a abertura caso a indicação externa não seja concluída.
- Pedidos antigos da v1.0.118 continuam compatíveis para não perder registros já criados.

Datas adicionais consecutivas e combos continuam fora desta versão.
