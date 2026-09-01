# HUMIAT Conect — Versão 1.0.14

## InfinitePay — escolha visível e parcelamento também no saldo

- Empresas com InfinitePay continuam usando a integração normalmente.
- A etapa de pagamento mostra sempre **PIX** e **Cartão**, tanto no primeiro pagamento quanto no pagamento do saldo.
- O cliente pode marcar visualmente como pretende pagar; a confirmação final da forma de pagamento continua sendo feita no checkout seguro da InfinitePay.
- Ao escolher Cartão, a área de **Simular parcelas** fica destacada.
- Quando já existe uma cobrança InfinitePay em andamento, o Conect reutiliza o mesmo checkout para impedir cobrança duplicada, mas mantém visíveis PIX, Cartão e a simulação de parcelas do valor daquela cobrança.
- Os dados para conferência do PIX continuam disponíveis: **nome do recebedor** e **banco/instituição**, quando cadastrados na empresa.
- Empresas sem InfinitePay permanecem no fluxo de PIX próprio, sem alteração da regra existente.

## Fechar

- O botão **Fechar** saiu de dentro de “Consultar contrato aceito”.
- Ele agora fica logo abaixo da etapa de pagamento.
- O botão tenta fechar somente a aba atual do navegador.
- Quando o navegador bloqueia o fechamento automático de uma aba aberta diretamente pelo cliente, o Conect informa que a aba pode ser fechada pelo seletor de abas.
- “Ver contrato” e “Ver cláusulas” continuam disponíveis na área recolhível de consulta.

Commit:

`v1.0.14 - restaura escolha PIX/cartão e simulador no saldo e reposiciona fechar`
