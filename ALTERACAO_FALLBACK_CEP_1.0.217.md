# Conect 1.0.217 — Fallback de frete por CEP sem número identificado

## Problema
O CEP 20735-080 é localizado pelo Google Maps, mas um número informado (ex.: 303) pode não existir na base do Google. Na tentativa com CEP + número, a rota fica parcial ou sem quilometragem segura. A versão 1.0.216 pode deixar o frete pendente nesses casos.

## Implementação
- A primeira tentativa permanece com rua, CEP, cidade, UF e número.
- Se a resposta do Google contiver correspondência parcial, só aceitar a distância **viária** quando o destino estiver próximo (até 2,5 km) da coordenada postal do CEP consultado em fonte independente, com município e UF conferidos no ViaCEP.
- Se falhar, uma segunda tentativa consulta **apenas CEP + cidade/UF** na Routes API e também valida a chegada contra a referência postal independente. Não usa linha reta nem aproximação arbitrária.
- Frete = distância efetiva de ida e volta, usando o valor/km configurado na empresa; o número do cliente nunca muda o preço manualmente.
- Rotas por CEP e respostas parciais aprovadas são exibidas como **frete estimado pelo CEP**, com número do endereço **não confirmado**. Esse alerta é mantido no carrinho e nas observações do contrato para conferência antes de entrega.
- Se o CEP não for validado ou as coordenadas postais independentes estiverem indisponíveis/divergentes, mantêm-se o fluxo seguro de **pedido pendente**, sem frete inventado.
- Preservadas todas as correções 1.0.213–1.0.216 (WhatsApp global, opcionais, retirada, frete público).

## Testes
- Rota por endereço parcial divergente + CEP validado próximo -> calcula distância da rota por CEP e sinaliza o número.
- Rota exata -> calcula normalmente, sem consultas adicionais e sem alerta.
- Rota parcial próxima -> calcula e mantém aviso sobre número não confirmado.
- CEP distante, coordenadas divergentes ou fontes indisponíveis -> permanece pendente.
- Alteração de frete manual pelo cliente segue bloqueada.

## Limite
A rota pelo CEP é uma **estimativa**, não confirmação do número da porta. O atendimento deve confirmar número/complemento/ponto de referência para fazer entrega. Os testes são simulados; validar o Google em produção para o CEP e número informado após publicar.
