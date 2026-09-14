# HUMIAT Conect — Versão 1.0.30

## Correção — aceite e pagamento automático do sinal InfinitePay

- O aceite do cliente confirma a reserva imediatamente, sem depender do pagamento.
- Empresas com InfinitePay habilitada não desviam mais o cliente para a confirmação de aceite por WhatsApp.
- Após o aceite, o Conect cria automaticamente a cobrança do **Sinal** e redireciona para o checkout InfinitePay.
- Se já existir uma cobrança pendente válida, o sistema reaproveita o mesmo checkout para evitar duplicidade.
- Se a InfinitePay falhar ou o cliente não concluir o pagamento, a reserva permanece confirmada para cobrança posterior.
- Empresas sem InfinitePay mantêm o fluxo existente.

`v1.0.30 - restaura pagamento automatico do sinal InfinitePay apos aceite`
