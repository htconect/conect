# Conect v1.0.29 — Validação global de campos

## Objetivo
Evitar ações de salvar/confirmar que parecem não responder quando falta algum dado necessário.

## Regras globais
- Campos HTML com `required` são validados automaticamente.
- Campos obrigatórios apenas para uma função podem usar `data-required-functional="1"`, sem alterar a obrigatoriedade no banco.
- Mensagens específicas podem ser informadas com `data-required-message="..."`.
- Uma ação específica pode exigir campos com `data-required-fields="campo1,campo2"`.
- Links/botões que não submetem o formulário também podem acionar a mesma validação usando `data-validate-form="id-do-form"`.
- O primeiro campo inválido recebe foco e rolagem automática.
- O campo é destacado em vermelho e recebe uma mensagem logo abaixo.
- Se o campo estiver dentro de um `details`, a seção é aberta automaticamente.
- A validação também se aplica a formulários inseridos dinamicamente.

## Operação
O campo `equipe_id` passou a ser obrigatório funcionalmente na tela Operação.
Se o usuário tentar salvar sem equipe, a ação é bloqueada e aparece:

`Selecione a equipe para continuar.`

Essa regra é apenas da função Operação; não exige alteração da coluna no banco.
