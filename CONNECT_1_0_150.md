# Connect 1.0.150 — abertura do checkout InfinitePay

- Corrige a possibilidade de bloqueio de redirecionamento ao domínio InfinitePay depois do POST, com política CSP `form-action 'self'` ativa.
- Ao criar ou reutilizar cobrança existente, o POST redireciona para uma página GET interna, que abre a InfinitePay e oferece link visível de contingência.
- O link do cliente com cobrança aguardando pagamento abre a **mesma cobrança**, sem gerar outra.
- No painel interno, cobranças aguardando pagamento apresentam botão **Abrir InfinitePay**.
- Nenhuma regra financeira, de estoque, contrato, status ou banco de dados foi modificada.

## Verificação após o deploy

1. Abrir contrato aceito, escolher pagar sinal/integral e clicar para pagar.
2. Conferir navegação para checkout; se não redirecionar, a página oferece botão direto.
3. Voltar ao link do contrato e repetir a operação; confirmar que **não** cria outra cobrança.
4. No painel interno, clicar em **Abrir InfinitePay** na cobrança aguardando pagamento.
5. Repetir no navegador do celular / dentro do WhatsApp.
