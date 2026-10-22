# Connect 1.0.171 — Opcionais e recursos nos cards

## Alterações

- Agenda e Operação agora mostram todos os opcionais do contrato como itens individuais, com quantidades, independentemente de consumirem estoque.
- Os recursos físicos continuam totalizados separadamente e incluem opcionais com vínculo válido, sem duplicar consumo.
- Detalhe do contrato passa a exibir a lista de opcionais para separar, mesmo quando o opcional não possui recurso físico vinculado.
- Relatório "Operação > Estoque do dia" verifica todos os opcionais ativos cadastrados na empresa (inclusive aqueles que não aparecerem na data), sinalizando a falta ou inatividade do vínculo físico.
- O relatório sinaliza nos contratos consultados as diferenças entre o vínculo congelado no contrato e o vínculo cadastrado hoje, bem como opcionais sem vínculo.
- Nenhum vínculo antigo é reescrito automaticamente, e os dados de estoque/financeiro não são modificados por essas consultas.

## Conferência dos itens de estoque

O recurso físico vinculado ao opcional é registrado como snapshot em `SolicitacaoOpcional.item_estoque_id` no momento da inclusão. Alterar o cadastro do opcional posteriormente não muda retroativamente o consumo daquele contrato. A divergência aparece na auditoria para correção manual, se pertinente.

No card, `Separar do estoque` é o total físico por recurso (equipamento + opcional, conforme ajustes manuais). `Opcionais do contrato` identifica o que foi contratado, **não é um consumo adicional a somar ao total dos recursos**. Opcionais sem vínculo não aparecem no consumo físico, mas continuam na lista de preparação.

## Testes

- `pytest -q --ignore=test_frete_161.py` — 50 aprovados.
- `pytest -q test_opcionais_cards_171.py test_estoque_operacao_170.py` — 10 aprovados.
- Uma falha já existente em `test_frete_161.py` exige que a string de fonte contenha `cep:`; a rota e valor de frete não foram modificados nesta versão.

## Publicação

Atualize os arquivos da aplicação e faça o deploy. Não sobrescreva variáveis de ambiente e banco de produção.
