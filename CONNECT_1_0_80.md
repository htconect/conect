# Connect 1.0.80

- Aceita valor zero na integração de saldos do Organiza, permitindo zerar um saldo anteriormente aberto.
- Continua bloqueando valores negativos.
- Passa a aceitar os tipos globais `atualizacao` e `estoque`, além de `venda` e `manutencao`.
- Mantém idempotência por `id_externo`, atualizando o saldo existente sem duplicidade.
