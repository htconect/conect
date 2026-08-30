# HUMIAT Conect v1.0.1 — Waze por coordenadas

## Motivo
O Waze aceita endereço textual em `q=`, porém navega para o primeiro resultado da pesquisa. Isso pode selecionar estabelecimento (POI), rua ou número diferente do contrato.

## Correção
- Quando a solicitação possui latitude/longitude com `status_geocodificacao=localizado`, o Waze recebe `ll=latitude,longitude&navigate=yes`.
- Android e iOS usam o mesmo critério nos deep links.
- Se não houver coordenadas confirmadas, permanece fallback `q=<endereço do contrato>`.
- Complemento não participa mais da geocodificação nem da busca do Waze/Maps.
- O endereço de exibição continua vindo exclusivamente do contrato.

## Compatibilidade
Nenhuma coluna é removida ou alterada. Não há nova migração de banco nesta versão.
