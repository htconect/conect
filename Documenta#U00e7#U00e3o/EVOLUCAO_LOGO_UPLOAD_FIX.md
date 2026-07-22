# Evolução — Logo no cadastro da empresa

## Correção realizada

A tela de criação/edição de empresa agora aceita envio de logo diretamente do PC ou celular.

Antes a tela ainda mostrava apenas o campo de URL, por isso a logo não aparecia como esperado.

## Ajustes

- Formulário de empresa passou a usar `enctype="multipart/form-data"`;
- campo de upload `logo_arquivo` incluído na criação/edição da empresa;
- arquivo salvo em `static/uploads/logos`;
- caminho salvo em `empresa.logo_url`;
- preview da logo atual exibido ao editar empresa;
- opção de URL ficou escondida em área avançada.

## Uso recomendado

No cadastro da empresa:

1. clique em **Enviar logo do PC ou celular**;
2. escolha PNG, JPG, WEBP, GIF ou SVG;
3. salve a empresa.

A logo será aplicada automaticamente nas telas que recebem a empresa no template.
