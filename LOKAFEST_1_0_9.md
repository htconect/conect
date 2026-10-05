# LokaFest 1.0.9

- Corrige o SSO do Humiat ID para reutilizar o usuário LokaFest já existente em vez de mandar um administrador conhecido para o cadastro público.
- Conciliação de identidade na ordem: `humiat_user_id` -> e-mail -> CPF -> WhatsApp (fallback legado).
- Adiciona `usuarios.humiat_user_id` e `usuarios.email` como campos opcionais, com migração automática sem apagar dados existentes.
- No primeiro acesso bem-sucedido pelo Humiat, grava o vínculo central; nos próximos acessos resolve diretamente pelo `humiat_user_id`.
- Não altera `is_admin`, `ativo`, `aprovado`, créditos, zonas, categorias nem histórico do usuário existente.
- Impede que um perfil LokaFest já vinculado a um Humiat ID diferente seja relinkado silenciosamente.
- Administrador existente autenticado pelo Humiat entra em `/painel`, igual ao login próprio do LokaFest.
