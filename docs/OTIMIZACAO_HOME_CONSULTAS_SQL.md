# Otimização da Home — Conect 67

## Objetivo

Reduzir a quantidade de viagens entre Render e Neon durante o carregamento de `GET /painel`.

## Alterações

- Consolidação das contagens de solicitações e Humiats em uma consulta agregada.
- Consolidação das contagens de entregas e retiradas em uma consulta agregada.
- Uso de `COUNT(id)` para clientes e produtos, sem carregar registros.
- Pré-carregamento de cliente e pagamentos usados pelos cards.
- Pré-carregamento das relações usadas nas pendências financeiras.
- Remoção de consultas lazy disparadas durante a renderização do template.
- Inclusão de etapas de diagnóstico específicas da Home.

## Etapas disponíveis no painel de performance

- `home.resumo_solicitacoes`
- `home.resumo_operacao`
- `home.totais_cadastros`
- `home.solicitacoes_pendentes`
- `home.pendencias_contrato`
- `home.pendencias_financeiro_operacao`

## Resultado esperado

A Home anteriormente registrou 33 consultas SQL. Após o deploy, limpar o painel de diagnóstico, abrir `/painel` e verificar a nova quantidade. A expectativa é reduzir significativamente as consultas, especialmente as provocadas por relacionamentos lazy.
