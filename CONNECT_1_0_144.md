# Connect 1.0.144 — Edição dos nomes dos recursos

- `Cadastro > Recursos`: nome e quantidade editáveis na mesma página, com um único botão "Salvar alterações", seguindo o padrão do cadastro de opcionais.
- Renomeia **o recurso existente**, conservando seu ID, as quantidades e os vínculos com produtos, opcionais e solicitações. Não cria um novo recurso ao trocar o nome.
- Validação no servidor de nomes vazios, com mais de 140 caracteres, ou duplicados (independentemente de maiúsculas/minúsculas e incluindo inativos).
- Suporta troca simultânea de nomes de dois recursos sem violar a restrição UNIQUE do banco.
- Uma consulta de recursos por empresa para salvar as alterações; nenhuma consulta por linha.
- Impede que "Adicionar recurso" com nome repetido modifique silenciosamente o estoque já cadastrado.
- Todos os demais comportamentos da 1.0.143 (opcionais no contrato/aceite/WhatsApp/PDF) são preservados.

## Testar no Render

1. Renomear "TV" para "TV 32 Polegadas" e confirmar a atualização em Produtos, Opcionais e Recursos.
2. Verificar que quantidade e vínculos no estoque não mudaram após o novo nome.
3. Tentar nome duplicado e vazio — a aplicação deve impedir o salvamento e exibir um aviso.
4. Trocar nomes de dois recursos em uma única gravação.
5. Conferir uma solicitação existente e seu consumo de recursos.
