# Conect 1.0.216 — Frete seguro / Vitrine

## Motivo
O Google Routes devolvia distância, mas indicava endereço parcial (`geocodingResults.destination.partialMatch = true`). A versão anterior descartava a rota inteira; a tela pública obrigava o cliente a digitar um valor e o servidor aceitava esse valor como frete manual.

## Ajustes
1. Na vitrine, removido completamente o campo e o botão de valor de frete manual. Requisições com um `frete_manual` artificial não alteram o orçamento: o servidor sempre obtém frete por cálculo próprio, não pelo formulário.
2. Em rotas parciais, só aceitar a distância **real de via pública** informada pelo Google se o destino tiver placeId e tipo compatível com endereço; a origem deve ser exata; CEP deve ter sido validado via ViaCEP e a coordenada de chegada da rota deve estar a até 2,5 km de coordenada postal obtida de BrasilAPI/AwesomeAPI, com cidade e UF confirmadas. Sem essa confirmação, continuar com frete pendente. Nunca cobrar por distância em linha reta.
3. O cliente pode enviar uma **solicitação pendente de frete**, sem valor inventado e sem criar contrato, para aprovação no painel existente.
4. Apenas operador autenticado pode aprovar o valor pendente no painel. A aprovação exige valor maior que zero.
5. Preservadas correções de WhatsApp/navegação (1.0.215), opcionais e retirada/horas (1.0.214 e 1.0.213).

## Fluxo de teste
- Na vitrine, informar CEP 20735-080 com número, calcular deslocamento e conferir valor, distância da ida/volta, e total do pedido.
- Se a rota continuar pendente por falta da coordenada de referência ou Google Routes, clicar **Enviar pedido para aprovar frete**. Conferir que nenhum contrato é criado e que a oportunidade aparece no painel de fretes pendentes.
- No painel aprovar com valor manual positivo e então retomar o carrinho pelo mesmo link.
- Testar POST com campo arbitrário `frete_manual`: jamais pode sobrescrever frete calculado, nem tornar `consultar` em aprovado.

## Limite
A captura da imagem do Google Maps não permite recuperar a resposta real da API do servidor. A correção foi validada com testes simulando as respostas do Google e dos provedores de CEP; é necessário conferir em produção com o mesmo CEP após o deploy. A API postal pode estar indisponível e então o sistema manterá o frete pendente.
