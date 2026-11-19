# Conect 1.0.213 — opcionais e WhatsApp

## Regra comercial
- Os opcionais somam/subtraem somente do campo `valor_equipamentos` e do total final.
- `valor_frete`, descontos, horas adicionais e recebimentos anteriores não são modificados nem recalculados.
- Total original inconsistente com equipamentos - descontos + horas + frete: edição bloqueada, aviso de conferência para o atendimento. Não altera dados automaticamente.
- Mantém o mesmo registro de solicitação/contrato, preservando histórico de alterações e pagamentos.
- Na alteração efetiva, deixa pendente o envio de nova versão pelo WhatsApp. A mensagem passa a identificar o contrato atualizado, com os valores atuais.

## Experiência do cliente
- Exibe o valor do frete congelado no catálogo.
- Em salvamento lento, oferece link para consultar o resultado em vez de manter a cliente sem saída.
- Ao retornar pelo histórico do navegador, habilita novamente o botão de confirmação.
- Opção indisponível previamente contratada não é removida por ausência no POST de checkbox desabilitado.

## WhatsApp / aba em branco
- Links de rotas internas que usam HTTP 303 para abrir o WhatsApp deixam de usar `target="_blank"` na área do contrato, pendências, cadastro, links de pagamento e autorização da vitrine.
- Mensagens WhatsApp externas abertas por URL direta não foram afetadas.
- O Conect prepara a mensagem; o usuário precisa confirmar o envio no próprio WhatsApp.

## Validação
- `python -m pytest -q` — 81 testes passaram na base de desenvolvimento.

## Publicação
1. Substituir os arquivos do projeto pelos deste pacote (ou aplicar o `.patch` com `git apply`).
2. `git add app.py config.py templates/admin/solicitacao_detalhe.html templates/admin/painel.html templates/admin/cliente_detalhe.html templates/admin/vitrine.html templates/publico/opcionais_contrato.html test_opcionais_cliente_213.py ALTERACAO_OPCIONAIS_WHATSAPP_1.0.213.md`
3. `git commit -m "Corrige opcionais sem recalcular frete e redirecionamento WhatsApp"`
4. `git push origin main` (se o branch de produção for `main`).
5. Verificar no Render se o deploy foi concluído e testar em um contrato de teste antes de liberar ao cliente.

## Caso Francielly
O pacote não modifica dados no banco da produção; os logs enviados não mostram o POST que salvou os opcionais. Identifique no Conect a solicitação específica e confira `valor`, `valor_equipamentos`, `valor_frete`, `valor_desconto`, `valor_horas_adicionais` e `SolicitacaoOpcional` antes de qualquer correção retroativa. O id `259` nos logs não é prova de que corresponde à Francielly.
