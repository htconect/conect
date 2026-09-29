# Connect 1.0.76

Correção da origem dos recebimentos InfinitePay no Financeiro.

- Movimentos criados automaticamente pela InfinitePay passam a aparecer como **Online** na lista financeira.
- Lançamentos realmente digitados pelo atendente continuam como **Manual**.
- A identificação Online usa o pagamento vinculado (`usuario_registro`, `conciliado_por` e observações da InfinitePay) e mantém compatibilidade com descrições antigas da integração.
- Na inicialização, pagamentos históricos vinculados a cobranças InfinitePay são normalizados para `usuario_registro = InfinitePay`, sem apagar o responsável de conciliação existente.
- Nenhum valor, data, categoria, banco ou vínculo financeiro é alterado pela normalização.
