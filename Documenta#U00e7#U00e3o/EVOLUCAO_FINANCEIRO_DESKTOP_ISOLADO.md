# Evolução — Financeiro Desktop Isolado

## Objetivo
Otimizar a nova tela de Financeiro/Conciliação para uso em desktop, em tela cheia, sem alterar a experiência mobile já existente no Connect.

## Decisões aplicadas
- A alteração ficou isolada em `templates/admin/financeiro.html`.
- No desktop, a tela oculta topo e navegação inferior para ganhar espaço.
- No celular, nada foi alterado: abaixo de 900px continua usando o layout mobile atual.
- Não foi iniciada uma versão desktop global do sistema para evitar retrabalho neste momento.

## Entregue
- CSS desktop específico para o Financeiro.
- Tela em largura total.
- Filtros em linha única.
- Cards de saldo otimizados.
- Tabelas lado a lado com rolagem interna.
- Formulários de lançamento manual e a receber mantidos na própria tela.

## Próximo passo sugerido
Validar essa tela no computador. Se a equipe aprovar o padrão, ele pode virar a base da futura versão desktop do Connect.
