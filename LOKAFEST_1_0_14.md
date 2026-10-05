# LokaFest 1.0.14

- Adiciona **Carregar dados de todos** na tela Administração > Usuários.
- A atualização do Organiza é totalmente manual: nenhuma consulta externa ocorre ao abrir a lista.
- A carga é feita em pequenos lotes pelo navegador e exibe progresso.
- Quando o Organiza confirma que um cliente não possui mais vínculo atual, o cache antigo de equipamentos é zerado, evitando manter aptidão após transferência.
- A lista passa a exibir explicitamente **Humiat ID: Sim/Não** usando apenas `usuarios.humiat_user_id` do banco local do LokaFest.
- Não há consulta ao Humiat para montar a tela de usuários.
