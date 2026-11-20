# Conect 1.0.218 – datas futuras no Banco Principal

## Diagnóstico
O importador de CSV/XLSX mantém a data informada na coluna Data do extrato. Em 20/11/2026, movimentos datados de 23/11/2026 ficam fora do indicador de saldo bancário **até hoje**, por causa do filtro `LancamentoBanco.data <= hoje`. Eles já participam dos totais mensais de novembro, porque estes consideram o mês completo.

## Alterações
- No resumo financeiro, o saldo do banco fica explicitamente rotulado como **até hoje**.
- Um segundo indicador aparece quando existem lançamentos de data futura importados: **Com lançamentos futuros do extrato**. Ele mostra o saldo do banco calculado incluindo essas importações, e sinaliza que é **projeção, não saldo disponível**.
- Um alerta informa o número de movimentos futuros, o período e totais de entradas/saídas.
- A tabela do banco marca cada data futura como **Previsto**.
- A data de referência do Financeiro passa a usar `America/Sao_Paulo`, inclusive no corte de saldo. Não modifica datas gravadas.
- A projeção considera o ano civil atual, pois o saldo existente também é calculado somente a partir de 1º de janeiro, sem saldo inicial.

## Preservações
- Nenhum registro bancário é alterado ou excluído.
- A importação e a prevenção de duplicidades não mudam.
- O saldo disponível até hoje não incorpora transações futuras.
- O balanço mensal, contas a pagar, a receber e conciliações mantêm a lógica anterior.

## Conferência importante
Se o extrato bancário **realmente informa 23/11**, o Conect não deve converter essa data automaticamente para 20/11. Se essa for uma data errada no arquivo original, investigue a origem antes de reimportar; a identificação de duplicidades considera a data, de modo que uma importação corrigida pode gerar movimentos duplicados se os registros anteriores não forem tratados adequadamente.
