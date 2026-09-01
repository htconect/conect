# HUMIAT Conect — Versão 1.0.13

## Pagamento e consulta do contrato no celular

- A etapa InfinitePay mostra sempre, inclusive no pagamento do saldo, as formas disponíveis: **PIX** e **Cartão**.
- PIX e Cartão aparecem de forma visual antes do cliente continuar para o checkout; a escolha efetiva continua sendo feita na tela segura da InfinitePay.
- Quando cadastrados na empresa, **nome do recebedor** e **banco/instituição** ficam visíveis para conferência caso o cliente escolha PIX.
- A regra de cobrança não mudou: no segundo pagamento o Conect oferece somente o saldo restante, evitando nova cobrança de sinal ou do valor original.
- A área “Consultar contrato aceito” ganhou o botão **Fechar**, permitindo apenas consultar e recolher a seção sem iniciar pagamento.
- A página “Ver cláusulas” também ganhou **Fechar**; quando o navegador não permite fechar a aba, o cliente retorna ao mesmo link da reserva, na etapa de pagamento.
- Empresas sem InfinitePay permanecem no fluxo PIX próprio já existente.

Commit:

`v1.0.13 - mantém PIX e cartão visíveis no saldo e adiciona fechar nas cláusulas`
