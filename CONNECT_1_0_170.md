# Connect 1.0.170 — InfinitePay mobile e auditoria de estoque da Operação

## Ajustes

1. **InfinitePay no celular:** corrige o cartão das cobranças que espremia o valor e o status em uma coluna com uma letra por linha. O valor permanece legível, e os botões ocupam a largura disponível no telefone.
2. **Relatório `Operação → Estoque do dia`:** disponível em `/painel/reservas/consumo-estoque`, filtrável por data. Mostra em equipamentos e recursos:
   - total de unidades cadastradas;
   - unidades na rua *agora* (entregas concluídas sem retirada concluída);
   - saldo estimado na loja *agora*;
   - saídas agendadas na data selecionada;
   - unidades ainda a preparar para as entregas não concluídas;
   - saldo após preparação e faltas.
3. **Opcionais:** corrigida a rotina `_analises_estoque_lote` para incluir o estoque consumido pelo snapshot `SolicitacaoOpcional` vinculado ao recurso físico (1:1). Antes, esse cálculo em lote considerava apenas recursos dos equipamentos, provocando divergências em telas que usam a análise agrupada.
4. **Auditoria de opcionais:** lista alertas para opcionais sem recurso vinculado e ajustes manuais que alteraram a quantidade base. Não altera silenciosamente os contratos antigos.
5. **Cache CSS:** o endereço das folhas de estilo passa a usar a versão do app.

## Regras de estoque e limites

- A quantidade cadastrada é o *total operacional*; a consulta é somente leitura e **não dá baixa permanente na quantidade mestre**.
- "Na rua agora" exige Entrega concluída e ausência de Retirada concluída na Operação. Considera também contratos cancelados depois da entrega, porque cancelar não prova que o equipamento foi devolvido.
- Não antecipa uma retirada ainda pendente como entrada na loja.
- "Saídas da data" segue a *data da entrega na Operação*, não necessariamente a data do evento no contrato.
- Ajustes manuais de recursos continuam sendo respeitados; a auditoria mostra quando o efetivo é diferente do padrão.
- Opcionais de contratos antigos sem `item_estoque_id` permanecem sem desconto físico até que sejam revisados; aparecem nos alertas.
- O relatório não é inventário físico: o resultado depende dos registros corretos de entrega e retirada.

## Validação

- Testes específicos v1.0.170: 5 aprovados.
- Suíte total: 50 aprovados; 1 falha preexistente em `test_frete_161.py` por texto da origem de geocodificação (espera `cep:` mas recebe `origem_postal:...`). Não afeta o cálculo de saldo.
- Não foram feitas alterações no banco de produção nem implantação no Render.
