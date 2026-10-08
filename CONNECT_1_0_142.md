# Connect 1.0.142 — Aceite resiliente e pagamento em etapa própria

- Corrige o aceite que prendia o cliente na tela "Registrando seu aceite": a rotina registrava o aceite e então criava um checkout InfinitePay **na mesma solicitação HTTP**, podendo segurar a resposta até o serviço externo responder.
- Depois de persistir o aceite, responde com redirecionamento HTTP 303 para o contrato permanente `?aceite=ok`, que exibe a escolha "Sim, prosseguir" ou "Agora não". Não chama InfinitePay nem abre WhatsApp automaticamente.
- Somente após escolha expressa, a rotina de pagamento gera um checkout; mantém proteção de pagamento pendente e idempotência.
- Se a gravação/navegação demorar mais de 8 segundos, a interface apresenta uma ação de recuperação **Verificar situação do contrato**, usando GET no link existente e sem repetir o POST de aceite.
- A recuperação nunca presume aceite bem-sucedido; consulta o status real do contrato no banco.
- Inclui as correções da versão 1.0.141 para link de pré-reserva e cancelamento local InfinitePay.
- Sem migração de banco; preços e regras de operação mantidos.

## Validação de produção necessária
1. Aceitar contrato com InfinitePay: POST /aceitar retorna 303 e GET /contrato/?aceite=ok mostra pergunta de pagamento. Nenhum checkout deve nascer no POST /aceitar.
2. "Agora não" permanece no contrato. "Sim, prosseguir" mostra as opções Sinal e Integral e cria cobrança somente ao confirmar.
3. Repetir acesso ao contrato após aceite não consome Humiat nem cria outro aceite.
4. Se ocorrer timeout na navegação, "Verificar situação do contrato" lê o status sem reenviar o POST.
5. Verificar logs do POST de aceite desta cliente para saber se a confirmação já foi persistida antes de repetir.
