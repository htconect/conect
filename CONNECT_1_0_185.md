# Conect 1.0.185 — Diagnóstico do frete Google

- Log `[FRETE] deslocamento pendente` em recusas de cotação por KM, com a causa, inclusive falta do novo campo **Endereço completo da loja** obrigatório desde 1.0.184.
- Em erros HTTP da Routes API, registra somente código HTTP e status lógico; não registra chave de API.
- Vitrine deixa de informar falsamente que o endereço foi confirmado quando o frete ficou sob consulta.
- Preserva a razão `erro_rota` no registro de oportunidade pendente.
- Mantém frete sob consulta quando o Google não confirmar a rota; sem retorno ao OSRM.

## Antes de atualizar o código: verificar a causa provável

Em Conect → Empresas → Karaokê RJ → Frete por KM, preencha e salve **CEP de origem**, **Endereço completo da loja incluindo número, bairro, cidade e UF** e **valor por KM**. O campo endereço completo é novo e fica vazio após atualizar versões anteriores. Repita para Viviokê se usa frete por KM. Teste com o mesmo endereço de partida no Google Maps.

Se ainda estiver sob consulta, consulte Render → Logs, filtre `[FRETE]` após nova simulação:

- `Configure o CEP de origem e o valor por KM`: origem incompleta;
- `Cadastre o endereço completo da loja`: campo novo não preenchido;
- `A integração Google Maps Routes API não está configurada`: variável ausente;
- `Google Routes API HTTP 403 status=PERMISSION_DENIED`: verificar chave e restrições;
- `Google retornou local não confirmado/endereçamento parcial`: revisar endereços.

**Não precisa configurar outra chave nem alterar o Google Agenda.**
