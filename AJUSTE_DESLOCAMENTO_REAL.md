# Ajuste de deslocamento real da Inteligência

- Distância entre paradas calculada por ruas com OSRM.
- Tempo operacional recebe margem urbana para não usar duração livre de trânsito como previsão final.
- Fallback conservador quando o provedor de rotas estiver indisponível.
- Velocidade configurada não pode gerar estimativa urbana acima de 25 km/h no fallback.
- A prévia mostra distância do trecho, tempo de deslocamento, instalação e horário em que o equipamento estará pronto.
- Os minutos de instalação continuam separados do deslocamento e são somados depois da chegada.

Variáveis opcionais do Render:

- `ROTA_FATOR_TRAFICO=1.35`
- `ROTA_MARGEM_URBANA_MIN=3`
