# HUMIAT Conect — Versão 1.0.11

## Fluxo único de contrato e pagamento, mobile e PIX

- O link público do contrato passa a ser o link permanente da reserva: aceite, primeiro pagamento, saldo e consulta final usam a mesma URL.
- A tela de contrato ainda não aceito foi redesenhada para celular com seções recolhíveis: dados do contrato, dados da locação, cláusulas e pagamento.
- O botão **Aceitar contrato** fica desabilitado até o cliente marcar **Li, conferi os dados e aceito o contrato**.
- Após o aceite, o cliente vê apenas a pergunta **Deseja passar para a etapa de pagamento?**.
- Empresas com InfinitePay continuam usando o checkout seguro com PIX/cartão e simulação de parcelamento.
- Empresas sem InfinitePay usam o PIX já cadastrado no Conect, com escolha de sinal/valor total e, depois de pagamento parcial, somente o saldo.
- Foram adicionados ao cadastro da empresa **Nome que aparece no PIX** e **Banco / instituição que aparece no PIX**.
- O preenchimento do pré-contrato não abre mais o WhatsApp automaticamente: os dados são salvos primeiro e o cliente decide se deseja avisar o responsável.
- Toda abertura de WhatsApp para o cliente usa o padrão: **Vamos abrir o WhatsApp com sua mensagem pronta. Quando a conversa abrir, basta tocar em Enviar.**
- O aceite não redireciona mais automaticamente para WhatsApp.
- Após o primeiro pagamento InfinitePay, o cliente pode abrir o WhatsApp para disponibilizar o contrato ou deixar o envio para o responsável.
- No segundo pagamento InfinitePay não há novo envio de contrato: apenas confirmação e agradecimento.
- Ao abrir o link com o contrato totalmente quitado, o cliente vê somente **Reserva concluída**, com opção de consultar o contrato.
- A mensagem de envio do link foi atualizada para destacar que a reserva aguarda aceite, que o cliente deve clicar no link e que ali encontrará informações de pagamento e parcelamento quando disponível.
- Mensagens antigas que ainda estejam exatamente no antigo padrão são atualizadas automaticamente; textos personalizados pela empresa são preservados.

Commit:

`v1.0.11 - unifica aceite e pagamentos no mesmo link e melhora fluxo mobile`
