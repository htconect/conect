# HUMIAT Conect — Versão 1.0.18

## Fluxo público / WhatsApp
- Pré-contrato continua sendo salvo antes de abrir o WhatsApp.
- O botão "Agora não" foi substituído por "Deixar para o responsável".
- O Conect registra quando o cliente clicou em "Abrir WhatsApp" e quando escolheu deixar a comunicação para o responsável.
- O registro de clique não é tratado como envio confirmado, porque o WhatsApp não devolve essa confirmação ao Conect.
- Após o aceite digital, a etapa de WhatsApp agora é realmente exibida.
- A mensagem de aceite é direcionada ao responsável do contrato; se não houver responsável fixado, usa o WhatsApp de retorno da empresa.
- O primeiro pagamento também registra se o cliente clicou no WhatsApp ou deixou o envio do contrato para o responsável.
- As pendências e o histórico do contrato passam a mostrar essas escolhas.

## Aceite manual
- O aceite manual passa a registrar usuário, motivo, data e status anterior.
- Foi incluída a ação "Excluir aceite manual" na tela do contrato e na busca do cliente.
- A exclusão é bloqueada se já houver pagamento, cobrança InfinitePay em andamento, contrato final marcado como enviado ou operação iniciada.
- Ao desfazer um aceite manual seguro, o contrato volta ao status anterior, os eventos operacionais pendentes são removidos e o Humiat é estornado sem apagar o histórico.
- Aceites manuais antigos são reconhecidos pela anotação histórica "Aceite manual por ...".
- O aceite digital do cliente nunca é removido por essa função.

## Commit sugerido
`v1.0.18 - corrige WhatsApp do cliente e adiciona exclusão segura do aceite manual`
