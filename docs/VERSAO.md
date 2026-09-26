# HUMIAT Conect — Versão 1.0.63

## Operação
- Exibe **Equipe tempo** = deslocamento puro entre endereços na ordem roteirizada manualmente.
- Exibe **Tempo para etapas** = deslocamento + tempo operacional da etapa anterior.
- Mantém instalação, desmontagem e pausa configuradas na Inteligência apenas como parâmetros de tempo.
- Não calcula peso/capacidade e não reorganiza a rota.

## Google Agenda
- Restaurados OAuth/configuração por empresa e botões **Sincronizar Google** em Contratos e Operação.
- Mantém um único evento por contrato e atualiza para Entrega/Retirada conforme sincronização operacional.
- Contrato finalizado/aceito volta a sincronizar automaticamente quando a empresa estiver conectada ao Google; ao encerrar a retirada, o evento é removido.

Commit Git/Render:
`Connect 1.0.63 - separa tempo de equipe e etapas e restaura Google Agenda`
