# Connect 1.0.166 — publicação no Git/Render

Pacote atualizado a partir de `Conect(20261014-134527).zip`.

Após substituir os arquivos do repositório pelos deste pacote, na raiz:

```bash
git add .
git commit -m "fix(connect): retirada obrigatoria editavel e responsavel da vitrine"
git push origin main
```

Se o branch principal no seu repositório não for `main`, substitua pelo branch utilizado pelo Render. Verifique o deploy e a versão 1.0.166.

**Conferência após publicar:**

1. `/painel/vitrine`: conferir `Responsável padrão do link público` e WhatsApp do Junior. Por padrão na Karaokê RJ, quando Junior tem WhatsApp cadastrado, o link geral passa a ser dele, inclusive se o legado apontava para outro atendente. Ao salvar a seleção no painel, ela passa a ser explícita e prevalece. Links pessoais seguem a pessoa do link.
2. Na reserva #167, usar `Salvar retirada` e trocar 19:00 por 20:00. A operação de busca pendente deve seguir 20:00 sem mudar o término de 16:00 nem os valores.
3. Na reserva que saiu como Luiz, usar `Corrigir responsável` e escolher Junior. O destino de contratos futuros/compartilhamentos da reserva passa a ser o WhatsApp dele; mensagens já enviadas não são reenviadas automaticamente.

**Banco:** migração leve em startup da coluna `vitrine_responsavel_configurado` (bool, padrão `false`). Não apague tabelas nem rode `DROP`.
