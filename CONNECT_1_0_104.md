# Connect 1.0.104

- Cadastro central de opcionais por empresa (nome, quantidade, valor, ativo e ordem).
- Produto/serviço passa a ter apenas a chave “utiliza opcionais” e pode excluir opcionais específicos sem duplicar cadastros.
- Migração compatível dos opcionais antigos por item para o catálogo central.
- Vitrine pública movida para logo abaixo de Início no menu principal.
- Carrinho da vitrine passa a listar itens, quantidades, opcionais, data, tipo de evento, desconto, deslocamento e total.
- CEP é enriquecido com logradouro/bairro/cidade/UF quando disponível; geocodificação usa o endereço completo antes do fallback por CEP.
- Botafogo/RJ passa a ser apresentado como bairro + Rio de Janeiro/RJ quando o CEP resolver esses dados.
