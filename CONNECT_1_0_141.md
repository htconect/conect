# Connect 1.0.141 — Correção de links de cadastro e cancelamento InfinitePay

- Cancelamento administrativo de cobrança: busca solicitação pelo ID inteiro e empresa autenticada (em vez de tentar usar ID como token público). Cobrança também é validada pela empresa e solicitação.
- Mantém histórico de cobranças e proibição de cancelar pagamento confirmado. Cancelar no Connect significa encerrar cobrança **localmente**; eventual pagamento feito pelo checkout antigo ainda pode ser conciliado pelo webhook.
- Link de cadastro enviado por WhatsApp: quando a solicitação já avançou para contrato, redireciona ao link permanente de contrato (somente com contrato e itens existentes).
- Pré-reserva ainda pendente ou em situação incompatível: informa o estado com mensagem adequada e HTTP 409, sem tornar editável um contrato já avançado ou cancelado.
- POST de formulário antigo do cadastro repete a proteção contra reabertura e duplicidade.
- Sem alteração de modelos, schema, conciliação, regras de preço ou estoque.

## Validação em produção
1. Pré-reserva pendente: mostrar aviso, sem formulário nem 404 indevido.
2. Pré-reserva aprovada, ainda em rascunho: cadastro disponível.
3. Cadastro já concluído, contrato emitido: link antigo leva ao contrato, sem alterar registro.
4. Pedido cancelado/indisponível: não oferecer cadastro ou aceite novo.
5. Cancelar cobrança InfinitePay AGUARDANDO_PAGAMENTO pela tela de solicitação: alterar somente status local e liberar nova; preservar histórico.
6. Cobrança paga ou de outra solicitação/empresa: nunca cancelar.
7. Confrontar logs dos POSTs de cancelamento (esperado HTTP 303) e dos GETs da pré-reserva.
