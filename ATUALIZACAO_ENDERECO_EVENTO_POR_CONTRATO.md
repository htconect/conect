# Atualização — endereço do evento por contrato

Data: 30/08/2026

## Objetivo

Corrigir o fluxo operacional de endereço para impedir que uma alteração no cadastro geral do cliente mude o destino de contratos anteriores no Waze, Google Maps ou Inteligência Logística.

## Nova regra

O endereço operacional pertence à `Solicitacao` (contrato/reserva), e não ao cadastro do `Cliente`.

Campos adicionados em `solicitacoes`:

- `local_numero`
- `local_complemento`
- `local_cidade`
- `local_estado`
- `local_cep`

Os campos já existentes `local`, `bairro` e `local_nome` continuam sendo utilizados.

O cadastro do cliente mantém o último endereço usado somente por compatibilidade e como atalho/histórico. Ele não comanda mais o destino operacional de contratos que possuem o snapshot de endereço.

## Neon / migração de produção

O startup utiliza a rotina já existente `garantir_colunas_novas()` e adiciona as novas colunas de forma aditiva. Nenhuma coluna ou dado existente é apagado ou renomeado.

A migração `20260830_endereco_evento_por_contrato_v1` tenta congelar endereços de contratos antigos usando `enderecos_clientes`.

Regras de segurança da migração:

1. Se houver um único endereço histórico compatível, ele é usado.
2. Se houver `local_nome`/apelido compatível, ele é usado para desempatar.
3. Se existirem números diferentes para a mesma rua e não houver evidência suficiente, o sistema não adivinha o número.
4. O número atual do cliente só é usado em situações legadas consideradas seguras.
5. Contratos ambíguos ficam com número não confirmado e recebem aviso na Operação para revisão.
6. A migração é idempotente e registrada em `app_migrations`.

## Fluxos revisados

- criação de contrato pelo painel;
- pré-contrato público;
- edição completa do contrato;
- edição pública do contrato;
- cópia de contrato / “Usar como base”;
- transferência entre empresas;
- histórico de endereços do cliente;
- “A caminho”;
- “Iniciar rota”;
- Waze;
- Google Maps;
- Operação / Preparar;
- Agenda e cards de painel;
- Inteligência Logística;
- geocodificação automática;
- visualização do contrato;
- conteúdo de endereço usado em PDF/WhatsApp por meio das rotinas compartilhadas.

## Escolha de endereço

Ao localizar um cliente, o formulário passa a oferecer os endereços já utilizados, incluindo o apelido/nome do local quando disponível, por exemplo:

- Salão Imperial — Rua A, 120
- Casa de Festas X — Avenida B, 850
- + Digitar novo endereço

Ao escolher um endereço, o endereço completo e o nome do local são copiados para o novo contrato. Na opção “Usar como base”, o endereço do contrato copiado permanece preenchido, mas o usuário pode mantê-lo, escolher outro endereço do histórico ou cadastrar um novo.

## Waze / Maps

O destino é montado exclusivamente com o endereço do contrato:

`logradouro, número, bairro, cidade, estado, CEP`

O complemento (apartamento, bloco, salão etc.) não é enviado como termo de busca ao Waze/Maps para não prejudicar a correspondência do número. Ele continua visível no contrato e na Operação.

O Waze web usa sempre `q=<endereço>&navigate=yes`, igualando a origem do destino ao fluxo móvel.

## Validações realizadas

- `python -m py_compile app.py models.py` — OK
- `python -m compileall -q .` — OK
- carregamento dos 42 templates Jinja — OK
- startup completo em banco SQLite novo — OK
- migração aditiva das cinco colunas simulando schema antigo — OK
- cliente com dois contratos e dois endereços diferentes — OK
- alteração posterior do endereço do cadastro do cliente sem alterar rotas antigas — OK
- Waze usando número do contrato e ignorando número do cadastro geral — OK
- Google Maps usando número do contrato — OK
- complemento fora da busca de navegação — OK
- migração com dois números na mesma rua sem evidência suficiente — não adivinha — OK
- migração com apelido do local para desempate — OK
- idempotência da migração — OK

## Rollback

As alterações de schema são apenas aditivas. Um rollback de código não exige remover as novas colunas. Entretanto, voltar ao código anterior também volta à lógica antiga que podia usar o endereço atual do cliente para a rota.
