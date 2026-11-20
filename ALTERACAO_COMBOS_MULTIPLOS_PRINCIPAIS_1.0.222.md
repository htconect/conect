# Conect 1.0.222 — área exclusiva para Combos

## Cadastro

- Menu lateral: **Combos** → **Novo combo**. Não é necessário cadastrar componentes físicos duplicados.
- Em **Produtos e serviços** ficam apenas os produtos principais, com seu estoque próprio.
- O combo usa os produtos principais já cadastrados, com quantidade individual (exemplo: 1 Portátil + 1 Fliperama + 1 Just Dance).
- O combo **não tem quantidade própria**. Seu teto por data é o menor saldo possível entre todos os componentes: `min(floor((estoque_principal - comprometido_principal) / quantidade_no_combo))`.
- Os opcionais e recursos adicionais do combo vêm **somente do próprio cadastro do combo**. Não herda opcionais dos principais nem recria itens.
- Bloqueios de data do combo ou de qualquer principal também bloqueiam o combo.
- Confirmação de reservas e aceite manual conferem todos os principais, recursos e opcionais de todas as datas incluídas na locação, inclusive período 24/12 a 26/12.
- Opções de produtos antigos cadastradas como `tipo=principal` na área de recursos físicos (modelo 1.0.219) deixam de ser consideradas. Os dados não são apagados.

## Banco de dados e migração

- Nova tabela **combo_produtos_principais**, com (empresa_id, combo_id, produto_principal_id, quantidade_por_combo) e chave única por par.
- O startup leve cria a tabela automaticamente via `CREATE TABLE IF NOT EXISTS` no PostgreSQL, sem `CONNECT_RUN_STARTUP_MAINTENANCE=1`.
- **Não apaga nem renomeia colunas antigas**, preservando registros do cliente. O campo obsoleto `empresas.exigir_recurso_principal` não é mais consultado ou criado.
- Para combos anteriores que tinham `produtos_servicos.produto_principal_id` preenchido, existe leitura compatível até serem editados. Ao salvar, a composição passa para a nova tabela e o vínculo legado é desativado.
- Não é necessário executar comandos SQL manualmente se o startup do Render funcionar normalmente.
- Faça backup do PostgreSQL antes de publicar, pois esta atualização altera o esquema.

## Implantação

Instale apenas se seu repositório local estiver exatamente em 1.0.220 (patch específico); caso contrário use o ZIP completo com cuidado para preservar arquivos locais.

1. `git apply --check Conect_1.0.222_patch_sobre_1.0.220.patch`
2. `git apply Conect_1.0.222_patch_sobre_1.0.220.patch`
3. `pytest -q` (na mesma dependência do projeto)
4. `git add -A && git commit -m "Cria area de combos com multiplos produtos principais" && git push origin main`
5. Acompanhe logs de deploy do Render. Confirme que a tabela existe e que /painel/combos abre sem erro 500.
6. Configure no painel: principal Portátil, Fliperama, Just Dance; combo com três itens 1/1/1 e seus opcionais próprios.
7. Antes de liberar a vitrine, confira contratos existentes, quantidades físicas e situações de estoque indisponível.

**Limite de validação:** testes automatizados foram executados localmente. O deploy real e o banco PostgreSQL de produção precisam ser testados após publicar.
