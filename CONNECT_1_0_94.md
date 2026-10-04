# Connect 1.0.94 — parametrização da empresa, vitrine e deslocamento

## Cadastro/ADM da empresa
- ADM de empresa reorganizado em blocos, acompanhando o padrão do cadastro guiado.
- Funcionalidades opcionais por empresa: Equipes, Recursos, Cupons e Inteligência.
- Ao desativar um módulo, os dados históricos são preservados e as telas/regras relacionadas deixam de aparecer no fluxo normal.
- Equipes deixam de nascer automaticamente para empresas novas; cadastro passa a usar ordem e inativação em vez de exclusão física.
- InfinitePay fica como configuração técnica exclusiva do ADM. A área comum da empresa mostra apenas o status do pagamento online.
- Sistemas Humiat vinculados passam a ser registrados no cadastro da empresa. O Connect aproveita slug/metadados recebidos do Humiat ID e pode criar um rascunho de empresa a partir do SSO administrativo.
- LokaFest pode ser marcado como sistema vinculado, com URL pública para encaminhamento da vitrine.

## Vitrine
- Cadastro de Categorias da Vitrine por empresa, com nome, ordem e ativo/inativo.
- A vitrine ordena primeiro as categorias e depois os itens pela ordem de exibição do produto/serviço.
- Categoria inativa deixa de aparecer publicamente sem apagar produtos ou histórico.
- Produtos passam a escolher uma categoria cadastrada na empresa.
- Fluxo da vitrine configurável no ADM: reservar diretamente, solicitar aprovação ou encaminhar ao LokaFest.

## Frete/deslocamento
- Três modos: Sob consulta, Por KM e Valor fixo.
- Removido o conceito de cálculo por região.
- No modo Por KM, o ADM informa CEP de origem e valor por KM.
- A vitrine solicita CEP e número do destino.
- Regra fixa: distância de ida x 2 = QTD KM ida e volta; total = QTD KM x valor por KM.
- O servidor recalcula o deslocamento antes de criar o pedido.
- CEP e número usados no cálculo seguem automaticamente para o rascunho do contrato.
- Em Sob consulta, o pedido aguarda aprovação porque o total final ainda depende do deslocamento.

## Cupom e composição comercial
- Cupom pode ser aplicado diretamente na vitrine quando o módulo de Cupons estiver ativo.
- A validação é repetida no servidor.
- O desconto segue a regra já usada pelo contrato: incide sobre os itens/equipamentos; o frete é somado depois.
- O rascunho recebe subtotal, cupom, percentual, desconto, frete e total final.

## Aprovação e LokaFest
- No fluxo de aprovação, a vitrine cria uma pré-reserva e mostra uma confirmação de pedido recebido.
- O responsável pode revisar antes de liberar o contrato pelo fluxo administrativo existente.
- Empresas com LokaFest ativo podem configurar a vitrine para encaminhar o cliente ao link público do LokaFest, levando origem, empresa e data do evento.

## Imagens e erros
- Upload de imagem passa a validar o conteúdo real do arquivo, não apenas a extensão.
- JFIF/JPE/JPEG são reconhecidos como JPEG e normalizados para .jpg.
- Campos de imagem aceitam JFIF e a própria prévia pode ser clicada para abrir a seleção de arquivo.
- Criada tela HTML padrão para erros 4xx/5xx, com mensagem amigável e código de referência; APIs continuam retornando JSON.

## Compatibilidade
- Migração preserva empresas existentes que já tinham equipes, recursos, cupons ou rotas inteligentes, ativando o respectivo módulo apenas na introdução da nova configuração.
- O campo histórico de multiplicador de KM é mantido por compatibilidade, mas o cálculo atual é sempre ida e volta (2x).
- Integrações específicas já existentes com Organiza não foram removidas nesta versão.
