# Connect 1.0.158 — mobile, CEP e orientação na vitrine

- **Contratos e reservas no celular:** filtro de busca em linha inteira, datas em duas colunas flexíveis, situações compactas e ações Filtrar / Limpar filtros sem transbordamento. CSS limitado à página de contratos, preservando a Operação.
- **Cálculo de deslocamento:** exige CEP com exatamente 8 dígitos, confirmado como existente via ViaCEP **antes de qualquer tipo** de frete (fixo, km ou sob consulta). Não calcular ou prosseguir com valor quando CEP não existe ou a consulta está indisponível. Falhas temporárias não são armazenadas no cache de CEP. O servidor também valida ao reservar.
- **Vitrine pública:** instruções dinâmicas e curtas: data > Residencial/Empresa > frete (agora ou mais tarde) > equipamento > opcionais no carrinho > horário > revisar e reservar. Botão de contexto leva à área correta sem páginas adicionais e respeita o fluxo Vitrine → Contrato → Pagamento. Se pagamento online estiver desativado, o fluxo termina no Contrato.
- **Frete não confirmado:** exibir “A calcular”, não R$0,00; quando CEP/número mudam, limpar valores anteriores e pedir novo cálculo. Mensagem de erro no modal para CEP inválido.

**Observação:** CEP continua sendo solicitado no cálculo do frete (atalho no catálogo ou dentro do carrinho), não no formulário inicial, e opcionais permanecem no carrinho.
