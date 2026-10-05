# Connect 1.0.102

## Vitrine — data e tipo de evento
- A entrada pública agora pede Data + Tipo de evento antes de montar o catálogo.
- Nesta etapa existem apenas Residencial e Empresa.
- Ao continuar, a interface mostra “Montando seu catálogo” enquanto consulta disponibilidade e aplica a regra de preço.
- Cada tipo de evento, no cadastro do item, possui as três opções: Preço normal, Preço fixo e Sob consulta.
- Preço normal usa o valor principal do item; Preço fixo abre/salva um valor próprio; Sob consulta não mostra valor na vitrine.
- A escolha do tipo de evento acompanha o pedido até o pré-contrato.

## Opcionais do item
- Novo cadastro de opcionais dentro de Preço e horário: Nome, Qtd. e Valor.
- Opcionais podem ser adicionados/removidos no cadastro do item.
- Quando o item possui opcionais, a vitrine permite escolher a quantidade de cada opcional.
- O valor dos opcionais entra no subtotal, no desconto e na composição comercial do pedido.
- Os opcionais escolhidos seguem descritos no item da reserva.

## Deslocamento
- Mantidas as três regras: Valor fixo, Por KM e Sob consulta.
- Por KM usa o CEP de origem da empresa e CEP + número do evento.
- A cobrança é ida e volta: distância rodoviária de ida × 2 × valor por KM.
- Sob consulta não cria valor falso na vitrine.

## Cupom
- Cupom continua disponível na vitrine quando o módulo Cupons estiver ativo.
- O desconto é aplicado aos itens e opcionais; deslocamento permanece separado.

## Compatibilidade
- Tipos de evento antigos permanecem no banco para histórico, mas a tela atual trabalha somente com Residencial e Empresa.
