# Connect 1.0.143 — Opcionais visíveis ao cliente

- Exibe somente os opcionais selecionados (nome, quantidade, valor unitário e subtotal) no link público do contrato, antes do aceite, e na consulta após o aceite.
- Discrimina os opcionais na mensagem "WhatsApp contrato" e no PDF.
- Corrige apenas o detalhamento comercial: a coluna já gravada `valor_equipamentos` inclui os opcionais. O novo valor apenas de exibição `equipamentos_sem_opcionais` é `valor_equipamentos - subtotal_opcionais`, sem alterar o total, descontos, frete, parcelas, pagamentos ou estoques.
- Mesma apresentação para contrato manual ou de vitrine; usa os opcionais congelados em `solicitacoes_opcionais`, e não o cadastro global do opcional, preservando nomes e valores do pedido.
- O vínculo do opcional TV ao recurso de estoque deve ser configurado no cadastro da empresa. Esta versão não muda o estoque nem ajusta contratos históricos.

## Validar em produção
1. Contrato com TV 32: em aceite, WhatsApp e PDF, aparece `1 x TV 32 Polegadas` + R$ 80 sem duplicar o total.
2. Contrato sem opcionais: nenhum bloco de opcionais é exibido.
3. Contratos manuais e de vitrine: o texto aparece identicamente.
4. Contrato já aceito: página permanente e PDF exibem os opcionais gravados.
