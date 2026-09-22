# Correção WhatsApp “A caminho” — v1.0.37

Na tela **Operação**, os cards de entrega e retirada reutilizavam a mesma frase ao enviar a mensagem para o responsável no local.

A montagem da mensagem agora verifica `data-tipo`:

- `entrega` → **Estamos a caminho da entrega do equipamento de [cliente].**
- `retirada` → **Estamos a caminho da retirada do equipamento de [cliente].**

Não houve alteração no fluxo de roteirização ou navegação.
