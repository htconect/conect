# Conect 1.0.184 — Frete Google Routes e WhatsApp para período

- Frete por quilômetro agora consulta a Routes API do Google, usando endereço completo da loja e do cliente, com alternativas de trajetos de carro. Cobrança usa menor distância rodoviária retornada, ida × 2 e valor/km cadastrado.
- Sem chave do Google, endereço completo de origem ou rota válida, bloqueia cotação automática e encaminha para aprovação de frete sob consulta, sem voltar para OSRM nem linha reta.
- Novo campo em Empresa: **Endereço de partida completo**, incluindo rua e número, para cada empresa; com migração aditiva na tabela empresas.
- Variável no Render: `GOOGLE_MAPS_API_KEY` (obrigatória), `GOOGLE_MAPS_ROUTES_TRAFFIC_AWARE=true` (Pro, opcional; false usa Essentials).
- Reserva por período: formulário abre compartilhamento em nova aba, com botão manual e cópia do link como alternativa caso o navegador impeça a abertura do WhatsApp.
- Compartilhamento de oferta por período na vitrine pública agora está disponível e preserva o link original, sem perder datas/preço.
- Não houve alteração na configuração existente de preço/km, nem na fórmula comercial de ida e volta.
- **Antes de publicar:** habilitar Routes API no Google Cloud, configurar chave segura no Render, cadastrar endereço completo da loja nas duas empresas que usam frete por km e verificar o CEP de origem.
- Confirmar que o Google Maps no teste está configurado com a *mesma origem cadastrada*, não simplesmente 'Seu local'.

## Verificação financeira antes do deploy

- Na captura de tela, o Google Maps partia de **Seu local**, que pode não ser o endereço cadastrado no Connect. Configure no Maps **o endereço da loja** como origem e compare com a mesma rua, número e CEP.
- Exemplo com a rota Google de 46,5 km e tarifa R$ 1,50/km: `46,5 × 2 × R$ 1,50 = R$ 139,50` (sem pedágios adicionais). Antes eram `13,1 × 2 × R$ 1,50 = R$ 39,30`.
- A rota do Google só é aceita quando origem e destino são geocodificados sem correspondência parcial. Caso contrário, o frete exige consulta.
- O sistema **não** foi implantado no Render; testes efetuados sem chave real de produção.
