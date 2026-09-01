# InfinitePay no HUMIAT Conect — v1.0.4

## Mensagem de aceite por empresa
- Se `infinitepay_ativa` estiver habilitada, a mensagem enviada ao cliente não inclui a chave PIX manual.
- O cliente é orientado a aceitar o pré-contrato e, em seguida, escolher **Sinal** ou **Valor integral**.
- O pagamento é concluído na InfinitePay por PIX ou cartão e a confirmação é processada automaticamente; não é solicitado comprovante.
- Se InfinitePay estiver desabilitada, o fluxo manual anterior permanece disponível, inclusive a instrução de PIX quando `exige_sinal` estiver ativa.

## Correção da pré-tela mobile
O seletor de opção herdava `width:100%` do CSS global de inputs e empurrava o título/valor para fora do card em telas estreitas. O rádio agora tem largura fixa e os textos de **Sinal** e **Valor integral** permanecem visíveis.

## Fluxo após pagamento
O comportamento da v1.0.3 foi preservado: pagamento confirmado gera pagamento e lançamento na conta InfinitePay, concilia automaticamente, aprova o contrato e abre o WhatsApp do responsável com a mensagem pronta para o cliente tocar em **Enviar**.
