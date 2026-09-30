# Connect 1.0.77

Integração simplificada de NFS-e com o Organiza.

- O botão passa a se chamar **Enviar NFS-e para o Organiza**.
- Ao clicar, o Connect solicita somente o **CNPJ do tomador**.
- O CNPJ informado é usado apenas para a NFS-e e não altera o cadastro do cliente nem o contrato.
- O Connect envia ao Organiza apenas: CNPJ, empresa/contrato de origem, valor e todos os dados do evento.
- Dados cadastrais/fiscais do CNPJ não são enviados; o Organiza localiza ou cria o cliente e permite atualizar os dados pelo CNPJ.
- Data, descrição e endereço completo do evento continuam sendo responsabilidade do Connect.
- A origem permanece identificada como `connect`, permitindo ao Organiza distinguir rascunhos automáticos dos manuais.
