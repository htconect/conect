# Horário mínimo de chegada ao cliente

- Novo parâmetro configurável na Inteligência, com padrão 08:00.
- A equipe pode sair da loja antes do horário mínimo.
- Entregas e retiradas não podem ter chegada prevista antes do limite configurado.
- Quando a rota chegaria antes, a linha do tempo aguarda até o horário permitido.
- O parâmetro é exibido nas configurações e no resumo da rota.
- Migração automática adiciona `horario_minimo_cliente` às bases existentes.
