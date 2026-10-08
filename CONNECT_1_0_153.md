# Connect 1.0.153 — Orientação de exclusão após cobrança Humiat

- Ao bloquear a exclusão de um contrato com movimento de cobrança Humiat, informar claramente que a cobrança já foi gerada e que a ação adequada é **Cancelar contrato**.
- Removida a orientação genérica «Verifique a movimentação na Carteira Humiat» nesse bloqueio.
- Mantida a proteção dos registros de Humiat e a separação entre cancelamento e exclusão; nenhuma movimentação financeira é alterada por esta versão.

## Validação

1. Tentar excluir contrato que já gerou cobrança Humiat e não possui bloqueios financeiros anteriores; verificar a mensagem.
2. Confirmar que o contrato e a cobrança permanecem cadastrados.
3. Usar o fluxo habitual de cancelamento, sem exclusão.
