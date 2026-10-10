# Connect 1.0.156 — Recuperação segura de links antigos de contratos

- Links legados `/e/<slug>/contrato/<id>` e `/e/<slug>/contrato/<id>.pdf` passam a abrir uma tela de confirmação por CPF/CNPJ completo do cadastro e redirecionam para o link atual com token privado.
- Equipe autenticada no Connect (mesma empresa) ou administrador geral vai diretamente ao contrato/PDF atual.
- Links numéricos de `/pedido/<id>` também são recuperados para o contrato atual.
- Respostas sem informações sensíveis antes da confirmação; tentativas limitadas a 8 a cada 10 minutos por IP; sem armazenamento ou envio de CPF/CNPJ na URL.
- Nenhum contrato, pagamento, aceite, cliente ou estoque é alterado; somente token público pode ser gerado para registro antigo que ainda não tenha um.
- Se o cadastro antigo não tem CPF/CNPJ, a recuperação automática não pode comprovar a titularidade: a equipe deve fornecer o link atual privado pelo painel.
- `CONECT_LEGACY_PUBLIC_CONTRACT_IDS` não é mais usado para abrir IDs livremente. Deixe `false` no Render.

Commit sugerido: `v1.0.156 - Restaura links antigos de contratos com validacao segura`
