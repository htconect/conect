# Connect 1.0.107

- Corrige deploy do Render: migração única de preços da 1.0.106 não bloqueia mais o startup/abertura da porta; roda em background e continua protegida por `app_migrations`.
- Otimiza a migração de preços removendo consultas N+1.
- Corrige cálculo de frete por KM: CEP de origem passa a ser geocodificado primeiro pelo endereço completo do ViaCEP, evitando coordenadas erradas ao consultar somente o CEP.
- Adiciona trava de segurança para não cobrar rota absurda quando origem e destino são do mesmo município/UF e a geocodificação retorna distância incompatível.
- Mantém a regra de frete: distância rodoviária de ida × 2 × valor por KM.
