# Conect 1.0.224 — cadastro de combo e bloqueio individual

- Bloquear um produto por data somente bloqueia a sua oferta; os combos que o utilizam continuam locáveis quando houver estoque físico suficiente.
- A composição continua consumindo os produtos principais e opcionais exclusivos do próprio combo.
- O cadastro trata erros de validação HTTP 422 e falhas de servidor HTTP 500 **sem sair da página ou apagar os campos preenchidos**; mostra a mensagem retornada pelo servidor ou orientação para consultar logs.
- Abre automaticamente a seção da operação quando um campo obrigatório está inválido.
- Salvar e **Aplicar a todos os itens** preservam os parâmetros do botão escolhido.
- Não cria tabelas, não apaga contratos nem altera registros existentes no PostgreSQL.

**Limitação:** esta versão melhora a recuperação e a mensagem do erro de salvamento, mas não é possível identificar com certeza um eventual erro 500 de produção sem a linha de exceção correspondente no log do Render. A atualização deve ser validada no ambiente real após o deploy.
