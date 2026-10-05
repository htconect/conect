# LokaFest V35 - Produção

## Regra de duplicidade
- Mesmo WhatsApp + mesma categoria + oportunidade ainda aberta = bloqueia.
- Não cria nova indicação.
- Não gera crédito.
- Se a oportunidade anterior estiver encerrada, o cliente pode voltar.
- Futuramente, categorias diferentes podem coexistir para o mesmo WhatsApp.
- O telefone é normalizado; copiar e colar do WhatsApp/agenda funciona.

## Variáveis de ambiente no Render
DATABASE_URL=<postgresql/neon>
LOKAFEST_ADMIN_USUARIO=<usuario-admin>
LOKAFEST_ADMIN_SENHA=<senha-forte>
LOKAFEST_SESSION_KEY=<chave-longa-e-aleatoria>
ORGANIZA_API_URL=https://www.humiat.com.br/api/integracoes/lokafest/cliente
ORGANIZA_API_TOKEN=<mesmo-token-configurado-no-HUMIAT>

## Comando de start no Render
python -m uvicorn app:app --host 0.0.0.0 --port $PORT

## Git
git add .
git commit -m "Prepara LokaFest beta com bloqueio de duplicidade e deploy em producao"
git push origin main


## Verificações finais V37
- `indicacao_token` possui migração automática para bancos existentes.
- Todos os usuários recebem link pessoal `/indicar/<TOKEN>`.
- `/favicon.ico` responde com o logo do LokaFest.
- `/sw.js` responde sem 404 para navegadores com registro antigo.
- O anúncio flutuante do Conect aparece no painel e pode ser fechado.
- Timer de aceite configurável por `TEMPO_ACEITE_SEGUNDOS` (padrão 120).
