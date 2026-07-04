import os

APP_NOME = "HUMIAT Conect"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./conect.db")

# Render/Neon às vezes usa postgres://. SQLAlchemy espera postgresql://.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

SECRET_KEY = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")

ADMIN_NOME = os.getenv("CONECT_ADMIN_NOME", "Admin")
ADMIN_SENHA = os.getenv("CONECT_ADMIN_SENHA", "humiat123")
