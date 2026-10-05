# Connect 1.0.103

## Correção de interações nas telas novas

- O `base.html` passa a renderizar o bloco `scripts_extra` das telas administrativas.
- Corrige os controles que apareciam visualmente, mas não reagiam ao clique:
  - Frete / deslocamento: Valor fixo, Por KM e Sob consulta.
  - Exibição dinâmica de CEP de origem e valor por KM.
  - Preço por tipo de evento.
  - Adicionar/remover opcionais do item.
  - Rotinas de fotos e otimização que dependem do JavaScript da página.
- O modo de frete salvo também já renderiza seus campos visíveis no carregamento da página, antes mesmo da execução do JavaScript.

## Ordem visual

- Remove o campo numérico de ordem do cadastro do produto/serviço.
- Produtos passam a ser ordenados visualmente na tela Produtos e serviços com botões Subir/Descer.
- A movimentação de produto acontece dentro da própria categoria.
- Produto novo entra automaticamente no final de sua categoria.
- Ao trocar um produto de categoria, ele entra no final da nova categoria.
- Remove o campo numérico de ordem das Categorias da vitrine.
- Categorias passam a ter botões Subir/Descer e posição visual.
- Categoria nova entra automaticamente no final da lista.
- As ordens internas são normalizadas automaticamente pelo sistema.
