# HUMIAT Conect — Versão 1.0.68

## Financeiro
- A aba **A pagar** ganhou o botão **Pagar** em cada título manual em aberto.
- O pagamento abre uma caixa com **Banco**, **Data do pagamento** e **Valor**.
- O banco vem pré-selecionado conforme o filtro atual do Financeiro e pode ser alterado no combo antes da confirmação.
- Ao confirmar, o Connect cria a saída financeira na conta escolhida e já vincula essa saída ao título, sem exigir novo lançamento e vínculo manual.
- Pagamentos parciais continuam suportados; o título permanece parcial até quitar o saldo.
- O botão **Importar** só fica habilitado quando o filtro estiver no **Banco Principal**.
- O backend também bloqueia importações direcionadas a qualquer outra conta, mesmo que a requisição seja enviada manualmente.

## Contratos / Operação
Mantidos os ajustes da versão 1.0.67 para suporte, retirada, disponibilidade e recursos.

## Commit sugerido
`Connect 1.0.68 - simplifica pagamento de contas e restringe importacao ao banco principal`
