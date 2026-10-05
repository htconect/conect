# Connect 1.0.116 — Horários da empresa e bloqueio de datas

## Horários: regra centralizada na empresa

- A duração padrão do contrato deixa de pertencer ao item e passa a pertencer à empresa/tipo de evento.
- A empresa pode definir duração para Residencial e Empresa.
- Para a Karaokê RJ, a migração aplica 4 horas para Residencial e 5 horas para Empresa.
- O item passa a apenas usar o padrão da empresa ou acrescentar horas ao padrão do tipo de evento.
- Quando há mais de um item, vale a maior extensão de duração encontrada; as extensões dos itens não são somadas entre si.
- O cadastro do item mantém preço por tipo de evento e permite configurar o acréscimo de horas por tipo.
- A ação "Aplicar a todos os itens" continua disponível para replicar preço e regra de horas.

## Retirada, cortesia e horas adicionais

- Configuração por empresa para cortesia de retirada no próximo dia.
- Configuração do limite de retirada no mesmo dia.
- Configuração separada para o valor da primeira hora adicional e das horas seguintes.
- Para a Karaokê RJ: primeira hora R$ 100,00, seguintes R$ 50,00 e limite de retirada no mesmo dia às 22:00.
- Ao solicitar retirada no mesmo dia, a cortesia deixa de valer.
- As horas adicionais atualizam horário de retirada e valor do contrato.
- Se o término ultrapassar o limite da empresa, a retirada no mesmo dia é impedida.

## Vitrine, contrato manual e aceite

- Vitrine, pré-contrato, contrato manual e aceite usam a mesma regra de duração da empresa/tipo de evento.
- No contrato manual, o tipo de evento e os itens determinam a duração final antes do aceite.
- No aceite público, o cliente vê duração, término, cortesia, retirada no mesmo dia e controles de horas adicionais antes de aceitar.
- O valor final é recalculado antes da confirmação do aceite.
- Textos fixos de "4 horas" foram substituídos por duração dinâmica da empresa.

## Agenda — bloqueio simples de datas

- A Agenda recebeu a ação "Bloquear datas".
- O bloqueio possui data inicial, data final e descrição opcional.
- O bloqueio é da empresa inteira nesta primeira etapa.
- A vitrine continua navegável, mas não permite novo pedido para uma data bloqueada.
- Novos contratos manuais também respeitam o bloqueio.
- Contratos já existentes não são invalidados por um bloqueio criado posteriormente.
- O bloqueio pode ser excluído pela Agenda.

## Fora desta versão

- Datas consecutivas/dias adicionais de locação não foram implementados.
- Combos/pacotes não foram implementados.
- Bloqueio por categoria, item ou quantidade ficou para uma evolução futura.
