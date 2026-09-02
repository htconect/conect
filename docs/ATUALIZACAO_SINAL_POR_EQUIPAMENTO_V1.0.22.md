# v1.0.22 — Sinal por equipamento

O campo `infinitepay_valor_sinal` passa a representar o valor do sinal por equipamento.
A quantidade é obtida pela soma de `ReservaItem.quantidade`. No aceite, o valor total calculado é salvo em `Solicitacao.sinal`, preservando o acordo após o aceite.

Exemplo: sinal configurado R$ 100,00 e 3 equipamentos => sinal R$ 300,00, limitado ao valor total do contrato.

Na home do painel foi removido o texto explicativo permanente abaixo de `Compartilhar Pré-Contrato`; o aviso permanece somente quando o WhatsApp do usuário não está cadastrado.
