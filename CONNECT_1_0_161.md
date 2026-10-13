# Connect 1.0.161 — Correção do cálculo de frete com CEP existente

Base: Connect 1.0.160 (mantém orientações da entrada, vitrine, cadastro, contrato e pagamento).

## Causa

O cálculo por KM confirmava a existência do CEP via ViaCEP, mas a etapa posterior de geocodificação podia retornar coordenadas de outro município. A trava de proteção para rotas superiores a 300 km entre endereços da mesma cidade impedia cobrar frete absurdo, porém devolvia erro mesmo para CEP existente, como 21911-280 (Rua General Edgardino Pinta, Freguesia/Ilha do Governador, Rio de Janeiro/RJ).

## Correção

- Se o trajeto inicial dentro da mesma cidade for incoerente (>300 km), ou se não houver rota, procurar referências de latitude/longitude associadas ao CEP na BrasilAPI CEP v2, com AwesomeAPI como alternativa.
- Conferir que o CEP, município e UF do serviço alternativo são os mesmos confirmados no ViaCEP. Coordenadas inválidas ou discordantes são rejeitadas.
- Recalcular a distância rodoviária com as coordenadas de referência (correção automática de origem e destino).
- Se a rota corrigida também for incoerente, **não cobrar preço inventado**; informar que o CEP foi confirmado, mas não foi possível validar a rota.
- CEP de 8 dígitos não existente no ViaCEP continua bloqueado; nenhuma mudança em pagamentos, contratos, cupons ou demais tipos de frete.
- Cachear só coordenadas postais confirmadas; falhas de serviços são temporárias e poderão ser tentadas novamente.
- Registrar em logs da Render a identificação da rota suspeita e a recuperação ou rejeição do cálculo.

## Verificação local (offline)

Testes simulados: (1) CEP existente com rota de 640 km recuperada para 18,5 km, (2) CEP inexistente bloqueado, (3) indisponibilidade dos serviços sem cobrança, (4) frete normal sem dependência adicional, (5) rejeição de cidade divergente, (6) cache apenas para referências válidas. Compilação do código Python concluída.

A API real de geocodificação/distância e a produção no Render não foram testadas nem alteradas; requer implantação e conferência do CEP 21911-280, número 135, com a origem real da empresa.
