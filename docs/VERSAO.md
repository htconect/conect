# HUMIAT Conect — Versão 1.0.15

## Pagamento mobile — correção de quebra e legibilidade

- Corrigido o estouro horizontal da etapa de pagamento em celulares.
- Os botões PIX e Cartão não recebem mais ícones automáticos do tema global.
- Textos dos métodos foram encurtados para **PIX / À vista** e **Cartão / Parcelar**.
- Em telas estreitas, PIX e Cartão ficam empilhados para não ultrapassar a largura disponível.
- Nome do recebedor e instituição passam a quebrar linha corretamente, inclusive nomes longos.
- Título, resumo financeiro, simulador e cards de pagamento receberam limites responsivos.
- O simulador de parcelas continua disponível e sua tabela rola apenas dentro do próprio bloco quando necessário.
- Botão **Fechar** permanece logo abaixo do pagamento e continua tentando fechar apenas a aba atual.

## InfinitePay e CEP

- Mantido o envio automático do CEP e endereço do contrato em todo checkout novo.
- Cobranças InfinitePay que já estavam iniciadas continuam reutilizando o mesmo checkout para evitar duplicidade; por isso um checkout criado antes da inclusão do endereço não é alterado retroativamente.
- Nenhuma cobrança pendente antiga é recriada automaticamente, evitando deixar dois links de pagamento ativos para o mesmo saldo.

Commit:

`v1.0.15 - corrige layout mobile do pagamento e preserva checkout InfinitePay pendente`
