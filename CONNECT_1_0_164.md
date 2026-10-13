# Connect 1.0.164 — responsável da vitrine e links curtos

- Configurar responsável padrão no painel Vitrine, com seleção de número cadastrado e ativo.
- Link pessoal da vitrine para cada operador (recebe contratos), link genérico usa padrão.
- Atendente acompanha a vitrine, link de compartilhamento, checkout e contrato, inclusive WhatsApp de aceite/pagamento.
- Sem padrão ativo: escolher primeiro contato cadastrado com WhatsApp válido; sem número válido não inventar.
- Link curto `/e/empresa/s/codigo` com escolhas persistidas por 30 dias sem CPF/WhatsApp; precificação e estoque revalidados na abertura.
- Links legados grandes seguem funcionando.
- Banco: nova coluna `empresas.vitrine_responsavel_token` e tabela `vitrine_compartilhamentos`, criadas na inicialização leve.
