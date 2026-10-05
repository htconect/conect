# LokaFest 1.0.22

- Empresas e logos ficam armazenadas no banco local do LokaFest.
- A Home não consulta mais o Organiza para montar a faixa de clientes.
- Novo ADM **Empresas / logos** com atualização manual sob demanda.
- A rotina baixa, otimiza para WebP e salva as miniaturas localmente.
- Logos usam cache longo e URL versionada por hash.
- A faixa pública é renderizada junto com a página, sem segundo fetch.
