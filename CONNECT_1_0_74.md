# Connect 1.0.74

Aplicação do último ajuste financeiro sobre a base correta 1.0.73.

- No **A Pagar**, o botão **Pagar** abre apenas banco, data e valor.
- O banco vem do filtro atual e pode ser alterado no combo antes da confirmação.
- A baixa gera automaticamente a saída financeira vinculada ao título existente.
- Pagamento parcial permanece disponível.
- O botão **Importar** só fica habilitado quando o filtro está em **Banco Principal**.
- O servidor também bloqueia qualquer tentativa de importar em outra conta.
- Removido o fallback para outra conta do tipo banco: somente o cadastro explicitamente chamado **Banco Principal** pode receber importação.
- Mantidas integralmente as funcionalidades da 1.0.73.
