# Git / Render — Connect 1.0.171

1. Extraia o ZIP completo sobre a pasta do projeto, preservando configurações locais e banco de dados.
2. Na raiz do repositório, execute:

```bash
git add .
git commit -m "fix(connect): v1.0.171 opcionais e recursos nos cards da operacao e agenda"
git push origin main
```

3. No Render, com Auto Deploy ativado, acompanhe o deploy do commit; caso contrário, publique manualmente esse commit.

## Conferência depois da publicação

- Abrir o contrato #206 e conferir o Catálogo Encadernado e demais opcionais em **Opcionais para separar**, além dos recursos físicos efetivos.
- Na Agenda e na Operação, verificar os cards da mesma reserva e as quantidades de opcionais e recursos.
- Em **Operação → Estoque do dia**, conferir avisos de vínculos do contrato e dos opcionais ativos do catálogo.
- O relatório é de leitura; nenhum histórico ou vínculo antigo será regravado automaticamente.

Testes: 50 aprovados, 1 falha antiga no teste textual da fonte da geocodificação do frete.
