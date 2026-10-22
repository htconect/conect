# Connect 1.0.168 — vitrine vinculada ao usuário logado

- Retirada a seção de links geral/pessoal/todos os atendentes do painel Vitrine; removidos os campos de link do Perfil, da Configuração e da lista ADM de empresas.
- **Ver vitrine** aponta para `?u=<código curto>` exclusivamente do usuário autenticado; **Compartilhar** é apenas um ícone WhatsApp que abre o aplicativo com uma mensagem contendo esse link.
- Se o usuário não tiver WhatsApp válido, não oferece vitrine genérica que possa encaminhar o contrato para outro número; mostra atalho de cadastro do perfil.
- Removido o link especial **direto sem aprovação** da configuração e seu mecanismo de sessão. Links diretos antigos autenticados por token redirecionam à vitrine comum, sem privilégios.
- O fluxo de reserva no carrinho volta a respeitar **`empresa.vitrine_fluxo`** (`direto` / `aprovacao`). Se estiver como `direto` (Não perguntar), segue ao cadastro e contrato; se `aprovacao`, aplica o fluxo de análise.
- Atribuição existente de responsável por `?u=...` ou links antigos `?r=...` preservada para não quebrar envios anteriores.
- Inalteradas as demais rotinas de contratos, pagamentos, frete, estoque e operação.

## Testes

- `python -m py_compile app.py config.py`
- `python -m pytest -q test_vitrine_links_individuais_167.py test_vitrine_162.py test_vitrine_responsavel_retirada_166.py`
- A suíte completa possui uma falha preexistente em `test_frete_161.py::test_cep_valido_rota_incoerente_recupera_por_cep` (assert da string `fonte`); este ajuste não alterou a rotina de frete.

## Após o deploy

1. Entrar como Junior e abrir **Ver vitrine**; conferir `?u=...` e a identidade Junior. Repetir com Débora e Luiz.
2. Compartilhar pelo ícone WhatsApp e confirmar que o link enviado é o pessoal, sem telefone exposto.
3. Em Configuração > Vitrine, deixar **Reserva direta** (“Não perguntar”). Simular reserva até contrato, aceite e pagamento com um produto que tenha modelo de contrato associado.
4. Verificar que um link antigo `/direto/...` não altera a regra.

Obs.: erro de aceite manual 400 do pedido 202 precisa de verificação do modelo de contrato e da mensagem de validação no banco de produção. Esta versão não aprova automaticamente nem altera esse pedido.
