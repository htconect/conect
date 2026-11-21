# Conect 1.0.223 — Tipos de cadastro e composição de combos no próprio produto

## Fluxo único: Produtos e Serviços

- O menu exclusivo **Combos** deixa de ser exibido. URLs antigas redirecionam para **Produtos e Serviços**.
- O cadastro mantém a escolha **Categoria da vitrine** independentemente do tipo de estoque.
- Em **Operação → Tipo de cadastro** estão três opções:
  - **Produto principal:** quantidade própria, por exemplo quatro Jukebox; consome apenas seus recursos obrigatórios.
  - **É combo?:** sem quantidade própria. Apresenta **Qual o produto principal?**, com campos **Produto principal** e **Quantidade** e botão **+ Adicionar produto principal**. Pode usar um ou muitos produtos principais, existentes na mesma empresa. Consome também seus próprios recursos opcionais obrigatórios, nunca os recursos dos principais.
  - **Opcional avulso:** não possui quantidade própria de Produto e Serviço; vincula os recursos físicos já cadastrados (JBL, microfones etc.) na própria seção Itens e opcionais obrigatórios. O aluguel avulso desconta do mesmo estoque compartilhado pelos combos e pelos opcionais extras dos contratos.
- Permite converter um produto existente para combo ou opcional avulso sem criar outro ID: preserva fotos, preço, categoria, contratos e vínculos de recursos já cadastrados. A composição nova vale também para compromissos ativos; revisar datas futuras após converter.
- Não permite que combo seja principal de outro combo, nem que opcional avulso seja selecionado como principal.
- Sempre confere estoque dos componentes e recursos na data de evento e em todo intervalo até a retirada, inclusive nas confirmações de contrato.
- Não permite retirar dos compromissos os recursos obrigatórios do combo ou do opcional avulso mediante ajustes manuais da operação.

## Exemplo de estoque

- 4 Jukebox no estoque próprio.
- Jukebox Pro = **1 Jukebox** e recursos obrigatórios próprios, por exemplo **2 JBLs**.
- Alugou Jukebox Pro: restam **3 Jukebox** para normal ou para outros combos (desde que suas peças também estejam livres).
- Aluguel JBL avulsa = opcional avulso ligado ao recurso existente JBL com quantidade 1; utiliza o mesmo estoque compartilhado, sem criar novas JBLs no cadastro.
- Combo Festa = 1 Portátil + 1 Fliperama + 1 Just Dance; faltando um deles, o combo não fica disponível.

## Migração

- PostgreSQL: startup leve acrescenta `produtos_servicos.tipo_cadastro VARCHAR(20) NOT NULL DEFAULT 'principal'` com `IF NOT EXISTS`, sem manutenção geral, e preenche `combo` nos registros antigos marcados `eh_combo = true`.
- As colunas históricas das versões 1.0.219 e 1.0.220 são preservadas para não apagar histórico.
- A tabela de composição de combos já existe na 1.0.222 e é reutilizada; não criamos um novo estoque.
- Se o aplicativo executar o startup normalmente, não requer SQL manual.
- Fazer backup e publicar apenas após validar a versão local. Não foi realizado deploy na produção.

## Instalação (apenas sobre o código 1.0.222)

```powershell
git apply --check Conect_1.0.223_patch_sobre_1.0.222.patch
git apply Conect_1.0.223_patch_sobre_1.0.222.patch
python -m pytest -q
git status
git add -A
git commit -m "Unifica produtos combos e opcionais avulsos com estoque compartilhado"
git push origin main
```

**Validação:** testes SQLite/FastAPI locais, não equivalem à confirmação do PostgreSQL/Render reais. Se o `git apply --check` falhar, não execute o segundo comando e não substitua arquivos indiscriminadamente.
