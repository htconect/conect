# Connect 1.0.139 — Leituras agrupadas por requisição

- Reutiliza os tipos de evento na mesma sessão de requisição, isolando por empresa.
- Mantém filtros de tipos ativos e atualiza a leitura quando há alterações pendentes.
- Evita cache global compartilhado entre clientes.
- Pendente: otimizar gravação da reserva, consulta de estoque e latência PostgreSQL.
