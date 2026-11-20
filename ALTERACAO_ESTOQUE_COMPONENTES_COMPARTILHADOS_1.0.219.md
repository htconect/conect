# Conect 1.0.219 — estoque físico compartilhado

- Estoque passa a distinguir **equipamento principal** e **acessório**. É possível mudar o tipo dos itens existentes, sem recriar IDs ou perder vínculos.
- Em cada Produto/Operação é possível vincular qualquer quantidade de iPhone, Heineken, Portátil, JBL, microfones e TVs por locação; o mesmo recurso mantém uma única quantidade física.
- A rotina de disponibilidade já soma reservas simultâneas por recurso; o limite de um produto passa a refletir o componente mais escasso.
- Exemplo: 4 JBLs, 3 Portáteis + JBL alugados => 1 JBL livre; Pro Plus exige 2 JBLs => indisponível.
- **Combo por produto:** marque “Este item é um combo” no cadastro e vincule seu equipamento principal e todos os componentes obrigatórios. Um combo publicado sem principal é bloqueado mesmo que a proteção geral esteja desligada.
- **Proteção de principal opcional e explícita:** é ativada na página Estoque somente quando todos os produtos publicados já têm algum equipamento principal. Após ativar, produtos sem principal não podem ser publicados e a vitrine/API não lhes atribuem disponibilidade.
- Novos recursos nunca são inventados nem vinculados automaticamente a produtos existentes: primeiro cadastre as quantidades reais e confirme a composição de cada produto.
- A transição não altera contratos existentes. Os vínculos de produtos são aplicados também às reservas atuais; ajuste manual de recursos no contrato ainda pode modificar o consumo.
- A migração cria `itens_produto_servico_estoque.tipo` e `empresas.exigir_recurso_principal` com valores padrão compatíveis com versões anteriores.
- O controle não reserva itens individualizados por serial; gerencia quantidades compartilhadas por tipo e data.

## Exemplo obrigatório de teste

Quatro caixas JBL cadastradas. Três JBLs reservadas separadamente (como produto avulso ou opcional vinculado ao mesmo recurso físico). Resultado para a data: **JBL avulsa = 1; Portátil com JBL = 1; Portátil Plus (2 JBL) = 0**. O estoque do portátil deve também ter capacidade livre. Se o último Portátil com JBL for reservado, os três produtos ficam indisponíveis.

## Ativação

1. Em **Estoque**, cadastre as quantidades reais dos recursos físicos (JBL, iPhone, Heineken, Portátil etc.) apenas uma vez por tipo.
2. Em **Produtos → Editar → Operação**, marque **Este item é um combo** nos combos e associe o principal e os componentes obrigatórios com as quantidades correspondentes.
3. Nos produtos avulsos, associe o recurso físico que cada um consome; nos opcionais avulsos, mantenha o vínculo do opcional ao mesmo recurso.
4. Confira uma data com reservas existentes antes de publicar novos combos. Produtos antigos não são mapeados automaticamente; não assuma disponibilidade correta sem configurar os vínculos.

**Limite operacional:** o teste verifica validações de disponibilidade; a confirmação em produção e reservas feitas simultaneamente precisam ser validadas no ambiente real.
