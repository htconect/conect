# Inteligência Operacional — estoque físico e previsões únicas

## Regras aplicadas

- Uma retirada incluída em uma rota inteligente fica reservada para aquela data.
- A mesma previsão não é repetida automaticamente em dias posteriores.
- Ao reconstruir a própria rota, ela ignora a própria reserva para permitir recálculo.
- O estoque inicial usa o total cadastrado menos equipamentos já entregues e ainda na rua.
- Retiradas previstas para o mesmo dia continuam na rua até a parada ser concluída.
- Retiradas planejadas em dia anterior são consideradas no estoque projetado do dia seguinte.
- Quando a demanda supera o estoque físico da loja, uma retirada compatível é promovida a obrigatória por estoque, sem criar horário rígido artificial.
- A auditoria informa total, quantidade na loja, quantidade na rua, demanda e déficit.
- Outras retiradas compatíveis continuam sendo oportunidades e só entram quando não atrasam entregas e respeitam a capacidade do veículo.
