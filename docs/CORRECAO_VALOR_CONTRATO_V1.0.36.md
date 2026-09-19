# Correção do valor do contrato — v1.0.36

## Sintoma
Ao salvar equipamentos/serviços em um contrato, o resumo financeiro podia exibir Total, Pago e Falta como R$ 0,00. A cobrança InfinitePay também recebia saldo zerado.

## Causa
A rota `preparar_contrato` acessava `item.itens` para montar a assinatura dos itens atuais. Em seguida fazia um `DELETE` em lote e criava novos `ReservaItem`. Como a relationship `item.itens` já estava carregada na sessão SQLAlchemy, ela podia continuar representando a coleção anterior. O total era calculado sobre essa coleção antiga. Em pré-contratos sem itens anteriores, a soma resultava em zero.

## Correção
O total passa a ser acumulado diretamente a partir dos novos itens enquanto eles são processados (`total_itens_novos`). `Solicitacao.valor` é então atualizado com esse total.

## Efeito
O valor total do contrato passa a alimentar corretamente o saldo a pagar e, consequentemente, a etapa de pagamento/InfinitePay.
