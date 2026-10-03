# HUMIAT Conect — Versão 1.0.88

## Padronização visual HUMIAT / Adminator

- Connect passa a usar o mesmo `humiat-design-system.css` adotado pelo Organiza.
- Nova camada `connect-adminator.css` aplica os tokens e proporções do componente padrão sem alterar regras de negócio.
- Sidebar desktop alinhada ao shell escuro HUMIAT do Organiza (`#141B2D`), com navegação mais compacta.
- Cards, formulários, tabelas, botões, títulos e espaçamentos foram reduzidos e padronizados.
- Removidos os elementos ilustrativos da Carteira Humiat (moeda/coroa/desenho de carteira).
- Carteira Humiat virou um card administrativo compacto com quatro indicadores e ações diretas.
- Mantida a navegação inferior em estilo app no celular.
- Topo e cards mobile foram apenas refinados; o fluxo móvel não foi substituído pelo menu desktop.

## Arquivos principais

- `static/css/humiat-design-system.css`
- `static/css/connect-adminator.css`
- `templates/base.html`
- `templates/admin/painel.html`
- `config.py`
