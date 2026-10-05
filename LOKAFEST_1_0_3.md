# LokaFest 1.0.3

## Correção Cloud Run / PostgreSQL

- Mantida integralmente a estrutura do pacote de origem enviado em 01/10/2026, incluindo `.firebase`, `.firebaserc`, `firebase.json`, `public`, `static` e `templates`.
- Normalização da `DATABASE_URL` para o driver `psycopg2`, compatível com `psycopg2-binary` já instalado em `requirements.txt`.
- URLs `postgres://`, `postgresql://` e `postgresql+psycopg://` passam a usar `postgresql+psycopg2://` antes da criação do engine SQLAlchemy.
- Versão da aplicação atualizada para 1.0.3.
