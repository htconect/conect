# Connect 1.0.162 — Busca CEP e compartilhamento da vitrine

- Modal de frete mantém CEP como padrão e permite busca por UF, cidade e logradouro via ViaCEP, com filtro opcional de bairro. O cliente escolhe um resultado e informa número antes de calcular.
- Botão Compartilhar vitrine envia data, categoria, CEP/número, equipamentos, quantidades, opcionais, cupom, início e retirada. Link temporário assinado, sem dados pessoais.
- Ao abrir, revalida disponibilidade, frete e cupom e não cria contrato.
- Rotas 0 km para CEPs diferentes são rejeitadas e recalculadas com referências postais independentes; não autoriza cobrança com percurso zerado.
