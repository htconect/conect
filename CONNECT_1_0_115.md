# Connect 1.0.115 — dados para adicionar ao pedido e troca de data no catálogo

- Mantém o catálogo livre para navegação: WhatsApp, CEP e número não bloqueiam a abertura da vitrine.
- A tela inicial passa a oferecer WhatsApp, CEP e número como dados opcionais para já abrir o catálogo com o deslocamento calculado.
- O botão "Adicionar ao pedido" exige WhatsApp válido, CEP, número e cálculo do deslocamento.
- Se os dados ainda não estiverem completos, abre um quadro simples para informar contato/endereço e, após o cálculo, adiciona automaticamente o item que o cliente tentou escolher.
- O deslocamento calculado passa a aparecer no próprio catálogo e permanece único para o pedido, sem ser somado por item.
- Os dados de contato e entrega são reaproveitados no carrinho, na pré-reserva e no pré-contrato, sem pedir o WhatsApp novamente no final.
- O WhatsApp passa a ser validado também no servidor para pedidos vindos da vitrine, inclusive no fluxo de reserva direta.
- O pré-contrato recebe o WhatsApp informado na vitrine já preenchido.
- Alterar data dentro do catálogo não volta para a página inicial: o botão abre diretamente o calendário e recarrega a mesma vitrine para a nova data.
- A troca de data preserva tipo de evento, WhatsApp, CEP e número e recalcula o deslocamento para o mesmo endereço.
- Na tela sem disponibilidade, "Escolher outra data" também abre o calendário dentro da própria vitrine.
