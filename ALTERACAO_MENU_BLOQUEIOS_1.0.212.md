# Conect 1.0.212 — Menu Bloqueios

## Navegação
- Novo item **Bloqueios** no menu lateral (desktop), menu superior (mobile) e atalhos da página inicial.
- `/painel/bloqueios`: uma central com **Bloqueio geral (todos os equipamentos)** e **Bloqueio por equipamento (opcional)**.
- A tela Agenda mantém a indicação visual de datas já bloqueadas. O cadastro/remoção agora é concentrado na central.
- A Vitrine e Disponibilidade exibem links para o mesmo menu.

## Regras preservadas
- Bloqueio geral continua usando `bloqueios_data`, a mesma tabela e lógica anteriores, e os endpoints `/painel/agenda/bloqueios`.
- Bloqueio específico continua usando `bloqueios_produto` e os endpoints `/painel/vitrine/bloqueios-produtos`.
- Ambos são por empresa. Bloqueios específicos impedem reserva por período que cruze dias ocupados; não apagam contratos antigos.
- **Exceção existente preservada**: links especiais de reserva por período continuam ignorando o bloqueio geral de datas, mas não o específico. Caso deseje que o geral também afete links especiais, é uma alteração de regra de negócio separada.
- Permissões: usuário com acesso de Agenda pode gerenciar bloqueios gerais; usuário com acesso de Cadastros pode gerenciar por equipamento; acesso total pode gerenciar ambos.

## Instalação
1. Backup do banco Postgres.
2. Copiar os arquivos da versão 1.0.212 sobre o projeto (sem apagar outros arquivos).
3. `git add -A && git commit -m "Conect 1.0.212 - Menu central de bloqueios" && git push origin main`.
4. Render Auto Deploy ou Manual Deploy > Deploy latest commit.
5. Verificar `/painel/bloqueios` e bloquear um dia para a empresa inteira e outro somente para um produto.
