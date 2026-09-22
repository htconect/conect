# Atualização Financeiro — v1.0.38

## Objetivo
Permitir controle real de contas a pagar e a receber com liquidações parciais vinculadas aos movimentos bancários.

## Regras implementadas
- Tipos manuais: `real` (movimento), `receber` e `pagar`.
- Entrada bancária (`valor > 0`) só baixa título `receber`.
- Saída bancária (`valor < 0`) só baixa título `pagar`.
- Cada vínculo grava o valor efetivamente baixado em `vinculos_titulos_financeiros`.
- O saldo do título é `valor original - soma das baixas`.
- O título só é marcado como liquidado quando a soma das baixas atinge o valor original.
- Ao remover uma baixa, o título volta automaticamente para aberto/parcial.
- Movimentos e títulos com vínculos não podem ser excluídos.

## Exemplo
Conta a pagar: R$ 4.000,00.
Movimento do banco: -R$ 2.000,00.
Após o vínculo: pago R$ 2.000,00 e saldo a pagar R$ 2.000,00.

## Relatório
A posição financeira exibe:
- valor no banco;
- total a receber em aberto;
- total a pagar em aberto;
- saldo projetado = banco + receber - pagar.
