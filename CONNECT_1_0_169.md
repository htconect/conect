# Connect 1.0.169 — Frete único no total

## Escopo
- Introduz `_total_pedido_frete_unico()` em `app.py` como composição comum do valor comercial: **equipamentos e opcionais - desconto + horas adicionais + um frete único**.
- Aplica o cálculo comum à vitrine/precontrato, persistência do contrato, oportunidades e fluxo de aprovação e recálculo de rascunhos. O valor do frete continua vindo da configuração da empresa, sem qualquer multiplicação pela quantidade de equipamentos.
- Centraliza o total visual do carrinho em `totalPedidoVitrine()`, aplicado igualmente ao mini-carrinho e resumo final.
- Detalha no checkout “Frete único do pedido”.
- Corrige uma duplicação visual de opcionais na revisão do cadastro: antes, a linha de cada equipamento exibia `reg.valor_total` (que já incluía opcionais) e repetia os opcionais listados abaixo. Agora usa `reg.valor_base_total` na linha, com opcionais separados. Esse problema de visualização **não significava necessariamente dupla cobrança de frete**.
- Mantém a regra de ida e volta por KM, sem mudança de tarifa e sem mudanças em contratos históricos já fechados.

## Testes
- `python -m py_compile app.py config.py`
- `python -m pytest -q test_frete_unico_169.py` (10 aprovados)
- `python -m pytest -q test_vitrine_links_individuais_167.py test_vitrine_162.py test_vitrine_responsavel_retirada_166.py test_operacao_datas_165.py test_frete_unico_169.py` (40 aprovados)
- `test_frete_161.py` possui 1 teste antigo que falha na verificação de texto da fonte de geocodificação: espera `cep:` e recebe `osrm;origem_postal:brasilapi+brasilapi`; o valor do frete do teste está correto. Essa rotina não foi alterada.

## Validação em produção
1. Na vitrine do usuário, selecionar 1 equipamento de R$ 350 e calcular frete. O total antes do cupom deve ser 350 + frete.
2. Adicionar outro equipamento de R$ 300 no mesmo pedido, sem mudar CEP. O frete deve **permanecer idêntico** e o total aumentar apenas R$ 300.
3. Aplicar cupom e conferir que o desconto incide só sobre equipamentos/opcionais.
4. Conferir o mesmo total no carrinho, pré-contrato, contrato e valor proposto pela InfinitePay.
5. Se persistir uma diferença, registrar os 4 valores mostrados (itens, desconto, frete e total) e a etapa exata, sem enviar dados pessoais.

**Limitação:** as fórmulas existentes já somavam o frete uma vez em sua lógica normal. Sem um pedido real discrepante ou sessão reproduzível, esta revisão reforça e padroniza o cálculo, mas não prova a causa de toda reclamação em produção.
