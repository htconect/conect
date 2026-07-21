# Evolução — Pendência de Envio de Contrato

## Objetivo
Garantir que todo contrato aprovado/aceito continue visível no painel até o envio do contrato final ao cliente pelo WhatsApp.

## Decisões aprovadas
- Reutilizar integralmente o fluxo já existente de envio do contrato pelo WhatsApp.
- Não criar um novo conteúdo ou tratamento de contrato.
- Criar no painel a pendência **Pendência de Envio de Contrato**.
- A pendência considera reservas com contrato nos status `aceito`, `aguardando_pagamento` ou `reserva_confirmada`.
- Ao clicar em **Enviar contrato**, o sistema usa a rota existente `/whatsapp-contrato`.
- O clique registra `contrato_enviado_em` e remove o item da pendência sem alterar o status operacional/financeiro da reserva.
- Contratos antigos já aprovados e ainda sem registro de envio aparecem automaticamente na nova pendência após a migração.

## Arquivos alterados
- `models.py`
- `app.py`
- `templates/admin/painel.html`
- `static/css/style.css`

## Banco de dados
Nova coluna em `solicitacoes`:
- `contrato_enviado_em TIMESTAMP NULL`

A migração automática do projeto cria a coluna quando ela ainda não existir.
