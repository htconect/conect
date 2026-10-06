# Connect 1.0.126

Versão acumulativa para implantação direta sobre a versão anterior em produção, sem necessidade de publicar 1.0.124 ou 1.0.125 separadamente.

## Contratos e preços
- Contrato administrativo permite selecionar tabela Residencial ou Empresa, usando os preços já cadastrados no item.
- Mantém edição manual do valor unitário para exceções.
- Desconto manual em R$ disponível apenas no fluxo administrativo; a vitrine continua permitindo somente cupom.

## Cupons
- Validade considera a data de fechamento/aplicação, não a data do evento.
- KARAOKE10 ajustado para fechamento até 31/10/2026.
- Cupom aceita desconto percentual ou valor fixo.
- Frete permanece fora da base de desconto.

## Opcionais e recursos
- Opcionais passam a existir separadamente dos recursos do contrato.
- Opcional gera cobrança adicional.
- Recurso representa consumo físico/estoque.
- Um opcional pode ser vinculado a um recurso; quando a empresa usa controle de recursos/estoque, a quantidade opcional também soma ao consumo do recurso.
- Exemplo: Just Dance inclui 1 TV e o cliente adiciona 1 TV opcional de R$ 50,00: contrato mostra TV opcional 1 x R$ 50,00 e estoque considera TV = 2.
- Empresas podem operar com estoque + opcionais, somente estoque, somente opcionais ou nenhum dos dois.
- A mesma regra é usada em contratos manuais e contratos originados pela vitrine.

## Fluxo público
- Pedido originado pelo link direto segue para aceite quando o contrato já está pronto, e depois para pagamento.
- O fluxo configurado com aprovação continua respeitado nos casos que realmente exigem aprovação/sob consulta.

## Compatibilidade com contratos anteriores
- Novas estruturas não reinterpretam contratos já fechados, aceitos, pagos ou concluídos.
- Recalculo automático da nova composição comercial fica restrito a rascunhos (`pre_reserva`/`reserva`).
- O histórico financeiro e operacional já confirmado permanece congelado.
