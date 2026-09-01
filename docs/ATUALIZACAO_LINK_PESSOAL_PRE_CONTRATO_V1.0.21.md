# Link pessoal de pré-contrato — v1.0.21

## Objetivo

Fazer o botão **Compartilhar Pré-Contrato** gerar um link permanente e diferente para cada atendente, permitindo que o Conect identifique o responsável pela negociação antes mesmo de o contrato existir.

## Regras

- Cada `UsuarioEmpresa` recebe um token próprio e estável.
- O administrador principal da empresa também recebe um token próprio.
- O link pessoal usa `/e/{empresa}/pre-contrato/r/{token}`.
- O link genérico `/e/{empresa}/pre-contrato` continua válido como fallback da empresa.
- Ao salvar um pré-contrato vindo de link pessoal, a solicitação já nasce com `responsavel_contrato` e `responsavel_contrato_telefone`.
- A confirmação do pré-contrato no WhatsApp usa primeiro o responsável da negociação; o WhatsApp geral da empresa fica somente como fallback.
- O token é opaco e não expõe o ID do usuário.

## Perfil

O perfil do usuário passa a permitir cadastrar **Meu WhatsApp**. Para usuários comuns, o telefone é salvo em `usuarios_empresa.telefone`. Para o administrador principal, o nome e telefone pessoais usados no link são armazenados separadamente do WhatsApp geral da empresa.

## Compatibilidade

Links antigos e genéricos continuam funcionando. Eles apenas não definem um responsável automaticamente e, nesse caso, usam o WhatsApp geral da empresa.
