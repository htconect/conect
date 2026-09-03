# v1.0.25 — Retorno InfinitePay e WhatsApp

No primeiro pagamento, antes de o cliente sair do Conect para o checkout da InfinitePay, é exibido um aviso de alta visibilidade:

> IMPORTANTE: depois de pagar, toque em CONTINUAR na tela da InfinitePay.
> Esse passo é necessário para iniciar automaticamente o envio do contrato pelo WhatsApp.
> Não feche a InfinitePay antes disso. Quando o WhatsApp abrir, toque em Enviar.

A regra é exibida apenas quando ainda não existe valor pago no contrato. O saldo posterior não repete a orientação de envio do contrato.

O endpoint de retorno continua sendo `/e/{slug}/pagamento-retorno`; após confirmar o primeiro pagamento, ele redireciona diretamente para o `wa.me` do responsável da negociação.
