# Connect 1.0.55 — Humiat ID

- Usuários existentes do Connect passam a aceitar vínculo por `humiat_user_id`.
- O vínculo é feito sem duplicar usuário: primeiro pelo ID já salvo, depois pelo mesmo e-mail/login e, por último, por telefone único.
- O e-mail do Humiat ID pode ser informado no ADM Connect ao editar o usuário existente; ao salvar, o Connect valida no Organiza e já grava o ID central.
- `modo=sistema` preserva as permissões locais de Agenda, Operação, Financeiro, Cadastros e Relatórios.
- `modo=adm` com empresa entra como administrador daquela empresa; equipe interna sem empresa entra no ADM global.
- O slug recebido pelo Humiat precisa existir no Connect exatamente igual; o Connect não cria empresa automaticamente.
- Login direto `/empresa/login` e `/admin/login` vai ao Humiat ID quando o SSO está configurado. `?local=1` mantém o login legado apenas como contingência de migração.
