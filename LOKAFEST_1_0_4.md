# LokaFest 1.0.4

- Adiciona API protegida para listar usuários na migração inicial para o Humiat ID.
- Adiciona API protegida para o Humiat criar somente o pré-cadastro quando o usuário ainda não existe.
- O pré-cadastro reaproveita CPF/WhatsApp e tenta carregar automaticamente equipamentos e catálogo pelo Organiza.
- O Humiat pode informar a zona principal inferida pelo endereço do cliente.
- Usuário pré-cadastrado pelo Humiat pode entrar via SSO mesmo antes de ficar apto e é direcionado para Meu Cadastro.
- Ao concluir a primeira configuração das áreas, se já houver categoria principal, o cadastro é liberado.
- Senha local aleatória do pré-cadastro nunca é enviada; o acesso normal é pelo Humiat ID.
