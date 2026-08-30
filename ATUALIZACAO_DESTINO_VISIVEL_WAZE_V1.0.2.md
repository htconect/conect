# HUMIAT Conect v1.0.2 — Destino visível e comparável

## Objetivo
Permitir verificar em produção se uma divergência de rua/número ocorre dentro do Conect ou na interpretação do aplicativo de navegação.

## Regra única
O texto exibido em **Operação > Destino** é exatamente a string usada pelos botões **A caminho** e **Iniciar rota**.

Formato:

`LOGRADOURO, NÚMERO, BAIRRO, CEP XXXXX-XXX`

Exemplo:

`Rua Engenheiro Edmundo Regis Bittencourt, 106, Olaria, CEP 21000-000`

## Fora da navegação
- complemento;
- apartamento;
- bloco;
- sala;
- nome do local;
- latitude/longitude nesta versão de diagnóstico.

## Waze
O Waze recebe `q=<destino visível>&navigate=yes`. Dessa forma, o operador pode comparar o Destino exibido no card com o endereço que o Waze resolveu.

## Google Maps
O Maps recebe o mesmo texto em `query=<destino visível>`.
