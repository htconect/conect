# Connect 1.0.65 — tempos da Operação manual

A Operação passa a usar os parâmetros já existentes na Inteligência apenas como fonte de tempos, sem deixar a Inteligência escolher ou reorganizar a rota.

## Regras

- Equipe tempo = somente deslocamento real/rodoviário entre os dois pontos consecutivos.
- Tempo de chegada = deslocamento + serviço da etapa anterior.
- Entrega concluída na etapa anterior acrescenta o parâmetro de instalação.
- Retirada concluída na etapa anterior acrescenta o parâmetro de desmontagem.
- Parada na loja acrescenta apenas o parâmetro de parada na loja à próxima etapa.
- Ao iniciar a rota, recalcula somente o dia/equipe do card e apenas o que ainda falta entregar, buscar/retirar ou cumprir como parada na loja.
- Não usa peso, capacidade do veículo, compartimentos ou otimização automática.

- Etapas já concluídas não reaparecem no cálculo, mas o último ponto concluído pode ser usado somente como origem física do próximo deslocamento, sem somar novamente seu tempo de serviço.

## Localização

O cálculo tenta geocodificar a loja e os contratos pendentes antes de usar a estimativa sem coordenadas. O trecho rodoviário é recalculado sem reutilizar o cache anterior quando o cálculo parte da Operação manual.

Versão: `1.0.65`
