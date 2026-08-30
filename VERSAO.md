# HUMIAT Conect — Versão 1.0.1

Data: 30/08/2026

## Alterações
- Waze passa a priorizar `ll=latitude,longitude` do endereço geocodificado do contrato.
- Evita a busca fuzzy de `q=` quando há coordenadas confirmadas, reduzindo troca de rua/número por primeiro resultado do Waze.
- Complemento removido também das tentativas de geocodificação; continua apenas como informação do contrato.
- Fallback por endereço textual permanece somente quando não existem coordenadas confirmadas.
- Mantida a regra de endereço independente por contrato/evento da v1.0.0.

## Commit padrão
`v1.0.1 - corrige destino Waze por coordenadas e remove complemento da geocodificacao`
