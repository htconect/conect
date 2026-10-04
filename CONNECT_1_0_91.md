# CONNECT 1.0.91 — Vitrine pública do cliente

## Objetivo
Primeira etapa da nova experiência visual do cliente dentro do próprio Connect. A operação interna existente foi preservada; a novidade fica antes do contrato.

## Fluxo público novo
- A raiz pública da empresa (`/e/{slug}`) pode abrir uma entrada visual com a marca da locadora.
- O cliente começa escolhendo a **data do evento**.
- A vitrine mostra somente itens ativos e a disponibilidade real calculada pelo Connect.
- O cliente adiciona um ou mais itens, ajusta quantidade e vê o total dos itens em tempo real.
- **Reservar** leva ao formulário público já pertencente ao Connect.
- O pedido escolhido é carregado automaticamente no formulário; a data não precisa ser digitada novamente.
- Ao concluir os dados, os itens são gravados em `reserva_itens`, o valor é calculado e o cliente segue diretamente para a página pública do contrato.
- Quando o produto possui contrato padrão, o contrato já nasce pronto para leitura/aceite.
- O fluxo público antigo foi preservado em `/e/{slug}/identificar` e continua sendo usado quando a vitrine está desativada.

## Identidade visual da empresa
Nova tela **Vitrine pública** no painel:
- ativar/desativar a vitrine;
- título e frase curta;
- cor principal;
- cor suave;
- imagem de fundo opcional enviada do celular/PC;
- prévia visual;
- link público para teste.

A vitrine começa **desativada por padrão**, evitando alterar links públicos de empresas já existentes sem decisão do locador.

## Itens de locação
Cada produto ganhou configuração visual independente:
- mostrar/ocultar na vitrine;
- resumo curto;
- categoria visual;
- ordem de exibição;
- envio de múltiplas fotos direto da galeria;
- primeira foto vira capa automaticamente;
- trocar a foto principal;
- excluir fotos.

## Disponibilidade
A vitrine reaproveita a regra já existente no Connect:
- quantidade física do produto;
- reservas ativas da data;
- recursos compartilhados vinculados ao item.

A disponibilidade é validada novamente ao tocar em Reservar e outra vez antes de criar o contrato, reduzindo risco de conflito entre a consulta e o fechamento.

## Banco
Novos campos em `empresas` e `produtos_servicos` são criados pela migração de startup. A nova tabela `produto_fotos` é criada via `Base.metadata.create_all`.

## Commit sugerido
`Connect 1.0.91 - adiciona vitrine publica visual e integra reserva ao contrato existente`
