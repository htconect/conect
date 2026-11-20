# Conect 1.0.218 — Banco Principal: data contábil x saldo disponível

## Problema observado
Em 20/11/2026 (sexta), o banco exibe no extrato movimentos que **já estão efetivados e com dinheiro disponível**, mas registra a data contábil de 23/11/2026 (segunda-feira, próximo dia útil). O Conect 1.0.217 excluía esses valores do saldo acumulado do Banco Principal, pois aplicava `LancamentoBanco.data <= hoje`.

## Regra aplicada
- O valor do lançamento e sua **data contábil** original continuam preservados (23/11), para conciliação e histórico mensal.
- No saldo acumulado do Banco Principal e na posição financeira, lançamentos já **importados do extrato** (`origem_importacao` presente), com data contábil até o **próximo dia útil** e importados até o fim do dia local de referência, são contabilizados como realizados.
- Um lançamento bancário futuro **não importado do extrato**, um lançamento manual e um movimento com data posterior ao próximo dia útil não são antecipados no saldo.
- O extrato mostra o selo **Extrato efetivo** para movimentos incorporados ao saldo apesar da data contábil posterior; a tela informa os valores incorporados.
- A data de referência é `America/Sao_Paulo`; o limite de importação usa a virada de dia convertida para UTC, inclusive após 21h de Brasília.
- Os totais mensais continuam classificados pela **data contábil do arquivo**. O saldo do banco continua acumulado a partir de 1º de janeiro como nas versões anteriores; esta alteração não implementa saldo inicial.
- Não há migração nem alteração em registros antigos; os já importados passam a ser considerados automaticamente na visualização.

## Observação operacional e limite
Essa regra pressupõe que **Importar extrato** contém somente movimentos efetivados, não a lista de pagamentos **agendados**. Não importe agendamentos no Banco Principal; use os títulos a pagar/receber até a efetivação. O tratamento automático cobre o próximo dia útil de segunda a sexta, pulando sábados e domingos; não é um calendário completo de feriados bancários. Para feriados em dias úteis sem o mesmo cenário de sexta-feira, pode ser necessária uma regra específica.

## Testes
- Movimentos contabilizados em 23/11 já importados em 20/11 aparecem no saldo de 20/11.
- Movimentos não importados, de 24/11 e importados após a data de corte não antecipam o saldo.
- Movimentos importados após 21h de Brasília no dia 20/11 são considerados corretamente.
- A data original é mantida e não há duplicação na importação.
