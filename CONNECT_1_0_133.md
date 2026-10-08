# Connect 1.0.133 — Vitrine e indicação manual

- A tela inicial apresenta data e opções Residencial / Empresa (reaproveitado da 1.0.132).
- O catálogo leva ao carrinho, com opcionais e preços individuais, detalhes e frete.
- Não exige WhatsApp na entrada, no carrinho ou para calcular frete.
- O botão Reservar segue para o cadastro na modalidade direta, aproveitando data, itens, horários e endereço calculado na sessão.
- Atalho Indicar no LokaFest abre página externa sem parâmetros de preenchimento; não solicita autorização, não envia dados e não altera status de solicitação.
- A antiga migração automática de configuração do LokaFest deixa de ser iniciada.

## Limitação pendente
O formulário de cadastro de contrato ainda exige WhatsApp do cliente e responsável, em validações de backend. Para transferir essa coleta exclusivamente para etapa posterior de aceite do contrato será preciso separar persistência do cadastro e contratação, garantindo duplicidade, contato e integridade de contratos existentes. Essa parte não foi removida de modo inseguro.

## Validação
Sintaxe Python, Jinja e JavaScript verificadas estaticamente. Fluxo real com PostgreSQL e pagamento ainda exige homologação.
