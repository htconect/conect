# Connect 1.0.124

Tabela de preço no registro de equipamentos do contrato interno.

- adiciona **Residencial** e **Empresa** em “Registrar equipamentos”;
- contratos antigos/internos usam **Residencial** como padrão;
- ao trocar a tabela, os valores unitários dos equipamentos selecionados são atualizados pelo mesmo cadastro de preços já usado na vitrine;
- o valor unitário continua editável para exceções;
- a escolha é salva em `solicitacoes.tipo_evento_comercial` e também passa a orientar a duração do contrato;
- não cria preço duplicado nem altera a regra da vitrine pública.
