# Connect 1.0.98 — Preço por tipo de evento

## Cadastro do item

- Adiciona opção **Cobrança por tipo de evento** por produto/serviço.
- O preço principal continua sendo o padrão.
- Para cada tipo de evento é possível escolher:
  - **Usar preço normal**;
  - **Preço específico**;
  - **Sob consulta**.
- O campo de valor aparece somente quando `Preço específico` é selecionado.
- A configuração pode ser desligada sem apagar os preços especiais já cadastrados.

## Tipos de evento

Os tipos são registros por empresa, preparados para futura administração/ordenação própria. Ao primeiro uso, a empresa recebe uma lista inicial:

1. Festa particular
2. Escola ou creche
3. Empresa
4. Prefeitura ou evento público
5. Igreja ou comunidade
6. Feira ou evento de grande porte
7. Outro

## Persistência

- Nova tabela `tipos_evento_empresa`.
- Nova tabela `produto_precos_evento`.
- Nova flag `produtos_servicos.preco_por_tipo_evento`.
- Ao copiar um produto/serviço, os preços especiais também são copiados.

## Vitrine

Nesta versão o cadastro e a persistência estão prontos. A seleção do tipo de evento e o uso desses valores na vitrine pública serão aplicados na rodada de refatoração da vitrine, conforme o mapeamento aprovado.
