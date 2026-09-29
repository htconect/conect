# HUMIAT Conect — Versão 1.0.74

## Financeiro — pagamento direto no A Pagar
- Cada título em aberto mantém o botão **Pagar**.
- O popup usa o banco selecionado no filtro como padrão e mantém o **combo de bancos** disponível para troca antes da confirmação.
- Data do pagamento e saldo em aberto são preenchidos automaticamente e podem ser ajustados antes de confirmar.
- A confirmação cria a saída financeira e vincula a baixa ao próprio título, sem redigitar descrição/categoria e sem vínculo manual posterior.
- Pagamentos parciais continuam suportados.

## Financeiro — importação protegida
- **Importar** fica habilitado exclusivamente quando o filtro está no cadastro chamado **Banco Principal**.
- Em qualquer outra conta o botão permanece desabilitado.
- O backend também rejeita importação para qualquer conta diferente do **Banco Principal**.
- Removido o fallback que poderia tratar outro banco como principal quando o cadastro nomeado não fosse encontrado.

## Base preservada
- Mantidas as alterações da versão 1.0.73, incluindo a padronização de pagamentos InfinitePay como **Online** e a edição em lote de categorias no relatório financeiro.

## Commit sugerido
`Connect 1.0.74 - aplica pagamento direto e restringe importacao ao Banco Principal sobre a base 1.0.73`
