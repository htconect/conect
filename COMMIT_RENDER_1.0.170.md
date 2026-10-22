# Git / Render — Connect 1.0.170

1. Extraia o ZIP completo sobre o projeto do Connect preservando os arquivos de ambiente e de banco de dados locais.
2. Na raiz do repositório, execute:

```bash
git add .
git commit -m "fix(connect): v1.0.170 mobile InfinitePay e estoque operacional com opcionais"
git push origin main
```

3. Se o Auto Deploy estiver ativado no Render, ele publica o commit automaticamente. Caso contrário, abra o serviço Render e acione o deploy manual do commit.

## Revisão
- Verificar no celular a seção **Cobranças InfinitePay**.
- Em **Operação**, abrir **Estoque do dia**, escolher uma data com entregas e conferir quantidades, ajustes e vínculos dos opcionais.
- Confirmar se entregas/retiradas concluídas estão corretamente marcadas, porque determinam o saldo na rua.
- A consulta não altera estoque físico, contratos nem registros financeiros.

Testes: 50 aprovados, 1 falha antiga de geocodificação textual no teste de frete.
