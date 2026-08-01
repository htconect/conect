# Correção — Operação independente da Inteligência

## Alterações

- Removido o recálculo automático de todas as rotas inteligentes ao salvar, remanejar ou concluir um card da Operação.
- A Operação agora apenas grava sua própria atualização no banco, sem executar processamento da Inteligência.
- O botão de iniciar rota no Waze/Google Maps voltou a usar diretamente o endereço cadastrado.
- A navegação operacional não tenta mais geocodificar o endereço e não utiliza latitude/longitude salvas pela Inteligência.

## Resultado esperado

- Atualizações na Operação voltam a responder rapidamente.
- Falhas ou lentidão do serviço de geocodificação não bloqueiam o atendimento.
- Coordenadas calculadas pela Inteligência não interferem no destino aberto pelo Waze/Maps.
- A Inteligência continua lendo os dados atuais da Operação quando uma rota for gerada ou recalculada dentro do próprio módulo.
