# HUMIAT Conect — Versão 1.0.65

## Operação manual — tempos ponto a ponto

- `Equipe tempo` mostra somente o deslocamento entre o ponto anterior e o atual.
- `Tempo de chegada` soma o deslocamento com o tempo operacional executado na etapa anterior.
- Entrega usa o parâmetro de instalação da Inteligência.
- Retirada/Busca usa o parâmetro de desmontagem da Inteligência.
- Parada na loja usa o parâmetro de parada na loja da Inteligência e não soma instalação/desmontagem.
- Antes do cálculo, o Connect tenta localizar loja e contratos sem coordenadas para evitar o antigo fallback fixo de 30 minutos.
- O cálculo manual força nova consulta do trecho rodoviário em vez de reutilizar o cache anterior.
- Ao clicar em `Iniciar rota` ou em `A caminho`, o Connect recalcula somente a data e a equipe daquela etapa.
- Entram apenas entregas, retiradas e paradas na loja ainda pendentes.
- A ordem roteirizada manualmente é preservada; peso, capacidade e otimização automática continuam fora desse cálculo.

Commit sugerido:

`Connect 1.0.65 - ajusta tempos ponto a ponto e recalculo ao iniciar rota`

- Etapas já concluídas não reaparecem no cálculo, mas o último ponto concluído pode ser usado somente como origem física do próximo deslocamento, sem somar novamente seu tempo de serviço.
