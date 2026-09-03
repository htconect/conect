# HUMIAT Conect — Versão 1.0.24

## Alterações
- Corrige a fila **Confirmar recebimento** para considerar somente ocorrências do novo fluxo a partir desta versão.
- Adiciona o marcador explícito `whatsapp_contrato_confirmacao_pendente`, evitando inferência por histórico antigo.
- Contratos anteriores permanecem fora da nova fila mesmo que tenham `whatsapp_contrato_acionado_em` ou `contrato_enviado_em` de versões passadas.
- O marcador é ativado apenas quando o WhatsApp do contrato é realmente acionado no fluxo InfinitePay atual.
- Ao confirmar o recebimento, a pendência é encerrada sem apagar o histórico de envio.
- A tela do contrato não oferece mais “Confirmar contrato recebido” para registros antigos que não pertencem ao novo acompanhamento.
- Empresas sem InfinitePay permanecem sem alteração.

## Commit
`v1.0.24 - limita confirmacao de recebimento ao novo fluxo InfinitePay`
