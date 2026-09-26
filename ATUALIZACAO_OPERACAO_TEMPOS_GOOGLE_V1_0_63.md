# HUMIAT Connect — Versão 1.0.63

- Operação passa a exibir **Equipe tempo** com o deslocamento puro entre os endereços na ordem manual.
- O primeiro trecho usa Loja → Cliente 1; os seguintes usam Cliente anterior → Próximo destino, inclusive Voltar à loja.
- **Tempo para etapas** continua considerando o serviço da etapa anterior (instalação, desmontagem ou pausa) somado ao deslocamento.
- O cálculo continua sem peso, capacidade do veículo ou reordenação automática.
- Restaurada a integração do **Google Agenda**: configuração por empresa, conexão OAuth e botões **Sincronizar Google** em Contratos e Operação.
- Restaurado o ciclo anterior do Google: contrato aceito/finalizado cria ou atualiza o compromisso; Entrega/Retirada reutilizam o mesmo evento; retirada encerrada remove o compromisso.

Commit sugerido:

`Connect 1.0.63 - separa tempo de equipe e etapas e restaura Google Agenda`
