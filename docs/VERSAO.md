# HUMIAT Conect — Versão 1.0.3

Data: 31/08/2026

## Alterações
- Integração InfinitePay por empresa, com opção de ativar/desativar no cadastro/configuração da empresa.
- Karaoke RJ reaproveita a mesma InfiniteTag/conta InfinitePay utilizada no SolVoz.
- Após o aceite, o cliente escolhe somente **Sinal** ou **Valor integral**; não existe valor livre.
- Pré-tela exibe simulação de 1x a 12x usando a tabela de taxas InfinitePay cadastrada por empresa.
- Confirmação de pagamento por webhook e conferência complementar via `payment_check`.
- Pagamento confirmado cria automaticamente o pagamento do contrato e o lançamento financeiro na conta **InfinitePay**, já vinculado e conciliado.
- A conta financeira antiga **Cartão** é reaproveitada/renomeada para **InfinitePay** quando aplicável; PIX e cartão recebidos pela integração entram nessa mesma conta financeira.
- O fluxo manual de aprovação e pagamento permanece disponível.
- O primeiro usuário que envia o contrato para aceite fica registrado como responsável comercial do contrato, incluindo o WhatsApp do responsável.
- Após pagamento autorizado, o cliente vê apenas a mensagem de preparação; o sistema abre automaticamente o WhatsApp do responsável com o contrato pronto e o cliente só precisa tocar em **Enviar**.
- Se a confirmação da InfinitePay ainda estiver propagando, a tela consulta novamente automaticamente, sem exigir atualização manual do cliente.

## Commit padrão
`v1.0.3 - integra InfinitePay no Conect com pagamento e financeiro automáticos`
