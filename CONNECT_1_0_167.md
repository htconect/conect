# Connect 1.0.167 — links individuais curtos da vitrine

Base: Conect(20261014-134527).zip, com correções da 1.0.166 preservadas.

- Link pessoal: `/e/{slug}?u={codigo}` (código curto estável calculado a partir do token pessoal persistido).
- `/painel/vitrine`: links de cada atendente com WhatsApp ativo e botões Copiar. `/painel/perfil`: meu link individual.
- `?u` identifica o usuário ativo dentro da empresa e recupera seu WhatsApp do cadastro, sem expor número na URL. Sem `?u`, não atribuir automaticamente um atendente.
- Links legados `?r=TOKEN` continuam funcionando. Cliente mantém responsável na seleção da data, vitrine, carrinho, cadastro, contrato e envio.
- Link público genérico recorre apenas ao WhatsApp institucional de retorno, se cadastrado. Não envia indevidamente para um funcionário.
- Link inválido ou de usuário sem WhatsApp retorna aviso 404 em vez de criar contrato com destinatário errado.
- Nenhuma migração adicional do banco para esta mudança; telefone reflete alterações feitas no cadastro.
- Versão 1.0.166: edição de retirada obrigatória e correção manual de responsável preservadas.
