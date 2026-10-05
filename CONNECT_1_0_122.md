# Connect 1.0.122

Hotfix de produção para a coluna `empresas.catalogo_musicas_url`.

- adiciona `catalogo_musicas_url` à migração estrutural leve executada no startup;
- mantém o startup rápido, sem reativar a manutenção pesada;
- configura o catálogo da Karaokê RJ somente quando o campo estiver vazio;
- corrige o erro 500 em telas que carregam `Empresa` após o deploy da v1.0.121.
