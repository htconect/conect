# Evolução: Pré-reserva profissional

## Decisões aplicadas

- O termo correto agora é **pré-reserva**, não pré-cadastro.
- O cliente existente pode ganhar uma **pré-reserva rápida** direto pela ficha do cliente, sem expor ou procurar dados publicamente.
- CPF e CNPJ são tratados como alternativas: **um ou outro, nunca os dois**.
- Pessoa física exige CPF válido, nome e data de nascimento.
- Pessoa jurídica exige CNPJ válido e não exibe data de nascimento.
- O formulário público foi dividido em blocos claros:
  1. Quem está reservando
  2. Endereço do evento
  3. Evento
  4. Responsável no local
- “Local do evento” foi separado em:
  - nome do local;
  - referência do local;
  - responsável no local;
  - telefone do responsável.
- Mensagens de WhatsApp ficam nas configurações da empresa, já pré-prontas e editáveis.
- Toda empresa nova recebe:
  - contrato padrão de locação;
  - produto de exemplo;
  - mensagens padrão.

## Arquivos alterados

- `models.py`
- `app.py`
- `utils.py`
- `templates/publico/cadastro.html`
- `templates/admin/painel.html`
- `templates/admin/configuracoes.html`
- `templates/admin/solicitacao_detalhe.html`
- `templates/admin/cliente_detalhe.html`
- `static/css/style.css`

## Próximo passo recomendado

Redesenhar a tela de agenda para trabalhar como fluxo de reserva:
pré-reserva → aceite → pagamento do sinal → reserva confirmada.
