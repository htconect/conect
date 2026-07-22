# EVOLUCAO_FLUXO_CONTRATO_RESERVA

## Objetivo
Ajustar o sistema para refletir o fluxo real da operação: primeiro contrato, depois reserva, agenda e financeiro.

## Decisões aplicadas
- Enquanto depende do cliente, o registro é tratado como contrato.
- Depois do aceite do cliente, o registro passa a ser tratado como reserva.
- O aceite só pode acontecer uma vez.
- Após aceito, o cliente não consegue desmarcar o aceite nem aceitar novamente.
- Após aceito, a única ação pública disponível é cancelar.
- Financeiro fica depois da preparação do aceite e entra no fluxo da reserva.
- O link público sem busca é o contrato em branco.
- O link com busca por celular/CPF é apenas para cliente existente.
- Modelos internos foram renomeados para política/modelo de contrato, evitando confusão com contrato do cliente.

## Entregas realizadas
- Tela pública de contrato ajustada.
- Botão Aceitar bloqueado após aceite.
- Checkbox de aceite travado após aceite.
- Cancelamento permitido também depois do aceite.
- Criação de agenda protegida contra duplicidade.
- Status tratado visualmente como Contrato ou Reserva.
- Painel renomeado para Contratos/Reservas.
- Valores exibidos em padrão brasileiro.
- Financeiro filtrado para reservas confirmadas/aceitas.
- Documentação desta evolução criada.

## Pendências
- Validar visualmente o fluxo no navegador com os dados de teste.
- Decidir se o status interno deve ser migrado no banco para nomes definitivos em português.

## Próximo passo
Testar um fluxo completo:
contrato em branco -> preparação interna -> aceite do cliente -> reserva -> agenda -> financeiro.
