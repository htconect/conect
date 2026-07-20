# Integração Organiza → Financeiro

## Destino

`POST /api/integracoes/organiza/lancamentos`

O endereço completo é a URL do Connect + o caminho acima.

## Autenticação

Configure no Render a variável `ORGANIZA_API_KEY`.

O Organiza deve enviar o mesmo valor no cabeçalho:

`X-API-Key: SUA_CHAVE`

Se a variável não estiver configurada, a API aceita chamadas sem chave (útil apenas em desenvolvimento).

## JSON enviado

```json
{
  "id_externo": "ORGANIZA-12345",
  "tipo": "venda",
  "cliente": "João da Silva",
  "descricao": "Venda OS 1548",
  "valor": 500.00,
  "data_pagamento": "2026-07-20",
  "banco": "Banco Principal"
}
```

### Campos obrigatórios
- `id_externo`: identificador único do registro no Organiza.
- `tipo`: `venda` ou `manutencao`.
- `valor`: valor do lançamento, maior que zero.
- `data_pagamento`: formato `AAAA-MM-DD`.
- `banco`: nome do banco/conta informado no Organiza.

### Campos opcionais
- `cliente`
- `descricao`

## Regra de duplicidade

`id_externo` é único. Se o Organiza reenviar o mesmo ID, o Connect atualiza o registro existente em vez de criar duplicado.

## Exemplos

Venda:
```json
{
  "id_externo": "VENDA-1548-1",
  "tipo": "venda",
  "cliente": "João da Silva",
  "descricao": "Venda OS 1548",
  "valor": 500.00,
  "data_pagamento": "2026-07-20",
  "banco": "Banco Principal"
}
```

Manutenção:
```json
{
  "id_externo": "MAN-1548-1",
  "tipo": "manutencao",
  "cliente": "João da Silva",
  "descricao": "Manutenção OS 1548",
  "valor": 300.00,
  "data_pagamento": "2026-07-22",
  "banco": "Mercado Pago"
}
```

## Respostas

Novo registro: `{"ok": true, "acao": "criado", ...}`

ID já existente: `{"ok": true, "acao": "atualizado", ...}`

## Conferência

`GET /api/integracoes/organiza/lancamentos`

Usa o mesmo cabeçalho `X-API-Key` e retorna os últimos lançamentos recebidos.
