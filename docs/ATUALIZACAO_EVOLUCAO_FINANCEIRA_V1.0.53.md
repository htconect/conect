# v1.0.53 — Evolução Financeira

Nova página **Financeiro → Evolução Financeira** para acompanhar a evolução mensal da Karaokê RJ.

## Base histórica importada

- 2024: 528 contratos — R$ 157.200,00
- 2025: 540 contratos — R$ 180.850,00
- 01/2026 a 06/2026: 175 contratos — R$ 60.580,00

Os valores históricos foram cadastrados mês a mês conforme a planilha fornecida.

## Fonte automática

A partir de **01/07/2026**, quantidade e valor passam a ser calculados diretamente pelos contratos válidos/aprovados do Conect. Contratos cancelados não entram no comparativo.

## Página

- cards anuais com faturamento, quantidade, ticket médio e variação anual;
- tabela mês a mês por ano;
- indicação da origem do dado: Histórico (H) ou Sistema (S);
- gráfico comparativo por valor ou quantidade;
- navegação entre períodos de três anos;
- ajuste manual dos dados históricos anteriores a 07/2026;
- atalho na tela Financeiro e no menu Consultas.

## Persistência

Foi criada a tabela `evolucao_financeira_historico`. A série real da Karaokê RJ é importada somente quando ainda não existe, de forma que correções manuais posteriores não sejam sobrescritas.
