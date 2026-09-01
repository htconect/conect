# Atualização — pagamento mobile v1.0.15

Ajustes específicos na página pública do contrato/pagamento para impedir overflow horizontal em celulares e reduzir textos.

A cobrança InfinitePay pendente permanece idempotente: se já existe checkout ativo, o Conect continua abrindo o mesmo link. Checkouts novos recebem o endereço/CEP do contrato; checkouts antigos não são modificados retroativamente.
