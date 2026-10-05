# Connect 1.0.96 — mídia persistente e preservação do original

## Objetivo
Corrigir o desaparecimento de fotos após deploy/restart e padronizar o tratamento de mídia no Connect.

## Alterações
- Armazenamento de mídia separado do código por `CONECT_MEDIA_ROOT`.
- Rota `/media` para servir arquivos persistentes.
- `render.yaml` preparado para disco persistente em `/var/data`.
- JPG, JPEG e JFIF continuam normalizados automaticamente.
- Fotos de produtos passam a manter três referências:
  - original imutável;
  - imagem ajustada para a vitrine;
  - miniatura WebP otimizada para cards.
- Ajustar uma foto existente não apaga mais o original.
- Logo e capa da empresa também preservam o arquivo original quando enviados pelo cadastro guiado.
- Migração automática de URLs antigas `/static/uploads/...` quando o arquivo físico ainda existe.
- Se o banco aponta para uma imagem já perdida, a interface mostra `Imagem ausente` em vez de ícone quebrado.
- Cadastro do produto permite reenviar uma foto ausente diretamente.
- A vitrine pública ignora arquivos locais ausentes e usa placeholder seguro.

## Importante sobre imagens antigas
Se um deploy anterior já removeu o arquivo físico, ele não pode ser reconstruído apenas pelo caminho salvo no banco. Nesses casos a foto precisa ser reenviada uma vez. Depois da 1.0.96, novos uploads ficam no armazenamento persistente.

## Render
O Blueprint inclui:

```yaml
CONECT_MEDIA_ROOT: /var/data/connect-media

disk:
  name: connect-media
  mountPath: /var/data
  sizeGB: 1
```

Se o serviço do Render não estiver sendo gerenciado pelo `render.yaml`, criar/associar manualmente um Persistent Disk em `/var/data` e definir `CONECT_MEDIA_ROOT=/var/data/connect-media`.
