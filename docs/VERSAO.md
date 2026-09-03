# HUMIAT Conect — Versão 1.0.23

## Alterações
- Fluxo novo exclusivo para empresas com InfinitePay.
- No primeiro pagamento InfinitePay confirmado, o retorno do checkout encaminha diretamente ao WhatsApp do responsável, sem botão intermediário.
- O Conect registra `whatsapp_contrato_acionado_em`, sem presumir que o cliente tocou em Enviar no WhatsApp.
- Se o pagamento for confirmado por webhook e o cliente não voltar ao Conect, permanece a pendência “Enviar contrato”.
- Após o WhatsApp ser acionado, a pendência muda para “Confirmar recebimento”.
- Atendente pode confirmar “Contrato recebido pelo cliente”, registrando data/hora e usuário.
- “Reenviar contrato” permanece disponível como contingência.
- Segundo/pagamento final não repete WhatsApp; apenas confirma/quita e permite fechar.
- Empresas sem InfinitePay mantêm integralmente o fluxo anterior.

## Commit
`v1.0.23 - automatiza WhatsApp apos primeiro pagamento InfinitePay e confirma recebimento`
