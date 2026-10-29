# Conect 1.0.179 — Utiliza brinde por empresa

- Adicionado `empresas.utiliza_brinde`, com valor inicial falso.
- Campo independente no ADM > Empresas > Funcionalidades do Connect.
- A opção é salva nas operações de criação e edição de empresa.
- Migração idempotente no startup leve (Render).
- Não altera contratos, opcionais, estoque, valores ou outras empresas.

**Limite conhecido:** a versão-base 1.0.178 não tem motor ou cadastro de regras de brinde. Este pacote adiciona o controle por empresa, mas não aplica brindes automaticamente e não copia regras inexistentes na base. Antes de implementar distribuição automática, é necessário definir gatilhos, quantidades, produtos elegíveis e forma de registrar o consumo no estoque.
