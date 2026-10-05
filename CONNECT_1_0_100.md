# Connect 1.0.100 — Revisão completa do cadastro de item e ações da vitrine

## Correções críticas

- Corrigido HTML inválido no cadastro de produto/serviço: formulários de Capa e Excluir estavam aninhados dentro do formulário principal do item.
- O formulário principal agora permanece íntegro do início ao fim e o botão Salvar é explicitamente associado a `formProduto`.
- Ações Capa e Excluir usam formulários independentes fora do cadastro principal, evitando conflito com Salvar.
- Excluir foto volta a remover registro, original otimizado, derivada e miniatura no Neon.
- Ajustar foto usa chamada POST dedicada, com tratamento de erro e retorno ao bloco Fotos.
- Botão Salvar mostra estado `Salvando...` somente após a validação do formulário e não fica mais sem ação.
- Corrigido erro 500 na Operação ao montar mensagem de saldo: `montar_mensagem_whatsapp_saldo_operacao` agora recebe a sessão `db` explicitamente.

## Validações executadas

- Compilação de `app.py`, `models.py`, `database.py`, `config.py` e `utils.py`.
- 63 templates carregadas com o ambiente real do Connect sem erro.
- Teste HTTP local com banco temporário:
  - login da empresa;
  - abertura do cadastro do item;
  - salvar alteração do item;
  - ajustar foto;
  - excluir foto;
  - remoção das mídias relacionadas;
  - renderização da vitrine pública.
- JavaScript renderizado das telas de cadastro do item e vitrine validado por `node --check`.
- Teste direto da mensagem de saldo operacional com link público seguro.

## Observação técnica

O defeito de Salvar/Capa/Excluir era causado principalmente pelo uso de `<form>` dentro de outro `<form>`, estrutura inválida em HTML. Navegadores podem encerrar o formulário principal automaticamente ao encontrar o formulário interno, produzindo comportamento aparentemente intermitente nos botões.
