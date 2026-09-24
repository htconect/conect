# Connect v1.0.57 — Integração Google Agenda

## Objetivo

A integração mantém **um único evento do Google Agenda por contrato**. O evento acompanha o ciclo operacional do Connect, sem criar compromissos duplicados.

Fluxo:

1. **Contrato finalizado/aprovado** → cria o evento do contrato automaticamente.
2. **Operação / Entrega roteirizada e sincronizada** → atualiza o mesmo evento com a data e a hora da roteirização.
3. **Buscar / Retirada roteirizada e sincronizada** → atualiza o mesmo evento, substituindo a etapa de entrega.
4. **Buscar / Retirada encerrada** → exclui o evento do Google Agenda.

Uma etapa posterior nunca regride para uma anterior. Por exemplo, depois que o evento virou Retirada, uma sincronização da tela de Contratos não o transforma novamente em Contrato.

## Botão Google Agenda

O mesmo botão curto **Google Agenda** é usado em:

- Agenda / Contratos
- Operação

O botão trabalha em lote e respeita exatamente os filtros e os registros exibidos na tela.

### Agenda / Contratos

- Ao finalizar/aprovar o contrato, o envio é automático.
- O botão permite sincronizar novamente todos os contratos visíveis no filtro.
- Na sincronização em lote, entram contratos a partir da data atual e ainda não assumidos pela etapa operacional concluída.
- Se data ou hora forem alteradas, o mesmo evento é atualizado.

### Operação

- O botão sincroniza somente os registros visíveis no filtro atual.
- Somente itens roteirizados são enviados como Entrega/Retirada.
- A data e a hora usadas são as da roteirização.
- Entrega encerrada não apaga o evento: ele permanece até ser substituído pela Retirada.
- Retirada encerrada exclui o evento do Google Agenda.

## Status nos cards

Os cards indicam o estado da integração, incluindo:

- Não sincronizado
- Sincronizado
- Atualizar
- Erro
- Substituído / Finalizado, conforme a etapa

O Connect armazena o ID do evento e a assinatura dos dados sincronizados. Isso permite atualizar o mesmo compromisso e detectar alteração de data/hora sem gerar duplicidade.

## Configuração por empresa

No cadastro da empresa foi incluída a seção **Google Agenda** com:

- Usar Google Agenda nesta empresa
- Sincronizar Contratos
- Sincronizar Operação
- ID do calendário (padrão: `primary`)
- Lembrete 1 em minutos
- Lembrete 2 em minutos
- Duração padrão do compromisso operacional
- Conectar / desconectar conta Google
- Identificação da conta Google conectada

Cada empresa possui sua própria configuração e seus próprios tokens de conexão.

## Configuração no Google Cloud / Render

Antes de usar em produção:

1. Crie ou selecione um projeto no Google Cloud.
2. Ative a **Google Calendar API**.
3. Configure a tela de consentimento OAuth.
4. Crie uma credencial **OAuth 2.0 Client ID** do tipo **Web application**.
5. Cadastre como Redirect URI a URL pública do Connect terminando em:
   `/admin/google-calendar/callback`
6. No Render, configure:
   - `GOOGLE_CALENDAR_CLIENT_ID`
   - `GOOGLE_CALENDAR_CLIENT_SECRET`
   - `GOOGLE_CALENDAR_REDIRECT_URI`
7. Publique a versão e entre em **Empresa → Google Agenda → Conectar Google**.

O `.env.example` e o `render.yaml` desta versão já contêm os nomes dessas variáveis.

## Banco de dados

A aplicação cria automaticamente no startup as novas colunas necessárias para as configurações da empresa e o vínculo do contrato com o evento do Google.

## Versão

`1.0.57`
