# Evolução Reserva Profissional

## O que foi ajustado

- Corrigido o erro `405 Method Not Allowed` ao salvar produto em `/painel/produto/{id}`.
- Troca visual de "pré-reserva" para "reserva".
- Painel mais simples, com foco em quatro ações: Reserva, Agenda, Cliente e Financeiro.
- Link público da reserva voltou para baixo do nome da empresa.
- Incluído botão de compartilhamento por WhatsApp no painel.
- Cadastro da empresa/configurações com campo para link da logo no IDB.co.
- Mensagens automáticas configuráveis por empresa.
- Incluídas novas mensagens: preparação da equipe, equipe a caminho e envio de localização.
- Produto agora exige contrato padrão.
- Contrato padrão inicial sem variáveis, com texto fictício pronto para edição.
- Cadastro de produto/serviço com botão copiar.
- Cadastro de cliente com filtro por CPF ou telefone.
- Ficha do cliente mostra histórico de reservas.
- Financeiro com filtro de data inicial e final, iniciando em hoje.
- Agenda com roteiro por ordem, previsão de entrega e botões de WhatsApp.
- Evento com acesso ao local: térreo, elevador, escada ou elevador + escada.
- Configuração dos campos do cadastro público: mostrar e obrigatório por empresa.
- Horários mantidos de 30 em 30 minutos.

## Observação importante

O envio automático de localização em tempo real pelo WhatsApp não é liberado por link comum.
O sistema agora permite salvar e enviar um link de localização/rota. Para automação real, será necessário usar WhatsApp Business API ou integração externa.

## Próximo passo sugerido

Redesenhar a tela de reserva para virar um fluxo guiado:
cliente → produto → data/local → valores → enviar aceite → confirmar sinal.
