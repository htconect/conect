# HUMIAT Conect — Versão 1.0.8

## Link permanente do contrato e aceite separado do pagamento

- O primeiro link de aceite passa a ser também o painel permanente do cliente para aquele contrato.
- Mostra valor total, já pago, falta pagar e histórico de pagamentos.
- Considera pagamentos manuais e InfinitePay no mesmo resumo.
- Se houver saldo e InfinitePay ativa, o cliente pode pagar pelo mesmo link.
- Se já existir checkout InfinitePay pendente, o botão reutiliza a mesma cobrança.
- Se já estiver quitado, nenhuma nova cobrança é criada.
- Após o aceite, pergunta “Prosseguir para pagamento?”; a InfinitePay não é aberta automaticamente pelo aceite.
- Pagamento manual após o aceite pode confirmar a reserva ao atingir o sinal mínimo exigido.
- Nenhuma alteração de banco e nenhuma variável de ambiente nova.

Commit:

`v1.0.8 - centraliza pagamentos no link do contrato e separa aceite do checkout`
