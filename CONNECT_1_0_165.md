# Connect 1.0.165 — Atualização da Operação após remarcação

## Correção
- Ao alterar a data de um contrato aprovado, a agenda operacional **pendente** acompanha o novo dia, inclusive quando a entrega já tiver sido roteirizada.
- Entrega e retirada comuns mudam pelo mesmo intervalo de dias. A retirada obrigatória acompanha a data e o horário contratados.
- Equipe, status pendente, informações de rota e histórico operacional permanecem; um registro de alteração é acrescentado às observações.
- A entrega nunca pode ficar depois da data e do horário de início do evento.
- Entregas e retiradas **concluídas** não são modificadas automaticamente.

## Reparar registros antigos
1. Abra Operação e ajuste os filtros para a data antiga, por exemplo, 12/10/2026.
2. Expanda o card da entrega e escolha **Corrigir datas pelo contrato** na seção “Datas diferentes”.
3. Confirme a correção. A página abrirá a nova data do contrato, por exemplo, 07/11/2026.
4. Confira a equipe, a rota e os horários. Se usar Google Agenda, clique em **Sincronizar Google** após conferir.

Não altera valor, contrato, cliente, pagamentos ou frete. Os links pessoais e o compartilhamento da vitrine permanecem funcionando.

## Testes
- Compilação Python do app/config.
- Testes offline SQLite: remarcação 12/10 → 07/11, entrega e busca comum, retirada obrigatória, dados legados, histórico concluído, chamada do endpoint e template Jinja2.
- Não houve teste no banco nem no ambiente de produção Render.
