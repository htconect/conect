# Atualização InfinitePay — v1.0.8

## Link permanente do cliente

O mesmo link enviado para o primeiro aceite passa a concentrar todo o acompanhamento do contrato:

- valor total;
- total já pago;
- saldo restante;
- histórico de pagamentos manuais e InfinitePay;
- botão para pagar quando houver saldo;
- reutilização da cobrança InfinitePay pendente, sem gerar uma segunda cobrança concorrente;
- bloqueio de nova cobrança quando o contrato estiver quitado.

## Aceite separado do pagamento

O aceite não abre mais a InfinitePay automaticamente. Após registrar o aceite, o cliente vê a pergunta **“Prosseguir para pagamento?”**. Somente ao escolher **Sim** ele segue para a etapa de pagamento.

## Pagamento manual e automático

A página pública usa a tabela `pagamentos` como fonte de verdade, portanto pagamentos lançados manualmente e pagamentos confirmados pela InfinitePay aparecem no mesmo resumo.

Se o contrato já foi aceito e um pagamento manual atingir o sinal mínimo (ou o valor integral quando não há sinal), a reserva é confirmada pela mesma regra operacional usada no pagamento automático.

## Compatibilidade

- Sem novas colunas de banco.
- Sem novas variáveis de ambiente.
- Contratos antigos continuam abrindo.
- O fluxo manual permanece disponível.
