# Connect v1.0.59 — Cupons, frete e composição comercial

## Regras implementadas

- Cadastro de cupons por empresa em **Cadastros > Cupons**.
- Cupom inicial da Karaokê RJ: **KARAOKE10**, com 10% de desconto, válido até **30/09/2026**.
  - A data solicitada como 31/09/2026 foi normalizada para 30/09/2026, pois setembro tem 30 dias.
  - A validade considera a data em que o cupom é aplicado ao contrato, não a data do evento. Portanto, um evento em dezembro pode receber o desconto se o contrato for fechado durante a campanha.
  - Uma condição já aplicada fica preservada no contrato mesmo depois do encerramento da campanha.
- O valor comercial do contrato passa a ser armazenado separadamente em:
  - valor dos equipamentos;
  - código e percentual do cupom;
  - valor do desconto;
  - frete;
  - total líquido final.
- O desconto incide **somente sobre os equipamentos**. O frete é somado depois.
- Ao selecionar um equipamento, o valor base cadastrado é carregado automaticamente e continua editável.
- A composição aparece no registro de pagamento, no contrato público/PDF e nos resumos enviados pelo WhatsApp.
- A regra de composição é global para todas as empresas do Connect. Cada empresa mantém seus próprios cupons.
- Cópias e transferências de contratos preservam a composição comercial.
- O total líquido final continua em `solicitacoes.valor` para manter compatibilidade com Financeiro e InfinitePay.

## Exemplo

Equipamentos: R$ 850,00  
Cupom KARAOKE10: - R$ 85,00  
Frete: R$ 100,00  
**Total: R$ 865,00**
