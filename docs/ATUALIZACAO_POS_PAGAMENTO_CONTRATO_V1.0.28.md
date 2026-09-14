# v1.0.28 — Pós-pagamento sem dependência do cliente

## Regra atualizada
1. O cliente lê e aceita o contrato.
2. O cliente efetua o pagamento pela InfinitePay.
3. Após confirmação, a página de retorno apenas informa que o pagamento foi registrado e a reserva está confirmada.
4. O retorno não abre WhatsApp e não depende do cliente tocar em “Continuar” para o contrato ser tratado.
5. Todo contrato com pagamento recebido e ainda sem `contrato_enviado_em` aparece em **Pendências > Aguardando envio**.
6. O atendente usa o botão **Enviar contrato**, preservando a rotina antiga de envio pelo WhatsApp.
7. A etapa **Confirmar recebimento** deixa de fazer parte da rotina ativa do painel.

## Motivo
O envio automático dependia do navegador retornar da InfinitePay. Quando o cliente fechava a página ou não tocava em “Continuar”, o contrato não seguia para o WhatsApp. A nova regra separa a confirmação do pagamento do envio operacional do contrato.

## Versão / commit sugerido
`v1.0.28 - simplifica pós-pagamento e restaura pendência de envio do contrato`
