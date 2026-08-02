# Próxima rodada — Performance e proteção de dados

## Ponto de partida

O diagnóstico de performance permanece ativo temporariamente. Os ganhos já medidos incluem:

- Home: 33 consultas para 11.
- Financeiro: 48 consultas para 23 antes da segunda fase.
- Disponibilidade: 15 consultas para 4.
- Agenda: 5 consultas.
- Operação/Reservas: 6 consultas após correção do carregamento.
- Empresa: removida das consultas repetidas de páginas GET por cache da sessão do servidor.

## Primeira tarefa da próxima rodada

Medir novamente as rotas abaixo depois do deploy desta versão:

1. `/painel`
2. `/painel/agenda`
3. `/painel/reservas`
4. `/painel/disponibilidade`
5. `/painel/financeiro`

Confirmar no diagnóstico que `SELECT empresas` não aparece nas páginas GET após o primeiro carregamento/login.

## Performance — próximos alvos

### Financeiro

- Manter a tela completa pronta antes de exibir.
- Não recalcular cards ao categorizar ou vincular lançamento.
- Atualizar cards apenas quando ocorrer:
  - importação bancária;
  - lançamento manual;
  - edição/exclusão financeira;
  - alteração de saldo inicial.
- Reduzir consultas restantes de lançamentos bancários e manuais.
- Salvar categoria e vínculo sem recarregar toda a página.

### Operação e Roteirização

- Medir o POST de salvar roteirização.
- Criar salvamento em lote, com um único commit.
- Não executar Inteligência, auditoria ou correções históricas em ações operacionais.
- Avaliar cache semanal somente após medir o salvamento real.

### Cache Manager

Evoluir o cache atual para dados de baixa alteração:

- empresa;
- contratos/modelos;
- produtos;
- equipes;
- categorias;
- permissões.

Cada cache deve ser invalidado apenas pela ação que altera aquele cadastro.

## Proteção dos dados dos clientes

Revisar em seguida:

- todas as rotas por `empresa_id`;
- acesso direto por ID na URL;
- tokens públicos e validade;
- cookies `Secure`, `HttpOnly` e `SameSite`;
- proteção CSRF em formulários;
- mascaramento de CPF, telefone, endereço e tokens nos logs;
- limite de tentativas no login;
- política de backup e teste de restauração no Neon;
- exclusão de dados sensíveis de mensagens de erro.

## Encerramento do diagnóstico

Quando as rotas principais estiverem dentro das metas:

```env
PERFORMANCE_MONITORING=false
```

O painel e o código permanecem disponíveis para futura reativação.
