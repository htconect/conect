# Connect 1.0.118 — Oportunidade da vitrine antes do contrato + LokaFest

- A pré-reserva da vitrine deixa de criar `Solicitacao`, cliente ou rascunho de contrato antes da decisão da empresa.
- Novo estágio `vitrine_oportunidades`: preserva o carrinho, valores, frete, horário, retirada, horas adicionais, WhatsApp e autorização para parceiros sem ocupar estoque.
- Os pedidos pendentes passam a aparecer em **Vitrine pública > Pedidos para analisar**, com duas ações independentes:
  - **Atender e enviar cadastro**: somente aqui nasce o contrato/solicitação e o WhatsApp do cliente é aberto com o cadastro já preenchido.
  - **Indicar no LokaFest**: abre o LokaFest preenchido, sem aprovar ou criar contrato no Connect.
- Se o cliente não tiver autorizado parceiros, continuam disponíveis **Solicitar autorização** e **Registrar autorização recebida**.
- A composição comercial vista pelo cliente é congelada na oportunidade e preservada ao virar contrato, incluindo horas adicionais e deslocamento.
- Metadados técnicos antigos `[VITRINE_*]` deixam de aparecer nas observações visíveis do contrato.
- **Buscar cliente** volta ao menu lateral (e ao menu superior) quando o usuário possui acesso ao módulo.
- LokaFest passa a ter URL padrão automática `https://lokafest.com.br/indicar`; ao ativar a integração não é necessário digitar o link manualmente.
- Karaokê RJ recebe migração única que deixa o LokaFest ativo e configurado automaticamente.
- Nova configuração opcional de ambiente: `LOKAFEST_PUBLIC_URL`.
