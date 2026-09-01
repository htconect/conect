# Atualização do fluxo de pagamento — v1.0.14

## InfinitePay integrada

A página do contrato passa a tratar a InfinitePay de forma visualmente distinta do PIX manual. Em qualquer cobrança InfinitePay pendente, inclusive no segundo pagamento, aparecem PIX e Cartão, os dados bancários para conferência do PIX e o simulador de parcelas do cartão.

Uma cobrança InfinitePay já criada não é recriada. O botão continua abrindo o checkout existente para manter a proteção contra duplicidade.

## Empresas sem InfinitePay

Nenhuma regra do PIX próprio foi removida ou substituída. O cadastro da empresa continua fornecendo PIX copia e cola, nome do recebedor e banco/instituição.

## Fechamento da página

O botão Fechar passa a ficar abaixo da área principal de pagamento. Ele chama `window.close()` e, por limitação de segurança dos navegadores, pode não encerrar uma aba que tenha sido aberta diretamente pelo usuário. Nesse caso a tela exibe orientação para fechar somente a aba pelo próprio navegador.
