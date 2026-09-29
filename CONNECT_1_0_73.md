# Connect 1.0.73

Padronização dos pagamentos Online e correção em lote de categorias no relatório financeiro.

- Pagamentos históricos da InfinitePay passam a ser reconhecidos como **Online**, inclusive registros antigos identificados pela cobrança InfinitePay, código `IP-*` ou descrição da integração.
- Na inicialização, pagamentos InfinitePay antigos são normalizados para `usuario_registro = InfinitePay`, sem apagar o responsável de conciliação existente.
- O relatório financeiro existente ganhou edição direta da **Categoria** em cada movimento.
- A tela permite corrigir várias categorias e usar **Salvar categorias** uma única vez no final.
- A correção em lote altera **somente a categoria**; data, descrição, conta e valor permanecem intactos.
- Vínculos financeiros sensíveis são preservados. Linhas vinculadas que não podem mudar de categoria são mantidas e informadas como bloqueadas.
- A coluna de descrição foi identificada como **Fornecedor / descrição**, facilitando a conferência de pagamentos repetidos do mesmo fornecedor usando os filtros já existentes.
