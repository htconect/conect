# Diagnóstico temporário de performance

O monitor é controlado pelas variáveis do Render:

```env
PERFORMANCE_MONITORING=true
PERFORMANCE_DETAIL=slow
PERFORMANCE_ROUTES=/painel
PERFORMANCE_SLOW_REQUEST_MS=500
PERFORMANCE_SLOW_SQL_MS=300
```

## Onde consultar

- Logs do Render: procure por `PERF`.
- Administrador geral: `/admin/performance`.

O diagnóstico registra rota, duração total, quantidade e tempo de SQL, consulta mais lenta e etapas marcadas. Parâmetros SQL e dados pessoais não são registrados.

## Desativar após otimizar

```env
PERFORMANCE_MONITORING=false
```

Depois de alterar a variável no Render, faça um novo deploy/restart. O código permanece disponível para reativação futura.

## Alteração emergencial na home

A home não chama mais `garantir_agenda_reservas()` durante o `GET /painel`. Essa rotina varria e corrigia a Agenda em todo F5. Correções de consistência devem ser executadas fora da consulta diária.
