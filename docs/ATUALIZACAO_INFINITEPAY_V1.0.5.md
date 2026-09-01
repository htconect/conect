# InfinitePay no HUMIAT Conect — v1.0.5

## Checkout sem etapa de endereço/entrega

- O Conect deixou de enviar o objeto `address` na criação do link InfinitePay.
- O endereço do cliente e do evento continua armazenado e utilizado normalmente dentro do Conect.
- A InfinitePay recebe somente os dados necessários para identificar cliente, cobrança, contrato e retorno/webhook.
- O objetivo é evitar a etapa redundante de **Entrega/Endereço** no checkout, já que o Conect já possui essas informações.
- Os fluxos Sinal/Integral, PIX/cartão, confirmação automática, conciliação financeira e retorno ao WhatsApp do responsável permanecem inalterados.

Commit sugerido:

`v1.0.5 - remove etapa redundante de endereco do checkout InfinitePay`
