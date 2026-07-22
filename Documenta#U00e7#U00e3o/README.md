# HUMIAT Conect

Sistema separado do Organiza para pré-cadastro, contratos, aceite e agenda.

## Perfis de acesso

### Administrador Geral
Cria e edita empresas. Não entra no painel operacional das empresas.

Credenciais padrão:
- Usuário: `Admin`
- Senha: `humiat123`

Variáveis opcionais:
- `CONECT_ADMIN_NOME`
- `CONECT_ADMIN_SENHA`

### Empresa
Cada empresa acessa somente seus próprios dados:
- pré-cadastros
- produtos e serviços
- contratos
- agenda

O usuário e senha da empresa são criados pelo Administrador Geral.

## Rotas principais

- `/admin/login` — login do Administrador Geral
- `/admin` — cadastro/edição de empresas
- `/empresa/login` — login da empresa
- `/painel` — painel operacional da empresa
- `/e/{slug}` — link público de pré-cadastro do cliente

## Rodar local

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

## Render

Start Command:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```


## V5 - Ajustes de segurança e contrato

- Busca pública aceita telefone ou CPF.
- Dados antigos só aparecem após confirmação do CPF.
- CEP com busca rápida.
- Horários em blocos de 30 minutos.
- Hora final calculada automaticamente pela duração do produto/serviço.
- Empresa configura PIX copia e cola.
- Empresa configura horário de suporte e escolhe se aparece no contrato.
- Contrato tem botão de cancelamento.
- Empresa pode informar logo da página pública.
- Três temas disponíveis: azul, escuro e claro.
