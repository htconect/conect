# HUMIAT Conect — Versão 1.0.6

## InfinitePay e compatibilidade de clientes antigos

- E-mail visível/obrigatório passa a ser validado no servidor somente nos novos envios do pré-contrato.
- Registros antigos continuam podendo ser abertos mesmo quando ainda não possuem e-mail; o banco não recebeu restrição NOT NULL.
- Cliente antigo sem e-mail pode informar o e-mail ao reutilizar o cadastro; o campo não fica travado vazio.
- Se o contrato já tiver qualquer pagamento, a InfinitePay oferece somente o saldo restante, nunca o valor total original.
- Enquanto houver uma cobrança InfinitePay com status AGUARDANDO_PAGAMENTO e URL válida, o Conect reutiliza o mesmo checkout e não cria outro.
- Nova cobrança só é criada quando não existe checkout ativo local (por exemplo, tentativa anterior em ERRO_CHECKOUT).
- Contrato aprovado com saldo pendente passa a exibir botão para pagar somente o restante pela InfinitePay.
- Endereço continua somente no Conect e não é enviado ao checkout.
- Fluxo manual permanece disponível.

Commit:

`v1.0.6 - protege cobrancas InfinitePay e compatibilidade de email`
