# Conect 1.0.223 — converter produto já cadastrado em combo

## Motivo
A versão 1.0.222 já possui uma área exclusiva **Cadastros → Combos** e aceita vários produtos principais. Esta atualização acrescenta o fluxo para transformar **o mesmo registro de Produto/Serviço** em combo, inclusive se já houver fotos, preços, opcionais e locações associadas.

## Como converter
1. Abra **Cadastros → Produtos e Serviços** e localize o item existente.
2. Clique em **É combo?** (ou **Editar** → **Operação** → **É combo?**).
3. Marque **É combo?** e selecione pelo menos um **produto principal** já cadastrado; configure a quantidade necessária de cada produto por unidade de combo.
4. Mantenha os recursos/opcionais obrigatórios do próprio combo e pressione **Salvar alterações**.
5. O produto preserva **o mesmo ID** e passa a aparecer em **Cadastros → Combos**.

### Regras de estoque
- O combo não tem estoque próprio: limita-se ao saldo dos principais selecionados e aos **recursos/opcionais obrigatórios cadastrados nele**, sem herdar os opcionais dos principais.
- Exemplo: 4 Jukebox disponíveis, conversão de Jukebox Pro com 1 Jukebox e 2 JBLs. Uma locação de Jukebox Pro consome 1 das 4 Jukebox e 2 JBLs, restando 3 Jukebox; a capacidade do combo ainda depende das JBLs disponíveis.
- Um produto que já é principal de outro combo não pode ser convertido para combo (evita vínculos em cascata).
- Quantidade anteriormente cadastrada no produto convertido fica preservada no registro para uma eventual reversão, **mas não limita a disponibilidade do combo**.

## Locações já cadastradas
- A conversão **não cria outro produto** nem apaga histórico: reservas, itens de contrato, fotos, preços e vínculos permanecem associados ao ID original.
- **Atenção à disponibilidade**: a composição passa a ser usada também para calcular o consumo das reservas ainda ativas do produto convertido. Se houver reservas futuras já aceitas, verifique possíveis conflitos no estoque após converter. Reservas antigas/históricas não são apagadas ou reescritas.
- Se o cadastro for revertido para produto principal, a quantidade original armazenada permanece disponível como referência, mas é necessário conferir o estoque antes de salvar.

## Migrações e implantação
- **Não requer nova migração do PostgreSQL** quando o banco já está no esquema 1.0.222: usa `produtos_servicos.eh_combo` e `combo_produtos_principais` já criados.
- Não exclui colunas ou registros históricos das versões anteriores. A tela antiga de “recurso principal” foi descontinuada na 1.0.222.
- O aplicativo não é publicado automaticamente: aplicar o PATCH no código 1.0.222, executar testes, publicar no Render e testar em empresa real após backup do banco.

## Testes
`pytest -q test_migrar_produto_combo_223.py` cobre conversão com locação preexistente, preservação de ID/preço/foto/vínculos e bloqueio de principal usado por outros combos. Executar também `pytest -q`.
