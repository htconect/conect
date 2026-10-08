# Connect 1.0.146 — Catálogo de opcionais, fotos e controle de estoque

## O que mudou

- Empresas configuram **Controla estoque?**; se não, vitrine e contrato manual/automático continuam sem exigências de estoque.
- Telas usam o termo **Estoque** no lugar do antigo nome **Recursos**; modelos e IDs permanecem intactos.
- Contrato manual e vitrine: opcionais selecionados por **checkbox**; cada marcação adiciona a quantidade cadastrada no opcional, com preço unitário multiplicado pela quantidade; vários opcionais podem ser selecionados.
- Disponibilidade do opcional verificada para a data do evento; quando falta estoque, o item fica desabilitado. O servidor valida novamente.
- Cadastro → Opcionais: enviar foto para cada opcional já salvo; miniatura exibida no cadastro, vitrine e catálogo do cliente. O arquivo fica no armazenamento de mídia do banco usado pelo Connect.
- Link do contrato oferece acesso ao catálogo de opcionais para clientes de contratos manuais ou da vitrine, inclusive depois do aceite.
- Cliente pode incluir/remover opcionais, confirmar a nova composição e salvar sem repetir o aceite; o aceite original é preservado.
- A **soma das remoções não pode superar o saldo ainda não pago**; se o contrato estiver quitado, nenhuma remoção é permitida. Inclusões continuam permitidas, respeitando restrições de cobrança InfinitePay pendente.
- Recalculados valor total e saldo sem alterar pagamentos recebidos, descontos ou frete; sem estorno automático.
- Alterações são registradas em histórico; criam **pendência para o atendente reenviar o contrato atualizado pelo WhatsApp**.
- Mensagens WhatsApp oferecem o link de opcionais; botão de envio do catálogo disponível na solicitação.
- Ajustes manuais de estoque do contrato são preservados ao incluir/remover opcionais, com atualização de quantidades.

## Migração de banco

A inicialização da aplicação contém migração idempotente para foto_url, sinalizadores da solicitação e tabela de histórico de opcionais. Não é necessário apagar ou recriar registros.

## Validação local

- TestClient com SQLite temporário: inclusão de opcional em quantidade de pacote 2, idempotência, pagamento parcial, bloqueio de remoções acima do saldo, inclusão após pagamento, empresa sem estoque.
- Estoque com 1 unidade para opcional que exige 2: bloqueio na página e no POST.
- Estoque com ajuste manual: inclusão e remoção atualizam a quantidade reservada.
- Sintaxe Python verificada. Testar interface e PostgreSQL/Render após deploy, antes de liberar para todos.

## Implantação

```bash
git add .
git commit -m "v1.0.146 - Catalogo de opcionais com fotos, saldo protegido e estoque opcional"
git push origin main
```

Faça backup do banco antes do primeiro deploy com migração. Verifique os logs de inicialização e os fluxos de aceite, pagamento e reenvio do contrato no ambiente de produção.
