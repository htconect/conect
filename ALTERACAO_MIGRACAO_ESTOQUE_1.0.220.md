# Conect 1.0.220 — correção emergencial do erro 500 pós 1.0.219

## Causa

A atualização 1.0.219 acrescentou três colunas ORM (`empresas.exigir_recurso_principal`, `produtos_servicos.eh_combo`, `itens_produto_servico_estoque.tipo`), mas só as incluiu em `garantir_colunas_novas()`, executado quando `CONNECT_RUN_STARTUP_MAINTENANCE=1`. No Render, startup normal ignora essa rotina. Portanto, SELECTs de `Empresa` causavam `psycopg2.errors.UndefinedColumn`, quebrando a navegação do painel.

## Correção

Inclui as três colunas também em `_garantir_colunas_v113_criticas()`, executado no startup normal. Usa `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, com defaults falsos/`acessorio` para preservar estado atual e impedir bloqueio automático de produtos ainda não configurados. Não apaga, reescreve ou migra registros de contratos/financeiro.

## Recuperação imediata por SQL (somente banco correto, com backup)

```sql
ALTER TABLE empresas ADD COLUMN IF NOT EXISTS exigir_recurso_principal BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE produtos_servicos ADD COLUMN IF NOT EXISTS eh_combo BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE itens_produto_servico_estoque ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) NOT NULL DEFAULT 'acessorio';
```

Executar manualmente essas instruções é opcional se o 1.0.220 for publicado; após o novo deploy, startup normal tenta criar os campos idempotentemente. Confirme em produção que as tabelas existem antes de aplicar a migração manual.

## Validação

Teste local automatizado verifica presença das três migrações na inicialização crítica. Exige teste real do Render após publicação. Os testes unitários não fazem deploy nem modificam o PostgreSQL de produção.
