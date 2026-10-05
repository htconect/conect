# LokaFest V1 — Projeto independente

Este projeto é separado do HUMIAT/Organiza. Não contém módulos, telas ou tabelas do Organiza.

## Rodar no PyCharm / Windows

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

Abra: `http://127.0.0.1:8000`

### Login inicial local
- Usuário: `admin`
- Senha: `admin123`

Em produção, configure as variáveis:
- `DATABASE_URL`
- `LOKAFEST_ADMIN_USUARIO`
- `LOKAFEST_ADMIN_SENHA`
- `LOKAFEST_SESSION_KEY`

## Escopo V1
- Home pública LokaFest na raiz `/`.
- Login próprio.
- Usuários com uma zona e produtos/serviços atendidos.
- Cadastro de produtos/serviços.
- Indicação: produto/serviço + data + zona + WhatsApp.
- Sorteio apenas entre usuários online, da zona, vinculados ao item e sem indicação aberta.
- Prioridade para quem gerou indicação.
- `Não fechou`: volta à fila e não retorna ao mesmo usuário.
- `Sucesso`: encerra.

As validações futuras com clientes/equipamentos/atualizações do Organiza ficaram fora desta V1 e poderão ser adicionadas por integração de consulta.


## Cadastros administrativos
- `/admin/produtos`: produtos e serviços, com edição e ativação/inativação.
- `/admin/zonas`: zonas de atendimento, com edição e ativação/inativação.


## V7 - Geografia nacional
Esta versão adiciona Estados, Municípios, Localidades e vínculo Localidade -> Área LokaFest.
A busca de local usa Nominatim/OpenStreetMap de forma explícita (botão Buscar, sem autocomplete contínuo).
O município é associado ao código oficial do IBGE quando possível.
Como `Indicacao.data_evento` passou a aceitar vazio e houve mudança estrutural, para teste local desta V7 apague `lokafest.db` antes da primeira execução.


## V14 - Validação Karaoke RJ
Somente a categoria **Karaokê** exige validação no Organiza.

Configure:
- `ORGANIZA_API_URL`
- `ORGANIZA_API_TOKEN` (opcional)

Contrato esperado do endpoint:
```json
{
  "encontrado": true,
  "cliente_id": "123",
  "cpf": "00000000000",
  "atualizacao": "2026.1",
  "equipamentos": {
    "jukebox": 1,
    "portatil": 0,
    "iphone": 1
  }
}
```

O LokaFest salva um cache da validação no cadastro do usuário:
quantidade de Jukebox, Portátil, iPhone, atualização e data da validação.
Assim não precisa consultar o Organiza em cada sorteio/operação.
