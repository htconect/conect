# Connect 1.0.138 — Financeiro e CSS da Operacao

- O CSS do painel (`connect-adminator.css`) passou para o `<head>` do layout base, evitando exibir a Operacao sem o estilo final durante o carregamento.
- Financeiro: elimina a segunda consulta identica de pagamentos quando status_sistema=todos, reutilizando o resultado ja carregado. Filtros pendente/vinculado permanecem independentes.
- Outras 40 consultas do Financeiro ainda necessitam auditoria e otimização progressiva; nao há promessa de reducao total.
- Sem alteracoes de saldos, pagamentos, vinculos ou migracoes.
