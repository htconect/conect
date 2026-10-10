# Connect 1.0.155 — vitrine e diagnóstico de estoque

- Corrigido CSS da vitrine: o aviso `Sem estoque nesta data` respeita o atributo `hidden` e aparece apenas quando o saldo do recurso está efetivamente insuficiente.
- Reservas consideradas no cálculo do estoque: somente contratos liberados para operação (`aceito`, `aguardando_pagamento`, `reserva_confirmada`). Pré-reservas, contratos aguardando aceite e créditos não bloqueiam a vitrine.
- Preservadas validações de estoque de equipamentos e opcionais, inclusive no servidor. Nenhum bloqueio real é ignorado.
- Adicionado `Agenda → Consumo de estoque`, com filtro por data, quantidades de produtos e recursos, reservas consideradas e contrato de origem.
- Calendário mensal deixa de contabilizar contratos em crédito (`aguardando_nova_data`) e pré-reservas da vitrine como contratos ativos do dia.

## Observação de produção
A base do Render não está no ZIP, portanto estoque e reservas reais devem ser conferidos na nova tela para 11/10/2026. Não foram alterados quantidade de estoque nem os contratos existentes.
Links legados numéricos de PDFs requerem solução separada de autenticação/compatibilidade; não foram tornados públicos nesta versão.
