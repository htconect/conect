# HUMIAT Conect — Versão 1.0.16

## Pente-fino do fluxo público de pagamento

- O primeiro pagamento mantém a confirmação **Sua reserva foi efetuada com sucesso** e a etapa de disponibilização do contrato no WhatsApp.
- O pagamento final agora usa mensagem própria: **Seu contrato está quitado**, sem repetir a mensagem de criação da reserva.
- No pagamento final o valor da cobrança é identificado como **Valor pago agora**, evitando confundir o cliente com a palavra “Saldo”.
- A confirmação final fica em um único card, mais curto e adequado para celular.
- O botão **Fechar** do pagamento confirmado passou a usar exatamente a mesma rotina de fechamento usada no link permanente da reserva.
- Fechamento de cláusulas e demais telas públicas foi centralizado na mesma função; quando o navegador impede o fechamento automático, aparece apenas uma orientação curta.
- O padrão global de botões do Conect foi revisado: **Fechar**, **Agora não**, **Sim, prosseguir**, **Tentar novamente**, **Ver cláusulas**, **Copiar PIX**, **Enviar reserva** e ações de pagamento recebem ícone, cor e formato coerentes.
- Removido o ícone genérico em círculo de ações como **Fechar**.
- Botões públicos agora podem quebrar texto de forma controlada em telas estreitas, sem estourar horizontalmente a página.
- PIX e Cartão mantêm botões próprios, compactos e sem interferência do decorador automático.
- A tela de WhatsApp do pré-contrato/aceite recebeu o mesmo tratamento responsivo dos demais passos.
- Texto legado da tela antiga de escolha de pagamento foi corrigido para não afirmar abertura automática do WhatsApp.

## Fluxos preservados

- Empresa com InfinitePay: aceite → sinal/total → checkout → primeiro pagamento com envio do contrato → saldo → quitação.
- Empresa sem InfinitePay: aceite → PIX da empresa, sem alteração da rotina já existente.
- Mesmo link da reserva continua atendendo aceite, pagamento, saldo e consulta final.
- Cobrança InfinitePay pendente continua idempotente para evitar duplicidade.

Commit sugerido:

`v1.0.16 - revisa confirmação final, fechamento e padrão de botões do fluxo público`
