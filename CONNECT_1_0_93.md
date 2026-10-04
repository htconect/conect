# CONNECT 1.0.93 — Cadastro de empresa + vitrine pública

## Objetivo
Primeira entrega da nova experiência visual do Connect, priorizando o que é urgente: cadastro guiado da empresa e vitrine pública para o cliente.

## Cadastro guiado da empresa
Nova rota `/painel/empresa`, organizada em blocos:
1. Empresa
2. Pagamento
3. Atendimento
4. Frete / deslocamento
5. Vitrine

O mesmo formulário pode ser salvo incompleto como rascunho e retomado depois pelo usuário ou pelo administrador que entrar na empresa.

### Imagens
Logo e capa passam pelo ajustador antes de serem usadas:
- enquadramento;
- zoom;
- posição horizontal/vertical;
- rotação;
- logo em 1:1;
- capa em 1400 x 617.

Também há botão para copiar um prompt de IA já com formato e contexto da empresa, sem integração direta com uma IA externa.

## Vitrine
Fluxo público:
`Data -> Produtos/serviços -> CEP -> Deslocamento -> Reservar -> Contrato existente`

O cliente só consegue reservar depois de informar o CEP e validar o deslocamento.

### Regras de deslocamento
Configuração por empresa:
- valor fixo;
- valor por KM;
- sob consulta.

No modo por KM, a empresa informa CEP de saída, valor por KM e multiplicador do trajeto. O Connect geocodifica os CEPs e usa a rota rodoviária existente para calcular a distância.

## Empresas novas sem vícios
- nenhuma empresa nova recebe produto exemplo de karaokê;
- nenhum recurso de estoque específico é criado automaticamente;
- InfinitePay não herda o handle da Karaokê RJ;
- recursos e produtos existentes das empresas atuais são preservados.

## Aparência
A personalização foi mantida intencionalmente curta:
- logo;
- capa;
- título;
- frase curta;
- descrição;
- cor principal;
- cor suave;
- três modelos simples: Clássico, Moderno e Divertido;
- texto do botão.

Não foi criada a parametrização extensa de temas da referência, pois adicionaria complexidade sem ganho proporcional.

## Compatibilidade
A tela antiga `/painel/configuracoes` continua disponível como configuração avançada. A operação, contratos, agenda, pagamento e financeiro existentes não foram substituídos nesta versão.
