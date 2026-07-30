# Inteligência Operacional — Fase 1 (visão semanal)

## Objetivo

A Inteligência planeja a semana, recomenda horários e respeita o estado real da Operação. Ela não toma decisões comerciais.

## Decisões aplicadas

- A visão ativa passa a considerar a semana operacional.
- Entregas e retiradas concluídas somem da tela ativa, mas permanecem no histórico.
- Retiradas previstas antes da conclusão da entrega aparecem apenas como previsão semanal.
- Uma retirada que ainda aguarda entrega não pode ser iniciada nem concluída.
- Antes do início da rota, a tela mostra **Horário recomendado**.
- **Chegada prevista** e **Atraso previsto** só aparecem durante a execução.
- Cada parada mostra data, dia da semana e acesso rápido ao contrato.
- Ao concluir uma parada, o restante da rota é recalculado.

## Arquivos alterados

- `app.py`
- `templates/admin/inteligencia_rota.html`

## Continuidade

A evolução futura deve manter separados os conceitos de planejamento semanal e execução da rota.
