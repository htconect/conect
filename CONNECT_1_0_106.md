# Connect 1.0.106

- Migração automática e única da Karaokê RJ: preço normal atual + R$ 200,00; valor anterior vira preço específico Residencial; Empresa usa preço normal.
- Migração protegida por `app_migrations`, sem recadastro e sem repetir em cada deploy.
- Mensagens de Residencial/Empresa passam a ser configuradas no cadastro da empresa, não em cada item.
- Vitrine mostra a mensagem imediatamente abaixo do seletor de tipo de evento.
- Quando o preço específico for menor que o normal, a vitrine mostra preço normal riscado + Promoção do tipo de evento.
- Cadastro do item passa a chamar o valor-base de “Preço normal”.
