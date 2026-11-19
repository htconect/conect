# Conect 1.0.214 — retirada no mesmo dia e horas adicionais após o aceite

Esta atualização **inclui integralmente a 1.0.213** (correção do cálculo dos opcionais, conservação do frete, histórico, reenvio de contrato e retirada das abas vazias do WhatsApp).

## O que muda

- **Cliente:** link permanente de **Catálogo de opcionais** permite marcar **Retirar no mesmo dia** e ajustar de 0 a 24 **horas adicionais**. Mostra antes de salvar a previsão de retirada, cobrança adicional e novo total. Preserva qualquer opcional marcado no mesmo envio.
- **Atendimento:** detalhe da solicitação no painel traz **Alterar retirada e horas extras**, sem precisar reabrir o aceite ou usar a edição completa que recalcula outros campos.
- Preços das horas: usa as configurações existentes em **Empresa** (na Karaokê RJ, primeira hora R$ 100, horas seguintes R$ 50). Com cortesia do próximo dia, horas adicionais = zero. Empresa sem cortesia permanece obrigatoriamente no mesmo dia.
- Horário: término = início + duração-base salva + horas extras. Retirada no mesmo dia não pode ocorrer após o limite configurado na empresa (Karaokê RJ: 22h); contratos com retirada em **outra data** não podem ser convertidos pelo catálogo e precisam de edição específica.
- **Frete congelado:** a edição não consulta CEP, distância, descontos ou frete. Apenas (a) opcionais alteram `valor_equipamentos` e (b) horas alteram `valor_horas_adicionais`. O total final incorpora cada uma dessas variações somente uma vez.
- Pagamentos e contrato original preservados. Não permite novo total abaixo do que já foi pago nem alteração enquanto há cobrança InfinitePay pendente. Bloqueia alteração após retirada operacional concluída.
- **Agenda:** o card Buscar recebe a data/hora nova. Quando o card já existe, preserva sua identidade e anota "Revisar rota e equipe". Quando a retirada deixa de ser obrigatória, volta ao dia seguinte com cortesia.
- **WhatsApp:** o contrato atualizado fica marcado para reenvio pelo atendimento, sem gerar outro contrato ou revogar o aceite já dado. Envio da mensagem continua confirmado manualmente no WhatsApp.
- Registra no histórico o valor anterior e novo, a descrição da alteração e os pagamentos realizados.
- A seleção de opcionais, quando for a única mudança, **não sobrescreve** o horário operacional que o atendente ajustou manualmente.

## Testes

`python -m pytest -q` — 89 testes passaram, incluindo testes com banco de dados de teste para:
- Uma hora extra, preço da empresa, frete congelado e retirada no mesmo dia.
- Retorno à cortesia no dia seguinte sem perder o card da busca.
- Impedir retirada após 22h e impedir conversão de contrato de vários dias.
- Bloquear alterações com retirada operacional já concluída.
- Alteração somente de horário pelo link público de opcionais.
- TV de R$ 80 + duas horas extras de R$ 150 no mesmo envio, sem dupla cobrança ao reenviar.
- Opcional sozinho mantendo a retirada ajustada manualmente.

## Como aplicar

**Se ainda não aplicou a 1.0.213:** use somente o `Conect_1.0.214_alteracoes_desde_original.patch` sobre o projeto da cópia `Conect(20261119-130031).zip` ou substitua os arquivos pelo ZIP completo 1.0.214. **Não aplique o patch antigo 1.0.213 depois da 1.0.214.**

1. Faça backup e pare alterações simultâneas no projeto.
2. Para aplicar o patch, coloque-o na pasta principal do Conect e execute `git apply --check Conect_1.0.214_alteracoes_desde_original.patch` e depois `git apply Conect_1.0.214_alteracoes_desde_original.patch`.
3. `git add app.py config.py templates/ test_opcionais_cliente_213.py test_personalizar_retirada_214.py ALTERACAO_OPCIONAIS_WHATSAPP_1.0.213.md ALTERACAO_RETIRADA_HORAS_OPCIONAIS_1.0.214.md`
4. `git commit -m "Permite alterar retirada e horas extras no contrato sem recalcular frete"`
5. `git push origin main` se essa for a branch de produção. Confirmar deploy do Render e testar primeiro em um contrato de teste.

**Atenção:** a atualização não recupera automaticamente valores que já ficaram incorretos nos contratos existentes (ex.: os R$ 370 relatados). O atendimento precisa verificar o contrato no banco antes de qualquer ajuste retroativo.
