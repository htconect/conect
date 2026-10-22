# Commit / Render — Connect 1.0.169

Substitua o código do projeto pela versão do ZIP (sem sobrescrever as configurações próprias de ambiente). Depois, no repositório Git:

```bash
git add .
git commit -m "fix(connect): unifica frete por pedido e corrige resumo do cadastro"
git push origin main
```

Se o Render estiver configurado com deploy automático para a branch `main`, acompanhe o deploy; caso contrário, use **Manual Deploy** na configuração do serviço Render.

Antes de publicar, teste localmente:

```bash
python -m py_compile app.py config.py
python -m pytest -q test_frete_unico_169.py test_vitrine_162.py test_vitrine_links_individuais_167.py test_vitrine_responsavel_retirada_166.py test_operacao_datas_165.py
```

**Atenção:** o teste antigo `test_frete_161.py::test_cep_valido_rota_incoerente_recupera_por_cep` continua falhando em uma string de identificação da fonte da geocodificação, não no valor do frete. Não foi alterada a rotina de rotas.
