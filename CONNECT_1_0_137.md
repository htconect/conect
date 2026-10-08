# Connect 1.0.137 - Otimizacao das etapas publicas

- Corrigido N+1 em configuracao de campos: carregamento SQLAlchemy joinedload(CampoEmpresa.campo) nos formularios e contexto de contrato.
- Corrigido N+1 em taxas InfinitePay: consulta em lote das parcelas existentes, sem alterar valores ou regras.
- Mantidos dados e regras comerciais; nao ha migracoes de banco.
- Verificar no Render quantidade de SQLs nas rotas /e/{slug}/reserva, pre-contrato, e contrato.
- Esta alteracao nao corrige automaticamente a latencia fixa de rede (~113ms/SQL).
