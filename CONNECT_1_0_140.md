# Connect 1.0.140 — Redução de consultas SQL

## Financeiro
- Removidas verificações de vínculos em SELECT por lançamento do banco: usa `vinculos_titulo_por_banco` e `vinculos_por_banco` já carregados.
- Removidas verificações de vínculos em SELECT por lançamento manual: usa `vinculos_titulo_por_manual` já carregados.
- Unificada a leitura dos vínculos de repasse; o conjunto de bancos com repasse vinculado deriva da consulta já necessária para montar a tela.
- Regra de saldos, baixas, conciliações e filtros preservada; nenhuma alteração de banco de dados.

## Reserva / Vitrine
- Busca de tipo de evento reaproveita o cache de sessão já existente, em vez de consultar novamente para preço e duração.
- A verificação dos tipos existentes alimenta o cache quando não há alterações.
- A verificação de categorias do catálogo calcula a ordem máxima a partir das categorias já consultadas; deixa de emitir `SELECT MAX` a cada acesso.
- O POST de cadastro/reserva usa o modo de *verificação de disponibilidade*: deixa de carregar novamente fotos, preços especiais, opcionais e suas exclusões. Os mesmos cálculos de reserva ativa e recursos/estoque permanecem ativos.

## Interface
- Mantido o tema/correção de Operação da versão anterior, sem alterações visuais nesta versão.

## Validação
- Sintaxe e templates; não há testes de carga com PostgreSQL nem deploy automático.
- Comparar especialmente GET `/painel/financeiro`, GET `/e/{slug}/vitrine`, POST `/e/{slug}/reserva` e GET `/painel` no monitor antes/depois.
- Se os tempos por consulta continuarem em ~113 ms, investigar proximidade Render/PostgreSQL e configuração do pool de conexões.
