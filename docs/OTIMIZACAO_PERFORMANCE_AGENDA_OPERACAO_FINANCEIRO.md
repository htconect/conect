# Otimização de performance — Agenda, Operação e Financeiro

## Alterações aplicadas

### Agenda
- A abertura da tela não executa mais `garantir_agenda_reservas`.
- O GET da Agenda voltou a ser somente leitura.
- Cliente e produto são carregados junto com os contratos.
- Pagamentos usados apenas no fallback do responsável são carregados em lote.
- Equipes das agendas operacionais são carregadas antecipadamente.

### Operação
- A abertura da tela não executa mais `garantir_agenda_reservas`.
- Removido o recálculo de pagamentos contrato por contrato.
- `valor_pago` passa a ser lido diretamente do resumo mantido no contrato.
- Solicitação, cliente, produto e equipe são carregados na consulta principal.
- Nenhuma auditoria ou `commit` é executado durante a consulta.

### Financeiro
- Os cinco blocos de CSS foram consolidados em `static/css/financeiro.css`.
- O CSS específico agora é carregado no `<head>` antes da renderização da página.
- A classe `tela-financeiro-desktop` nasce diretamente no `<body>`.
- Removido o JavaScript que alterava o layout depois de a página aparecer.
- Isso elimina as trocas progressivas de tamanho, cabeçalho, navegação e rolagem.

### Render + Neon
- Configurado pool pequeno e reaproveitável de conexões SQLAlchemy.
- `pool_pre_ping` permanece ativo.
- Conexões são recicladas para reduzir problemas com conexões ociosas.
- O carregamento visual global só aparece após 450 ms, evitando piscadas em navegações rápidas.

## Regra adotada

Rotas GET de consulta não devem criar, corrigir, apagar, sincronizar ou executar commit.
Correções históricas permanecem disponíveis nas rotinas existentes, mas não são mais executadas no trabalho diário.

## Próxima evolução recomendada

O salvamento da roteirização ainda pode ser convertido para uma única requisição em lote e atualização da tela sem redirecionamento completo. Essa evolução deve ser feita separadamente para preservar as regras operacionais atuais.
