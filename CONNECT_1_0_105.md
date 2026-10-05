# Connect 1.0.105

- Restaura **Contratos** no menu principal, entre Disponibilidade e Agenda, apontando para `/painel/solicitacoes`.
- Mantém **Política / modelos** separado em Cadastros.
- Corrige erro **422** ao subir/descer opcionais: o carregamento global agora preserva `name/value` do botão que disparou o formulário antes de desabilitá-lo.
- A mesma correção protege outras telas com botões de ação nomeados, como ordenação de categorias/produtos.
- Startup padrão passa a ser leve: migrações/manutenções automáticas ficam desativadas por padrão, já que a base de produção está migrada.
- Para manutenção excepcional, usar `CONNECT_RUN_STARTUP_MAINTENANCE=1` temporariamente.
- Adiciona `/health` e resposta `HEAD /` 200 para health checks sem gerar 405.
