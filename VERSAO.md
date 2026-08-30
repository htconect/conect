# HUMIAT Conect — Versão 1.0.2

Data: 30/08/2026

## Alterações
- Card **Operação > Destino** mostra exatamente o mesmo texto enviado ao Waze/Google Maps.
- Destino de navegação formado somente por **logradouro + número + bairro + CEP**.
- Complemento (apartamento, bloco, sala etc.) não aparece no Destino e não é enviado à navegação.
- Waze volta temporariamente a usar endereço textual `q=` para permitir comparação direta em produção.
- Latitude/longitude não são usadas pelo botão **A caminho / Iniciar rota** nesta versão diagnóstica.
- Google Maps recebe a mesma string textual do card.
- Mantida a independência do endereço por contrato/evento.

## Commit padrão
`v1.0.2 - iguala destino do card ao Waze Maps com bairro e CEP`
