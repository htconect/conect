import os

APP_NOME = "HUMIAT Conect"
APP_VERSION = "1.0.114"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./conect.db")

# Render/Neon às vezes usa postgres://. SQLAlchemy espera postgresql://.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

SECRET_KEY = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")

# Segurança/autenticação. Em produção o Connect usa exclusivamente o Humiat ID.
# O login local existe apenas como escape explícito para desenvolvimento/recuperação.
LOCAL_LOGIN_ENABLED = os.getenv("CONECT_LOCAL_LOGIN_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
SESSION_COOKIE_SECURE = os.getenv("CONECT_SECURE_COOKIES", "true").strip().lower() in {"1", "true", "yes", "on"}
SECURITY_HEADERS_ENABLED = os.getenv("CONECT_SECURITY_HEADERS", "true").strip().lower() in {"1", "true", "yes", "on"}
LEGACY_PUBLIC_CONTRACT_IDS = os.getenv("CONECT_LEGACY_PUBLIC_CONTRACT_IDS", "false").strip().lower() in {"1", "true", "yes", "on"}
API_DOCS_ENABLED = os.getenv("CONECT_API_DOCS", "false").strip().lower() in {"1", "true", "yes", "on"}

# Sem credencial padrão. Se o login local for excepcionalmente habilitado,
# usuário e senha precisam ser definidos explicitamente no ambiente.
ADMIN_NOME = os.getenv("CONECT_ADMIN_NOME", "").strip()
ADMIN_SENHA = os.getenv("CONECT_ADMIN_SENHA", "").strip()

# Diagnóstico temporário de performance. Desative no Render após a otimização.
PERFORMANCE_MONITORING = os.getenv("PERFORMANCE_MONITORING", "true")
PERFORMANCE_DETAIL = os.getenv("PERFORMANCE_DETAIL", "slow")

# Integração NFS-e: o Conect apenas entrega os dados operacionais ao Organiza.
ORGANIZA_NFSE_URL = os.getenv("ORGANIZA_NFSE_URL", "https://humiat.com.br/organiza/nfse/importar-connect")
