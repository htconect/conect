# InfinitePay — v1.0.10

## Correção do retorno após pagamento

O erro `Input should be a valid integer` acontecia porque a URL `/e/{slug}/pagamento/retorno` era capturada antes pela rota dinâmica `/e/{slug}/pagamento/{solicitacao_id}`. O texto `retorno` acabava sendo interpretado como um ID inteiro.

A correção registra a rota de compatibilidade antes da rota dinâmica e passa a gerar novos checkouts com `/e/{slug}/pagamento-retorno`, eliminando a colisão.

## Endereço no checkout

O payload da InfinitePay passa a enviar o endereço congelado da própria solicitação/contrato usando o bloco `address`: CEP, logradouro, bairro, número e complemento. O cadastro atual do cliente não substitui o endereço já congelado do contrato.

## WhatsApp e recuperação manual

Quando o pagamento é confirmado, a página continua tentando abrir automaticamente o WhatsApp do responsável pelo contrato. O botão manual **Enviar contrato pelo WhatsApp** permanece visível desde o início para permitir nova tentativa.

No painel interno da solicitação, a área **Pagamento** também passa a exibir **Enviar contrato** quando o contrato já foi aceito.
