# LokaFest 1.0.6

- Perfis criados/garantidos pelo Humiat passam a nascer **ativos e aprovados**.
- Remove a necessidade de aprovação manual do LokaFest para o fluxo vindo do Organiza/Humiat.
- Preenche automaticamente nome, CPF, WhatsApp, zona principal, equipamentos, pacote e categoria a partir do Organiza.
- Gera token de indicação já na criação do perfil.
- Mantém regiões adicionais livres para o usuário configurar depois, sem bloquear o acesso inicial.
- A rota de garantia é idempotente: se o perfil já existir, sincroniza os dados do Organiza e o libera.
- A criação falha de forma segura se o Organiza não puder ser consultado, evitando perfil incompleto.
