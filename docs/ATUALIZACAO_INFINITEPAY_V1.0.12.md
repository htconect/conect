# Atualização InfinitePay — v1.0.12

## Objetivo

Evitar que o cliente precise digitar novamente o CEP e o endereço na etapa de pagamento quando esses dados já existem na reserva.

## Regra

O endereço enviado à InfinitePay é o endereço do contrato/reserva. O Conect envia `address` com `cep`, `street`, `neighborhood`, `number` e `complement`.

Contratos antigos com endereço incompleto podem recuperar apenas os campos ausentes de um endereço histórico compatível do mesmo cliente. A regra não troca o endereço congelado do contrato.

Empresas sem InfinitePay continuam no fluxo de PIX próprio, sem alteração.
