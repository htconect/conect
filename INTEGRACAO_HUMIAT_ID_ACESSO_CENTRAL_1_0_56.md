# Connect 1.0.56 — acesso central Humiat ID

- Entradas de usuário e ADM passam pelo Humiat ID.
- Primeiro acesso termina no portal Humiat; com sessão ativa não pede senha novamente.
- Sessão do Connect limitada a 24 horas.
- "Esqueci minha senha" e recuperação apontam para o padrão central do Humiat ID.
- Usuários vinculados ao Humiat ID deixam de alterar senha local no Connect.
- Logout local retorna ao portal Humiat.
- Endpoint interno de logout permite ao Humiat encerrar a sessão Connect no logout global.
- Permissões operacionais internas do Connect permanecem inalteradas.
