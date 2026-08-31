# Inteligência Logística — implementação concluída

## Correções estruturais
- Inclui entregas por `Agenda.data` e retiradas por `Solicitacao.retirada_data`.
- Exclui operações concluídas, rejeitadas e canceladas.
- Usa itens e quantidades reais do contrato para calcular carga.
- Permite configurar pontos de carga por produto.
- Exibe operações sem coordenadas e aplica previsão conservadora de 30 minutos.

## Motor de cálculo
- Ordena por risco de atraso, folga, liberação de retirada e distância.
- Calcula chegada, saída, deslocamento, serviço e risco por parada.
- Insere retornos automáticos à loja conforme capacidade do veículo.
- Recalcula a rota preservando paradas concluídas.
- Calcula distância, duração, retornos, carga máxima e custo estimado.

## Configurações
- Loja e coordenadas.
- Tempos de montagem, desmontagem e parada na loja.
- Antecedência de entrega e velocidade média.
- Custo por km e custo da equipe por hora.
- Veículos com capacidade em pontos.

## Banco de dados
As novas colunas são criadas automaticamente no startup, tanto em banco novo quanto existente.
