# Connect 1.0.159 — guia fixo e destaque das ações da vitrine

Base: Connect 1.0.158. Não altera as regras de CEP, contratos, operação ou pagamentos.

## Orientação visual
- Card de **próximo passo** fica visível no topo enquanto o usuário rola a vitrine (CSS `position: sticky`). Produtos e carrinho aparecem abaixo dele.
- Card mais chamativo: borda na cor configurada da empresa, título, texto contextual, botão de ação e barra de seis etapas.
- Etapas: confirmar data, confirmar tipo de evento, calcular frete (ou ver produtos), escolher equipamento, conferir opcionais/horário e revisar pedido. As confirmações iniciais são gravadas apenas na sessão do navegador e não criam dados no banco.
- Campo relacionado à ação atual recebe borda/pulsação suave por poucos segundos, permanecendo destacado após a animação. Respeita `prefers-reduced-motion`.
- `Ver produtos` vai até o primeiro card de produto visível (respeitando filtros), com deslocamento vertical que evita esconder o card atrás do guia fixo. `Continuar comprando` usa a mesma navegação.
- Frete pode continuar sendo calculado depois da escolha dos equipamentos; ao finalizar ele continua obrigatório e validado pelas regras da 1.0.158.
- Nenhum bloqueio novo ao processo de reserva e nenhuma nova etapa de backend.

## Testes realizados
- Sintaxe Jinja da vitrine e JavaScript validada.
- Navegação no Chromium em larguras de 320, 375, 430 e 820 px, sem rolagem horizontal.
- Sequência de data, tipo, pular frete, ver primeiro produto, adicionar e conferir opcionais/horário testada no navegador local, sem exceções de JavaScript.
- Ambiente de produção/Render não alterado.
