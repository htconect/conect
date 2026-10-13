# Connect 1.0.160 — guia desde a entrada até o contrato

Base: Connect 1.0.159.

- Entrada: mostra SOMENTE os passos 1 e 2 (data e tipo de evento); botão **Entrar na vitrine** habilitado após escolher ambos. Destaque no campo da etapa atual.
- Vitrine: começa em **passo 3 de 6 — Calcular o frete**, com escolha flexível de produtos e opcionais. Não exige confirmar data/tipo novamente.
- X para ocultar orientação em todas as telas e botão **Mostrar orientações** para reabrir; preferência temporária compartilhada entre as telas da empresa na mesma aba.
- Cadastro do contrato: orientação fixa por seção (quem reserva, endereço, evento e responsável no local).
- Contrato: orientação por seção de conferência dos dados, locação, cláusulas, valores, horário e aceite. Botões abrem seções recolhidas; aceite não é bloqueado pelo guia.
- Pagamento após aceite: guia para continuar e escolher a forma de pagamento existente, sem mudanças no fluxo bancário.
- Respeita movimento reduzido, mantendo navegação manual e cores da empresa.
- O X tem caractere visível mesmo sem carregar a biblioteca de ícones.

## Verificações locais
- Templates Jinja compilados, JavaScript validado via Node e cinco páginas renderizadas em Chromium.
- Sem rolagem horizontal nas larguras 320, 375, 430 e 820 px.
- Entrada: habilitação do botão Entrar após data e tipo, fechamento e reabertura.
- Vitrine: início no frete, navegação ao primeiro produto, X e reabertura.
- Cadastro: navegação para a próxima seção e X/reabertura.
- Contrato: abertura e progressão das seções. Pagamento: passagem de contrato aceito para formas de pagamento.
- Não houve publicação no Render nem testes com dados reais de produção.
- Sem alterações no banco de dados, cálculo de frete ou pagamentos.
