# Atualização do fluxo público — v1.0.11

## Mensagem padrão do link

Olá, {{cliente}}! Sua reserva está aguardando seu aceite.

*Clique no link abaixo para continuar:*
{{link}}

No link você poderá conferir os dados da reserva, ler as cláusulas e consultar as informações de pagamento e, quando disponível, as opções de parcelamento.

*Importante:* o contrato só será efetuado após a conclusão desta etapa.

## Estados do mesmo link

1. Não aceito: leitura em seções recolhíveis + aceite.
2. Aceito e sem pagamento: etapa de pagamento.
3. Pagamento parcial: somente saldo restante.
4. Quitado: reserva concluída, sem nova cobrança.

## Empresas com InfinitePay

- Sinal ou valor do contrato no primeiro pagamento.
- PIX ou cartão no checkout.
- Parcelamento conforme opções apresentadas.
- Primeiro pagamento confirmado: oferece disponibilização do contrato no WhatsApp, sem abertura automática.
- Segundo pagamento: somente agradecimento.

## Empresas sem InfinitePay

- Usa o PIX cadastrado na empresa.
- Exibe nome do recebedor e banco/instituição para conferência.
- Primeiro pagamento: sinal ou valor total quando houver sinal configurado.
- Depois de pagamento parcial: somente saldo restante.
- Não abre WhatsApp na etapa de pagamento.
