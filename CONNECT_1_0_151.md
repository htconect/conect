# Connect 1.0.151 — exclusão segura de contratos

- Evita falha de chave estrangeira ao excluir pré-reserva criada na vitrine: desvincula e cancela apenas a oportunidade convertida correspondente, preservando seu histórico.
- Limpa histórico de opcionais e reserva de estoque da solicitação e desvincula roteiro logístico antes de excluir.
- Preserva o cadastro de cliente, mesmo quando seu único contrato é excluído.
- Impede exclusão física se houver pagamento registrado, cobrança/histórico InfinitePay, movimentação Humiat, repasse ou transferência; exibe motivo na própria tela.
- Em caso de integridade referencial inesperada, reverte a operação e exibe erro seguro em vez de HTTP 500, mantendo dados intactos.
- Não altera valores, cobranças, documentos nem relações de outras empresas.
