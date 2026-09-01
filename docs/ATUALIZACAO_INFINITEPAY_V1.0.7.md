# Atualização InfinitePay — v1.0.7

## E-mail no checkout

Regra aplicada:

1. Se o cliente/contrato possui e-mail válido, o Conect envia `customer` com nome, e-mail e telefone para a InfinitePay.
2. Se não possui e-mail, o Conect não envia o bloco `customer`.
3. Se existe e-mail legado inválido, o bloco também é omitido para manter compatibilidade com contratos antigos.
4. O endereço nunca é enviado à InfinitePay.

## Compatibilidade

- Nenhuma coluna nova.
- Nenhum `NOT NULL` novo.
- Contratos antigos sem e-mail continuam abrindo.
- Novos cadastros continuam obedecendo à configuração de obrigatoriedade do e-mail.

## Correção adicional

Corrigida a montagem da mensagem de WhatsApp do contrato, que referenciava a variável `complemento` sem inicializá-la a partir do snapshot do endereço.
