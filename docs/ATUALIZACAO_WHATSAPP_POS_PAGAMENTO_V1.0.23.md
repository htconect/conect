# v1.0.23 — WhatsApp após primeiro pagamento InfinitePay

## Regra
A automação é exclusiva de empresas com InfinitePay habilitada. Empresas sem InfinitePay não mudam de fluxo.

1. Primeiro pagamento InfinitePay (sinal ou total) confirmado.
2. Se o navegador retornar ao Conect, o servidor redireciona imediatamente para o WhatsApp do responsável da negociação com a mensagem do contrato pronta. Não existe botão “Abrir WhatsApp”.
3. O Conect grava `whatsapp_contrato_acionado_em`; esse registro comprova apenas o encaminhamento ao WhatsApp, não o envio da mensagem.
4. Se apenas o webhook confirmar e o cliente não retornar, nenhuma abertura de WhatsApp é possível; o painel mantém “Enviar contrato”.
5. Depois de o WhatsApp ser acionado, a pendência passa para “Confirmar recebimento”.
6. O atendente confirma o recebimento e o sistema grava `contrato_recebido_em` e `contrato_recebido_por`.
7. Pagamentos posteriores não repetem o envio automático.
