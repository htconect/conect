# Publicação Conect 1.0.184 — Git + Render

## Google Cloud
1. No projeto Google Cloud, habilite a **Routes API**, associe faturamento e crie uma chave de API restrita ao serviço **Routes API**.
2. Não coloque a chave nos arquivos do site, commits, conversas ou HTML. Mantenha a chave exclusivamente no Render em **Environment**.
3. Configure quota e alerta de orçamento no Google Cloud. As modalidades com trânsito podem custar mais que o modo sem trânsito.

## Render
Defina as variáveis de ambiente:

```
GOOGLE_MAPS_API_KEY=SUA_CHAVE_PRIVADA_NO_RENDER
GOOGLE_MAPS_ROUTES_TRAFFIC_AWARE=true
```

Não use uma chave real em arquivo `.env.example` ou em um commit Git.

A migração **aditiva** de `frete_endereco_origem` ocorre no startup leve do Render. Não é necessário rodar a manutenção pesada para este campo.

## Conect (por empresa que usa frete por KM)
No painel, abra **Empresa → Frete por KM** e preencha:
- **CEP de origem** (já existente, confira se é o CEP exato da loja).
- **Endereço de partida completo**, com rua e número, bairro, município e UF.
- **Valor por KM**, que permanece editável.

Teste em duas telas com a *mesma origem*, não com a posição genérica **Seu local** do Google Maps. Exemplo: Rua Jorge Kuraiem Filho, 4, Guaratiba, Rio de Janeiro/RJ, CEP 23042-550. Se não houver rota Google válida, o pedido segue como frete pendente de aprovação, sem faturar a distância calculada antes pelo OSRM.

## Git (executar na pasta do repositório, depois de substituir os arquivos)
```
git add app.py models.py config.py .env.example templates/admin/empresa_guiada.html templates/admin/empresas.html templates/admin/vitrine.html templates/admin/compartilhar_periodo.html templates/publico/vitrine.html test_frete_161.py test_vitrine_162.py test_google_routes_184.py test_vitrine_links_individuais_167.py CONNECT_1_0_184.md COMMIT_RENDER_1.0.184.md
git commit -m "feat: Conect 1.0.184 frete Google Routes e compartilhamento WhatsApp periodo"
git push origin main
```

Se o Render estiver configurado para deploy automático da branch `main`, ele fará o deploy após o push. Caso contrário, acione **Deploy latest commit** no painel.

## Checklist antes de disponibilizar
- API ativa e chave de servidor configurada no Render (não exposta ao navegador).
- Cada empresa com o endereço completo de origem correto.
- Google Maps com origem igual ao Conect e destino com rua/número/CEP idênticos.
- Frete da vitrine mostra os km de ida e ida + volta e multiplica pelo valor configurado.
- Chave ausente, endereço incompleto ou rota não encontrada: **sob consulta**, pedido vai para aprovação manual.
- Reserva por período abre WhatsApp em nova aba e oferece botão/link caso o navegador bloqueie redirecionamento automático.
- Ao visitar a oferta personalizada, o botão WhatsApp conserva o link específico com preço e datas.
