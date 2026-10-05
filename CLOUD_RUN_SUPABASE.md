# LokaFest — Produção no Cloud Run + Supabase

## Arquitetura
- GitHub privado: código-fonte
- Google Cloud Run: FastAPI em `southamerica-east1` (São Paulo)
- Supabase PostgreSQL: `sa-east-1` (São Paulo)
- Desenvolvimento local: SQLite quando `DATABASE_URL` estiver vazia

## Variáveis obrigatórias no Cloud Run

- `APP_ENV=production`
- `DATABASE_URL=<URI Session Pooler do Supabase com senha percent-encoded>`
- `LOKAFEST_ADMIN_USUARIO=<usuario administrador>`
- `LOKAFEST_ADMIN_SENHA=<senha forte>`
- `LOKAFEST_SESSION_KEY=<chave aleatoria longa>`
- `ORGANIZA_API_URL=https://www.humiat.com.br/api/integracoes/lokafest/cliente`
- `ORGANIZA_API_TOKEN=<token da integração HUMIAT>`
- `TEMPO_ACEITE_SEGUNDOS=120`

Nunca grave segredos no GitHub.

## Banco novo

No primeiro start, o sistema cria automaticamente as tabelas e os dados básicos.

Na fase Beta, somente a categoria **Karaokê** é criada/ativada:
- Jukebox
- Portátil
- iPhone

As áreas de atendimento e a regra de catálogo obrigatório também são inicializadas.

## Health check

Acesse:

`/health`

Resposta esperada:

`{"status":"ok","database":"postgresql"}`

## Configuração inicial recomendada no Cloud Run

- Região: `southamerica-east1`
- CPU: 1 vCPU
- Memória: 512 MiB
- Concurrency: 40
- Min instances: 0
- Max instances: 1 no primeiro deploy

Depois que o banco estiver inicializado e testado, pode aumentar `max instances`.

## Checklist antes de liberar o Beta

1. Abrir `/health`.
2. Entrar com o administrador.
3. Confirmar que apenas Karaokê está ativa.
4. Cadastrar e aprovar 2 usuários de teste.
5. Testar indicação, sorteio, timer, aceite/passar, WhatsApp e encerramento.
6. Confirmar no Supabase que os dados foram gravados.
