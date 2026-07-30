# Atualização do Otimizador Logístico

- Retiradas vencidas deixaram de ter prioridade fixa.
- Entregas são priorizadas por horário de início, limite e folga.
- Retiradas sobem somente quando liberam equipamento e podem ser encaixadas sem comprometer entregas.
- Após uma retirada, entregas do mesmo produto recebem vantagem para permitir reaproveitamento direto.
- Na ausência de coordenadas, o cálculo usa estimativa por localidade e deixa isso explícito.
- Os cards exibem início do evento, limite, chegada prevista e folga/atraso.
- O recálculo continua sem consumo de Humiat e reconstrói todas as operações atuais.
