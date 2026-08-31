# Regra absoluta de prazo das entregas

- A Inteligência não considera válida uma rota que chegue a qualquer entrega após o horário-limite.
- Retiradas e reaproveitamentos são descartados quando tornam uma entrega futura inviável.
- Ao gerar uma rota nova, o sistema testa a linha do tempo antes de consumir Humiat.
- Se houver atraso, a rota não é criada e nenhum Humiat é consumido.
- Rotas já existentes recalculadas recebem status `invalida_atraso` quando alguma entrega ultrapassa o limite.
- A tela da rota mostra aviso destacado de rota válida ou inválida e os cards atrasados ficam destacados.
