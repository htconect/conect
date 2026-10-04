# CONNECT 1.0.92 — Segurança com Humiat ID

Release de segurança sobre a 1.0.91. Não altera o fluxo operacional do Connect nem a nova vitrine pública.

## Proteções aplicadas

- Humiat ID passa a ser o acesso padrão e exclusivo em produção (`CONECT_LOCAL_LOGIN_ENABLED=false`).
- Credenciais locais humanas antigas são invalidadas uma única vez quando o login local está desligado.
- Removidas credenciais administrativas padrão do código/Render.
- Links públicos de contratos, PDF, aceite, cancelamento, pagamento, WhatsApp e confirmação usam token aleatório em vez de ID sequencial.
- Links numéricos antigos ficam desligados por padrão; compatibilidade temporária pode ser ativada com `CONECT_LEGACY_PUBLIC_CONTRACT_IDS=true`.
- Sessão configurada para cookie Secure/SameSite e headers de segurança HTTP.
- POSTs das páginas são protegidos contra origem externa (same-origin).
- Rate limit leve para login, gravações públicas e consulta pública de cadastro.
- Consulta pública por telefone não expõe mais nome, CPF/CNPJ, e-mail ou endereços apenas com o número; exige confirmação do CPF/CNPJ.
- Cadastro público impede alteração de cliente existente protegido sem confirmação do documento já cadastrado.
- Upload de imagens valida extensão, assinatura real do arquivo e tamanho máximo.
- Rotas de documentação OpenAPI ficam desligadas em produção por padrão.
- Scanners comuns recebem 404 antes de banco/sessão/monitor de performance.
- Páginas sensíveis de contrato/pagamento recebem `Cache-Control: no-store`.
- Uvicorn inicia sem expor o header de servidor.

## Variáveis recomendadas no Render

```env
CONECT_LOCAL_LOGIN_ENABLED=false
CONECT_SECURE_COOKIES=true
CONECT_SECURITY_HEADERS=true
CONECT_LEGACY_PUBLIC_CONTRACT_IDS=false
CONECT_API_DOCS=false
```

Mantenha `HUMIAT_SSO_SECRET` configurado com o mesmo segredo válido do Humiat ID e mantenha `SECRET_KEY` como segredo forte do Render.

## Compatibilidade de links antigos

A partir desta versão, novos links públicos sempre usam token seguro. Se houver contratos numéricos antigos já enviados a clientes e ainda ativos, é possível habilitar temporariamente:

```env
CONECT_LEGACY_PUBLIC_CONTRACT_IDS=true
```

Depois que esses contratos não precisarem mais ser acessados pelos links antigos, volte para `false`.

## Commit sugerido

`Connect 1.0.92 - reforca seguranca com Humiat ID e links publicos protegidos`
