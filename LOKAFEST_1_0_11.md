# LokaFest 1.0.11

- Exibe a versão do sistema no rodapé.
- Usuários com `humiat_user_id` local exibem o selo Humiat ID sem consulta externa.
- Recebe o Humiat ID por evento no momento da aprovação no Humiat.
- Revalidação do Organiza usa primeiro o `cliente_id` salvo quando disponível.
- Administração pode pesquisar por número técnico da máquina, por exemplo `KRJ00786`.
- Falha de uma nova consulta não apaga nem mistura o cache anterior da validação.
