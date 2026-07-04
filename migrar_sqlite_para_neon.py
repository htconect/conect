"""
Migração do banco local SQLite (conect.db) para o Neon PostgreSQL.

Uso:
1) Instale as dependências:
   pip install -r requirements.txt

2) Defina a connection string do Neon:
   Windows PowerShell:
     $env:DATABASE_URL="postgresql://usuario:senha@host.neon.tech/neondb?sslmode=require"

   Mac/Linux:
     export DATABASE_URL="postgresql://usuario:senha@host.neon.tech/neondb?sslmode=require"

3) Execute:
   python migrar_sqlite_para_neon.py

Por padrão o script usa o arquivo conect.db na raiz do projeto.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models import Base


SQLITE_PATH = Path(os.getenv("SQLITE_PATH", "conect.db"))
DATABASE_URL = os.getenv("DATABASE_URL", "")


def normalizar_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def valor_convertido(valor: Any) -> Any:
    # SQLite guarda booleanos como 0/1. O SQLAlchemy/Postgres converte bem,
    # mas mantemos esta função para centralizar ajustes futuros se necessário.
    return valor


def carregar_linhas_sqlite(tabela: str) -> list[dict[str, Any]]:
    conexao = sqlite3.connect(SQLITE_PATH)
    conexao.row_factory = sqlite3.Row
    try:
        cursor = conexao.execute(f'SELECT * FROM "{tabela}"')
        return [
            {chave: valor_convertido(linha[chave]) for chave in linha.keys()}
            for linha in cursor.fetchall()
        ]
    finally:
        conexao.close()


def resetar_sequence_postgres(conexao, tabela: str, coluna_id: str = "id") -> None:
    conexao.execute(
        text(
            """
            SELECT setval(
                pg_get_serial_sequence(:tabela, :coluna),
                COALESCE((SELECT MAX(id) FROM """ + tabela + """), 1),
                true
            )
            """
        ),
        {"tabela": tabela, "coluna": coluna_id},
    )


def main() -> None:
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(f"Arquivo SQLite não encontrado: {SQLITE_PATH}")

    if not DATABASE_URL:
        raise RuntimeError("Defina a variável DATABASE_URL com a connection string do Neon.")

    if DATABASE_URL.startswith("sqlite"):
        raise RuntimeError("DATABASE_URL está apontando para SQLite. Use a connection string do Neon.")

    engine = create_engine(normalizar_database_url(DATABASE_URL), pool_pre_ping=True)

    print("Criando/validando tabelas no Neon...")
    Base.metadata.create_all(bind=engine)

    tabelas = [tabela for tabela in Base.metadata.sorted_tables]
    nomes_tabelas = [tabela.name for tabela in tabelas]

    with engine.begin() as conexao:
        print("Limpando tabelas no Neon...")
        conexao.execute(
            text(
                "TRUNCATE TABLE "
                + ", ".join(f'"{nome}"' for nome in reversed(nomes_tabelas))
                + " RESTART IDENTITY CASCADE"
            )
        )

        print("Migrando dados...")
        total_geral = 0

        for tabela in tabelas:
            linhas = carregar_linhas_sqlite(tabela.name)

            if not linhas:
                print(f"- {tabela.name}: 0 registros")
                continue

            conexao.execute(tabela.insert(), linhas)
            total_geral += len(linhas)
            print(f"- {tabela.name}: {len(linhas)} registros")

        print("Ajustando sequences...")
        for tabela in tabelas:
            if "id" in tabela.c:
                resetar_sequence_postgres(conexao, tabela.name)

    print(f"Migração concluída. Total migrado: {total_geral} registros.")


if __name__ == "__main__":
    main()
