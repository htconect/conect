# Diagnóstico SQL agrupado

O monitor de performance agora agrupa todas as consultas SQL executadas em cada requisição por assinatura segura.

Para cada grupo são exibidos:

- operação SQL;
- tabelas envolvidas;
- quantidade de execuções;
- tempo total acumulado;
- tempo médio;
- maior execução;
- assinatura sem parâmetros.

Nenhum valor enviado nos parâmetros SQL é armazenado. O recurso pode ser desativado com `PERFORMANCE_MONITORING=false`.
