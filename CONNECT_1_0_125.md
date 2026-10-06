# Connect 1.0.125 — Cupons por fechamento e desconto fixo/percentual

## Alterações

- A validade do cupom passa a considerar a **data de fechamento/aplicação do cupom**, e não a data do evento.
  - Exemplo: um evento de Natal em dezembro pode receber o cupom se o contrato for fechado dentro da validade da campanha.
- Na Karaokê RJ, o cupom `KARAOKE10` fica com validade até **31/10/2026**.
- O cadastro de cupons agora permite escolher:
  - **Percentual (%)**; ou
  - **Valor fixo (R$)**.
- O desconto continua incidindo somente sobre equipamentos/opcionais elegíveis; o frete é somado depois.
- O contrato tradicional, a tela de equipamentos, a vitrine e os resumos financeiros passam a calcular e exibir corretamente os dois tipos de desconto.
- Contratos já fechados preservam o desconto aplicado mesmo se o evento ocorrer depois da data final da campanha.
- Mantida compatibilidade com a estrutura atual do banco, sem necessidade de nova coluna/migração para o tipo de cupom.

## Compatibilidade interna

Para evitar migração estrutural nesta versão, o campo histórico `percentual` mantém percentuais positivos e representa valor fixo por valor negativo internamente. A interface sempre apresenta o tipo e o valor de forma normal ao usuário.
