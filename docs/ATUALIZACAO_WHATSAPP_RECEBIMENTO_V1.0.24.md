# v1.0.24 — Confirmação de recebimento somente daqui para frente

## Objetivo
Evitar que contratos antigos apareçam retroativamente na fila **Confirmar recebimento** apenas porque possuíam histórico de envio/WhatsApp de versões anteriores.

## Regra nova
- Exclusiva para empresas com InfinitePay habilitada.
- A fila **Confirmar recebimento** usa o marcador explícito `whatsapp_contrato_confirmacao_pendente`.
- Contratos existentes antes desta versão recebem o valor padrão `false` e não entram na nova fila.
- O marcador passa para `true` somente quando, a partir desta versão:
  - o retorno do primeiro pagamento InfinitePay aciona automaticamente o WhatsApp; ou
  - o atendente aciona/reenvia o contrato pelo fluxo InfinitePay após existir pagamento; ou
  - o fluxo público registra um clique real para abrir o WhatsApp do contrato após pagamento.
- Ao confirmar o recebimento, o marcador volta para `false` e são preservados data/hora e atendente da confirmação.
- O histórico antigo de `whatsapp_contrato_acionado_em` continua preservado apenas para auditoria, sem gerar pendência retroativa.
- Empresas sem InfinitePay continuam com o fluxo anterior, sem alteração.
