# Atualização da Inteligência Operacional

## Regras implementadas

- Entregas e retiradas são operações independentes, mesmo quando pertencem ao mesmo contrato.
- A consulta inclui entregas do dia, retiradas do dia e retiradas pendentes de dias anteriores.
- Quando o contrato possui retirada prevista e não existe card de retirada na agenda, a operação é criada virtualmente para o cálculo.
- Retiradas vencidas e retiradas obrigatórias ficam antes das entregas.
- Depois são ordenadas as entregas e, por último, as retiradas opcionais.
- Quando não há horário de retirada, o sistema sugere automaticamente um horário e informa isso na rota.
- O motor cruza produtos e quantidades. Se a quantidade disponível não cobre as entregas do dia, a retirada compatível é promovida para obrigatória.
- Retiradas compatíveis com entregas são marcadas como oportunidade de reaproveitamento do equipamento.
- Ao escolher uma equipe, operações ainda sem equipe também continuam visíveis, evitando que contratos desapareçam da Inteligência.
- O consumo de Humiat continua ocorrendo apenas depois que existem operações válidas para salvar.
