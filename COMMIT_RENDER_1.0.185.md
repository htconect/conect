# Publicação do Conect 1.0.185

**Antes de publicar:** no painel do Conect, vá em Empresas → Karaokê RJ → Frete por KM e preencha e salve o novo campo **Endereço completo da loja (para cálculo pelo Google)**, incluindo número e cidade/UF. Confirme também CEP de origem e valor/km. Isso pode resolver o problema na versão 1.0.184, sem novo deploy.

Se precisar publicar o diagnóstico melhorado, substitua os arquivos da pasta do repositório com os deste ZIP e execute:

```bash
git add .
git commit -m "Conect 1.0.185 - Diagnostico frete Google Routes"
git push
```

O Render está configurado para publicar commits na branch `main` quando auto deploy estiver habilitado. Após subir e testar, procure `[FRETE]` nos **logs de aplicação** do serviço correspondente para identificar o motivo. O status HTTP 200 é compatível com frete sob consulta e não comprova cálculo da rota.

Não envie a chave da API pelo chat nem a inclua no Git. Verifique `GOOGLE_MAPS_API_KEY` no Render.
