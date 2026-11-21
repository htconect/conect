# Conect v1.0.224 — bloqueio manual por cadastro, sem efeito cascata

- Bloquear um produto por data desativa **somente aquela oferta** de aluguel.
- O bloqueio manual do Portátil sozinho não impede os combos Portátil com JBL e Portátil Pro.
- Ao confirmar uma reserva do combo, o Conect continua consultando a disponibilidade física do Portátil e de todos os seus componentes obrigatórios. Falta de estoque físico impede a locação do combo.
- O bloqueio de data geral da empresa continua global.
- A alteração abrange vitrine, consulta de estoque API, painel de disponibilidade, confirmação final de contrato e mensagem de bloqueio.
- Não altera tabela, não apaga bloqueios existentes e não requer migração de banco.
- Bloqueio manual de **um combo específico** continua impedindo somente esse combo.

## Validação sugerida em produção

Com 3 Portáteis livres e JBLs suficientes, bloqueie apenas a oferta `Portátil` em uma data futura. A vitrine deve indicar `Portátil = 0`, enquanto `Portátil com JBL` e `Portátil Pro` apresentam saldo físico positivo. Confirme um combo na data e verifique que o saldo dos Portáteis diminuiu normalmente. Se todas as unidades físicas forem reservadas, os combos devem chegar a zero.
