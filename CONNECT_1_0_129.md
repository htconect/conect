# Connect 1.0.129

## Correção — Evolução de Vendas

- Corrige erro ao abrir **Relatórios > Evolução de Vendas** em produção.
- A tabela `evolucao_vendas_historico` agora é criada pela migração estrutural leve executada em todo startup, sem depender de `CONNECT_RUN_STARTUP_MAINTENANCE=1`.
- Mantém índices de empresa e ano para o relatório.
- Corrige a tela padrão de erro: o `base.html` não tenta mais acessar `empresa.modulo_opcionais_ativo` quando `empresa` não existe no contexto.
- Com isso, uma eventual exceção futura deixa de ser mascarada por `jinja2.exceptions.UndefinedError: 'empresa' is undefined`.

## Causa

A versão 1.0.128 adicionou o model `EvolucaoVendasHistorico`, mas em produção `Base.metadata.create_all()` só roda quando o modo de manutenção está habilitado. O startup leve não criava a nova tabela. Ao ocorrer a exceção do banco, o próprio template de erro falhava porque duas verificações de Opcionais acessavam `empresa` sem validar se ela estava definida.
