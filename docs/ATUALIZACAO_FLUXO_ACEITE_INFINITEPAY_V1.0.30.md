# Atualização v1.0.30 — Aceite com pagamento automático do sinal

## Problema identificado

A etapa de WhatsApp adicionada ao fluxo público passou a receber o redirecionamento logo após o aceite. Por isso, mesmo com InfinitePay habilitada, o cliente via a mensagem de confirmação do aceite para o responsável em vez de seguir para a cobrança.

## Regra corrigida

1. O cliente confirma o aceite digital.
2. O aceite confirma imediatamente a reserva.
3. Se a empresa usa InfinitePay e existe sinal configurado, o Conect cria automaticamente o checkout do **Sinal**.
4. O cliente é redirecionado diretamente para a InfinitePay.
5. A confirmação de aceite por WhatsApp não interrompe mais esse fluxo.
6. Se a InfinitePay falhar ou o cliente abandonar o checkout, a reserva permanece confirmada para cobrança posterior.
7. A proteção contra cobrança duplicada e o reaproveitamento de checkout pendente continuam ativos.

Empresas sem InfinitePay preservam o fluxo próprio já existente.
