# Conect 1.0.180 — Ativação de brindes para duas empresas

- Ativa `utiliza_brinde` para Karaokê RJ e Viviokê por migração única ao iniciar o Conect.
- A migração usa `app_migrations` para não reativar o campo em deploys futuros se o administrador desmarcá-lo.
- Não modifica as configurações de outras empresas, estoque, contratos ou opcionais.
- A função é um controle administrativo: não implementa nem replica regras automáticas de brinde.
- Aplicar esta versão após a 1.0.179 (incluída no pacote).
