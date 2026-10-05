# Connect 1.0.101

## Fotos da vitrine
- Upload de fotos de itens salvos passa a ser imediato, sem depender do botão geral Salvar.
- Em item novo ainda não salvo, a foto grande é reduzida localmente antes de entrar no editor; assim o formulário não carrega o arquivo bruto de vários MB.
- Ao selecionar uma foto, o usuário vê a prévia e o progresso de envio.
- Após o upload, a interface informa “Processando e melhorando a imagem” enquanto o servidor corrige orientação, redimensiona e comprime.
- Imagens são persistidas no Neon em WebP otimizado, com original de composição preservada e miniatura leve.
- Padrão de tamanho reduzido: original otimizado até 1400 px / alvo 260 KB; ajuste até 1200 px / alvo 220 KB; miniatura até 420 px / alvo 55 KB.
- O botão Ajustar foi reforçado com delegação de clique, feedback de carregamento e feedback durante o salvamento do ajuste.
- Novo botão “Otimizar todas deste item”.
- Novo botão “Otimizar fotos” no catálogo para reprocessar todas as fotos da empresa de uma só vez, preservando enquadramentos já ajustados.

## Publicação
- Corrigido item que permanecia em rascunho após escolher Ativo.
- A publicação agora é enviada diretamente pelo rádio `vitrine_ativo=1/0`, sem depender de campo oculto atualizado por JavaScript.
- O backend interpreta explicitamente `1` como ativo e `0` como rascunho.

## Validações
- Python compilado.
- 63 templates Jinja analisadas sem erro.
- JavaScript renderizado do cadastro do item validado com `node --check`.
- Testes locais de upload, compressão, miniatura, otimização em lote e conversão Ativo/Rascunho executados.
