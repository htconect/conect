# Atualização 1.0.34 — Recursos e alertas de estoque

## Fluxo do atendente
- Em Operação, **Ver contrato** abre `/painel/solicitacao/{id}`, sem usar a tela pública nem PDF.

## Registrar equipamentos
- A seleção de produto/serviço calcula uma prévia dos recursos configurados no cadastro do produto.
- Quantidade do produto multiplica automaticamente a quantidade dos recursos.
- Depois de salvar, o atendente pode editar/desmarcar os recursos somente naquele contrato.

## Alertas
- **PRODUTO EXCEDIDO**: o número de unidades reservadas ultrapassa a quantidade física do produto disponível na data.
- **RECURSO EXCEDIDO**: TV, Som JBL, BOMBOX JBL, Microfone sem fio, Pedestal, Mesa de apoio, Spot de LED, Mesa de som ou outro recurso compartilhado ultrapassa o estoque disponível na data.

## Visibilidade
Os alertas e recursos aparecem em:
- detalhe do contrato;
- Agenda;
- Operação;
- Disponibilidade;
- Pendências da tela principal, sempre com link para o contrato afetado.
