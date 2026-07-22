# Evolução Reserva - Correções de fluxo

## Ajustes realizados

- Corrigido link quebrado em reservas por erro de rota/listagem.
- Corrigido uso de variável `busca` sem definição na tela de reservas.
- Restaurado acesso a Configurações, Produtos e Contratos dentro da empresa.
- Link público da reserva voltou para baixo do nome da empresa no painel.
- Botão de compartilhar WhatsApp mantido ao lado do link da reserva.
- Logo agora usa `logo_url` ou, se vazio, `logo_idb_url`.
- Produtos/serviços não exigem mais contrato.
- Contrato continua existindo, mas agora é vinculado à reserva.
- Reserva aceita mais de um produto/serviço.
- Valor total da reserva continua manual, permitindo combo, desconto ou ajuste comercial.
- Tela de aceite pública mostra produtos/serviços da reserva.
- Cliente mantém filtro por CPF/telefone e mostra reservas no detalhe.
- Campos configuráveis da empresa são recriados automaticamente para empresas já existentes.
- Produto exemplo e contrato fictício são criados para empresas sem dados iniciais.

## Observação importante sobre logo

Links como `https://ibb.co/...` normalmente são página de visualização, não imagem direta.
Para aparecer no sistema, use o link direto da imagem, geralmente terminando em `.png`, `.jpg` ou `.webp`.

