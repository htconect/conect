# Atualização — Transferência entre empresas e navegação Waze

## Objetivo
Permitir que contratos transferidos entre empresas cadastradas no Conect sejam espelhados na empresa de destino, com operação e financeiro coerentes, e corrigir o fluxo de navegação para não abrir Waze e Google Maps ao mesmo tempo.

## Regras aprovadas

### Transferência para empresa cadastrada
- O contrato original permanece na empresa de origem.
- É criada uma cópia vinculada na empresa de destino.
- Cliente, texto do contrato, itens e agenda/operação são copiados para a empresa de destino.
- Pagamentos do cliente não são duplicados.
- O valor já recebido do cliente acompanha o contrato como `valor_pago`, reduzindo corretamente o saldo que ainda é devido pelo cliente na empresa de destino.
- O mesmo valor já recebido vira:
  - **A pagar / repasse** na empresa de origem.
  - **A receber da empresa de origem** na empresa de destino.
- A baixa do repasse continua sendo feita pelo lançamento bancário de saída da empresa de origem.
- Pagamentos parciais do repasse aparecem como parciais também na empresa de destino.
- A cópia interna não gera nova cobrança HUMIAT.

### Transferência para “Outros” / externo
- Não cria cópia de contrato.
- Mantém a regra anterior de repasse e o valor informado manualmente.

### Navegação
- Desktop: abre Waze Web.
- Android: usa `intent` do Waze com Google Maps como fallback nativo.
- iOS: tenta o aplicativo Waze e só usa Google Maps se a página continuar ativa, cancelando o fallback ao detectar que o aplicativo assumiu a tela.

## Arquivos principais alterados
- `models.py`
- `app.py`
- `templates/admin/solicitacao_detalhe.html`
- `templates/admin/financeiro.html`
- `templates/admin/preparar.html`

## Banco de dados
Foram adicionados automaticamente à tabela `solicitacoes`:
- `transferencia_origem_id`
- `transferencia_copia_id`

A migração segue o mecanismo automático já existente no projeto.
