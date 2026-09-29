# Atualização Financeiro — Connect 1.0.68

## Pagamento direto no A Pagar
- Cada título manual em aberto possui o botão **Pagar**.
- O popup reaproveita o lançamento existente e solicita somente:
  - banco/conta;
  - data do pagamento;
  - valor.
- O banco abre selecionado conforme o filtro atual do Financeiro e pode ser alterado no combo.
- O valor abre com o saldo em aberto do título.
- Ao confirmar, o Connect cria a saída financeira e vincula automaticamente a baixa ao título.
- Baixa parcial continua permitida e mantém o saldo restante como **Parcial**.

## Importação de extrato
- O botão **Importar** fica habilitado somente quando o filtro está no **Banco Principal**.
- Em outros bancos/contas, o botão permanece desabilitado.
- A rota de importação também valida a conta no servidor e rejeita importação fora do Banco Principal.

## Versão
- APP_VERSION: 1.0.68

## Commit sugerido
`Connect 1.0.68 - simplifica pagamento de contas e restringe importacao ao banco principal`
