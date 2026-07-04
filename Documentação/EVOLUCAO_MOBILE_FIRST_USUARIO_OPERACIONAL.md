# EVOLUCAO_MOBILE_FIRST_USUARIO_OPERACIONAL

## Objetivo
Refazer a experiência principal do Conect pensando em uso quase 100% no celular.

## Decisões aplicadas
- Layout mobile-first, não desktop reduzido.
- Navegação inferior com atalhos principais.
- Home operacional com Agenda, Preparação, Financeiro e Busca de Cliente.
- Modo Cliente virou consulta por CPF/telefone para listar reservas do cliente e reenviar contrato.
- Uso de accordions para economizar tela.
- Histórico operacional simples, apenas ações importantes.
- Pagamento registra automaticamente o usuário do sistema logado.
- Correção conservadora dos valores inflados mantida no startup.

## Entregas
- `templates/base.html`
- `templates/admin/painel.html`
- `templates/admin/agenda.html`
- `templates/admin/clientes.html`
- `templates/admin/cliente_detalhe.html`
- `templates/admin/solicitacao_detalhe.html`
- `templates/admin/financeiro.html`
- `static/css/style.css`
- `models.py`
- `app.py`

## Observação
O sistema agora guarda `usuario_registro` em pagamentos novos. Em bancos existentes, a coluna é criada automaticamente na inicialização.
