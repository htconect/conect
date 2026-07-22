# Atualização — Módulo Financeiro / Conciliação Bancária

## O que foi entregue
- Nova tela em `/painel/financeiro`, sem menu lateral, usando o fluxo atual do Connect.
- Importação de extrato bancário em CSV ou XLSX.
- Classificação dos lançamentos do banco em quatro categorias: Casa, Empresa, Aluguel e Manutenção.
- Vínculo dos lançamentos do banco com os pagamentos já existentes do sistema.
- Lançamento manual.
- Lançamento futuro em A Receber.
- Resumos de saldo real por conta, saldo real total, a receber e saldo previsto.
- Controle no cadastro de usuários: visualiza ou não o financeiro.

## Arquivos alterados
- `app.py`
- `models.py`
- `templates/admin/financeiro.html`
- `templates/admin/empresas.html`
- `static/css/style.css`
