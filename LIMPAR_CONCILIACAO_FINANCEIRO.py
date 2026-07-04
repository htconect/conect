"""Limpa apenas a conciliação financeira.

Não apaga clientes, reservas, contratos, pagamentos/aluguéis do sistema nem extratos importados.
Ele somente desfaz vínculos entre lançamentos do banco e pagamentos do sistema.

Uso:
    python LIMPAR_CONCILIACAO_FINANCEIRO.py
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("conect.db")

con = sqlite3.connect(DB)
cur = con.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lancamentos_banco'")
tem_banco = cur.fetchone() is not None
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pagamentos'")
tem_pagamentos = cur.fetchone() is not None

if tem_banco:
    cur.execute("UPDATE lancamentos_banco SET pagamento_id = NULL WHERE pagamento_id IS NOT NULL")
    banco_limpos = cur.rowcount
else:
    banco_limpos = 0

if tem_pagamentos:
    cur.execute("UPDATE pagamentos SET conciliado_em = NULL, conciliado_por = NULL WHERE conciliado_em IS NOT NULL OR conciliado_por IS NOT NULL")
    pagamentos_limpos = cur.rowcount
else:
    pagamentos_limpos = 0

con.commit()
con.close()
print(f"Conciliação limpa. Vínculos do banco: {banco_limpos}. Pagamentos liberados: {pagamentos_limpos}.")
