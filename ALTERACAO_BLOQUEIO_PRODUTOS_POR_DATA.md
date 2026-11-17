# Conect — Bloqueio de equipamentos por data

## Uso
Painel → Vitrine → **Bloquear aluguel de equipamento por data**. Selecione modelo, início, fim (inclusive) e motivo opcional; salve. Os bloqueios ativos futuros aparecem nessa tela com opção **Remover bloqueio**.

## Comportamento
- Bloqueio é por empresa e produto; não altera estoque físico nem cancela contratos existentes.
- Nova locação no dia bloqueado vê disponibilidade zero na vitrine pública e no painel de disponibilidade.
- Também se aplica a links personalizados de reserva por período, mesmo quando ignoram o bloqueio **geral** da agenda.
- Um aluguel de vários dias é barrado se algum dia de ocupação cruzar o bloqueio. O dia da retirada não conta como ocupação.
- No cadastro interno, contratos novos ou alteração da data/produto também respeitam bloqueios.
- A tabela `bloqueios_produto` é criada automaticamente no startup, mesmo quando a manutenção completa estiver desabilitada. Não modifica `bloqueios_data`.

## Teste de aceitação manual
1. Bloquear um equipamento em 24/12–26/12; conferir quantidade 0 nesse período na vitrine e no painel de disponibilidade.
2. Conferir que outro equipamento permanece disponível na mesma data.
3. Gerar link personalizado com ocupação cruzando 25/12: deve recusar.
4. Conferir que reserva retornando em 24/12 (última ocupação no dia 23) não sofre esse bloqueio.
5. Remover bloqueio e confirmar disponibilidade normal. Verificar que contratos antigos permanecem inalterados.

## Implantação
Substituir os arquivos modificados, publicar pelo fluxo Git/Render normal. O startup executa `CREATE TABLE IF NOT EXISTS` pelo SQLAlchemy exclusivamente para a nova tabela. Precisa de permissão `CREATE` no esquema. Fazer backup do banco antes de implantar.
