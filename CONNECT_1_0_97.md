# Connect 1.0.97 — Mídia otimizada no Neon

## Objetivo
Eliminar a dependência de disco persistente no Render Free. Fotos, logos e capas são tratadas no momento do upload e persistidas no Neon/Postgres em formato compacto.

## Alterações
- Nova tabela `midias_imagens` com conteúdo binário (`BYTEA` no PostgreSQL/Neon).
- Endpoint `/midia/{id}` para servir imagens do banco com cache longo no navegador.
- Todo novo upload de logo, capa e foto de produto é normalizado para WebP antes de gravar.
- O arquivo bruto grande não é gravado no banco.
- O “original” preserva composição e enquadramento, porém já otimizado e redimensionado.
- Foto ajustada/recortada é persistida separadamente.
- Miniatura do card é gerada e persistida separadamente.
- JFIF/JPEG/PNG/WebP/GIF continuam aceitos na entrada; a saída persistida é WebP.
- Alvos aproximados de tamanho:
  - logo original: até ~150 KB;
  - logo ajustada: até ~120 KB;
  - capa original: até ~420 KB;
  - capa ajustada: até ~350 KB;
  - foto original de produto: até ~450 KB;
  - foto ajustada: até ~300 KB;
  - miniatura: até ~90 KB.
- Imagens antigas que ainda existirem em `static/uploads` ou `/media` são migradas automaticamente para o banco no startup.
- Arquivos antigos já perdidos pelo Render não podem ser recriados e continuam exigindo reenvio.
- Ao trocar/excluir fotos, as versões antigas armazenadas no banco são removidas quando não são mais usadas.
- `render.yaml` não exige mais Persistent Disk nem `CONECT_MEDIA_ROOT`.

## Render Free + Neon
O Render executa somente a aplicação. O Neon mantém banco e imagens persistentes. Redeploy/restart do Render não apaga novas fotos.
