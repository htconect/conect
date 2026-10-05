import hashlib
import hmac
import os
import re
import secrets
import json
import time
import unicodedata
import urllib.parse
import urllib.request
from dotenv import load_dotenv
from datetime import date, datetime, timedelta
from urllib.parse import quote_plus
from io import BytesIO

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint, create_engine, func, inspect, text, or_
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
DATABASE_URL = os.getenv("DATABASE_URL", "").strip() or f"sqlite:///{os.path.join(BASE_DIR, 'lokafest.db')}"
# O projeto instala psycopg2-binary. Normaliza URLs antigas/externas para
# o dialeto compatível antes de o SQLAlchemy carregar o driver.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
if DATABASE_URL.startswith("postgresql+psycopg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

IS_SQLITE = DATABASE_URL.startswith("sqlite")
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

if IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
else:
    connect_args = {}
    if "supabase.com" in DATABASE_URL and "sslmode=" not in DATABASE_URL:
        connect_args["sslmode"] = "require"
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=5,
        connect_args=connect_args,
    )
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

ADMIN_USUARIO = os.getenv("LOKAFEST_ADMIN_USUARIO", "admin")
ADMIN_SENHA = os.getenv("LOKAFEST_ADMIN_SENHA", "admin123")
CHAVE_SESSAO = os.getenv("LOKAFEST_SESSION_KEY", "lokafest-dev-key-change-me")
ORGANIZA_API_URL = os.getenv("ORGANIZA_API_URL", "").strip()
ORGANIZA_API_TOKEN = os.getenv("ORGANIZA_API_TOKEN", "").strip()
ORGANIZA_PUBLIC_BASE_URL = os.getenv("ORGANIZA_PUBLIC_BASE_URL", "").strip().rstrip("/")
if not ORGANIZA_PUBLIC_BASE_URL:
    try:
        _organiza_parts = urllib.parse.urlsplit(ORGANIZA_API_URL)
        if _organiza_parts.scheme and _organiza_parts.netloc:
            ORGANIZA_PUBLIC_BASE_URL = f"{_organiza_parts.scheme}://{_organiza_parts.netloc}"
    except Exception:
        ORGANIZA_PUBLIC_BASE_URL = ""
if not ORGANIZA_PUBLIC_BASE_URL:
    ORGANIZA_PUBLIC_BASE_URL = "https://www.humiat.com.br"
HUMIAT_SSO_SECRET = os.getenv("HUMIAT_SSO_SECRET", "").strip()
HUMIAT_SSO_VALIDATE_URL = os.getenv("HUMIAT_SSO_VALIDATE_URL", "https://www.humiat.com.br/api/humiat/sso/validar").strip()
HUMIAT_PORTAL_URL = os.getenv("HUMIAT_PORTAL_URL", "https://www.humiat.com.br/painel").strip()
LOKAFEST_GRUPO_WHATSAPP_URL = os.getenv("LOKAFEST_GRUPO_WHATSAPP_URL", "").strip()
LOKAFEST_PUBLIC_URL = os.getenv("LOKAFEST_PUBLIC_URL", "https://lokafest.com.br").strip().rstrip("/")
TEMPO_ACEITE_SEGUNDOS = max(30, int(os.getenv("TEMPO_ACEITE_SEGUNDOS", "120")))
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
IS_PRODUCTION = APP_ENV == "production"
ZONAS = ["Zona Norte", "Zona Sul", "Zona Oeste", "Centro"]
APP_VERSION = "1.0.23"
EQUIPAMENTOS_INDICACAO = {
    "portatil": "Portátil",
    "jukebox": "Jukebox",
    "iphone": "iPhone",
}

app = FastAPI(title="LokaFest", version=APP_VERSION)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    caminho = os.path.join(BASE_DIR, "static", "lokafest", "favicon.ico")
    if os.path.exists(caminho):
        return FileResponse(caminho, media_type="image/x-icon", headers={"Cache-Control": "no-store, max-age=0"})
    return Response(status_code=204)


@app.get("/apple-touch-icon.png", include_in_schema=False)
@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
def apple_touch_icon():
    caminho = os.path.join(BASE_DIR, "static", "lokafest", "apple-touch-icon.png")
    if os.path.exists(caminho):
        return FileResponse(caminho, media_type="image/png", headers={"Cache-Control": "no-cache"})
    return Response(status_code=204)




@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest_webmanifest():
    return JSONResponse({
        "name": "LokaFest",
        "short_name": "LokaFest",
        "description": "Plataforma de indicações para festas e eventos",
        "start_url": "/painel",
        "scope": "/",
        "display": "standalone",
        "background_color": "#f4f7fb",
        "theme_color": "#6B21A8",
        "icons": [
            {"src": "/static/lokafest/icon-192.png?v=8", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/static/lokafest/icon-512.png?v=8", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    }, headers={"Cache-Control": "no-store, max-age=0"})

@app.get("/sw.js", include_in_schema=False)
def service_worker_placeholder():
    # Evita 404 em navegadores que procuram um service worker antigo.
    return Response(
        content="self.addEventListener('install',()=>self.skipWaiting());self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
MAX_REPASSES_INDICACAO = max(1, int(os.getenv("MAX_REPASSES_INDICACAO", "6")))

def data_br(valor):
    if not valor:
        return ""
    try:
        return valor.strftime("%d/%m/%Y")
    except Exception:
        return str(valor)

templates.env.filters["data_br"] = data_br


def _novidade_itens(novidade):
    if not novidade or not novidade.itens_json:
        return []
    try:
        itens = json.loads(novidade.itens_json)
        return itens if isinstance(itens, list) else []
    except Exception:
        return []


def novidade_ativa():
    db = SessionLocal()
    try:
        novidade = db.query(Novidade).filter(Novidade.ativo == 1).order_by(Novidade.id.desc()).first()
        if novidade:
            novidade.itens = _novidade_itens(novidade)
        return novidade
    finally:
        db.close()


templates.env.globals["novidade_ativa"] = novidade_ativa
templates.env.globals["app_version"] = APP_VERSION


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False)
    usuario = Column(String(80), unique=True, nullable=False)
    # Identidade central Humiat. Campos opcionais para preservar cadastros antigos.
    email = Column(String(180), nullable=True)
    humiat_user_id = Column(String(64), nullable=True)
    whatsapp = Column(String(30), nullable=False, default="")
    senha_hash = Column(String(255), nullable=False)
    zona = Column(String(40), nullable=False, default="Zona Norte")
    is_admin = Column(Integer, nullable=False, default=0)
    ativo = Column(Integer, nullable=False, default=1)
    aprovado = Column(Integer, nullable=False, default=1)
    online = Column(Integer, nullable=False, default=0)
    prioridade_creditos = Column(Integer, nullable=False, default=0)
    criado_em = Column(DateTime, server_default=func.now())
    cpf = Column(String(20), nullable=True)
    krj_validado = Column(Integer, nullable=False, default=0)
    krj_cliente_id = Column(String(60), nullable=True)
    krj_jukebox_qtd = Column(Integer, nullable=False, default=0)
    krj_portatil_qtd = Column(Integer, nullable=False, default=0)
    krj_iphone_qtd = Column(Integer, nullable=False, default=0)
    krj_fliperama_qtd = Column(Integer, nullable=False, default=0)
    krj_atualizacao = Column(String(40), nullable=True)
    krj_validado_em = Column(DateTime, nullable=True)
    krj_equipamentos_json = Column(Text, nullable=True)
    indicacao_token = Column(String(32), nullable=True, unique=True)
    somente_zona_propria = Column(Integer, nullable=False, default=0)
    zonas_bloqueadas_json = Column(Text, nullable=True)
    zonas_bloqueadas_atualizadas_em = Column(DateTime, nullable=True)
    grupo_locadores = Column(Integer, nullable=False, default=0)


class Novidade(Base):
    __tablename__ = "novidades"
    id = Column(Integer, primary_key=True)
    titulo = Column(String(180), nullable=False)
    chamada = Column(String(220), nullable=True)
    itens_json = Column(Text, nullable=False, default="[]")
    ativo = Column(Integer, nullable=False, default=1)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())


class EmpresaParceira(Base):
    __tablename__ = "empresas_parceiras"
    id = Column(Integer, primary_key=True)
    organiza_id = Column(Integer, unique=True, nullable=False, index=True)
    nome = Column(String(160), nullable=False)
    slug = Column(String(120), nullable=True, index=True)
    logo_data = Column(LargeBinary, nullable=True)
    logo_mime = Column(String(80), nullable=True)
    logo_hash = Column(String(64), nullable=True)
    ativo = Column(Integer, nullable=False, default=1)
    sincronizado_em = Column(DateTime, nullable=True)


class RedefinicaoSenha(Base):
    __tablename__ = "redefinicoes_senha"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True)
    expira_em = Column(DateTime, nullable=False)
    usado_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, server_default=func.now())



class Item(Base):
    __tablename__ = "itens"
    id = Column(Integer, primary_key=True)
    nome = Column(String(140), nullable=False, unique=True)
    tipo = Column(String(20), nullable=False, default="Produto")
    ativo = Column(Integer, nullable=False, default=1)
    # Reservados para regras futuras / integração com Organiza.
    exige_cliente_krj = Column(Integer, nullable=False, default=0)
    exige_equipamento = Column(Integer, nullable=False, default=0)
    criado_em = Column(DateTime, server_default=func.now())




class Estado(Base):
    __tablename__ = "estados"
    id = Column(Integer, primary_key=True)
    uf = Column(String(2), nullable=False, unique=True)
    nome = Column(String(80), nullable=False)
    criado_em = Column(DateTime, server_default=func.now())


class Municipio(Base):
    __tablename__ = "municipios"
    __table_args__ = (UniqueConstraint("estado_id", "nome", name="uq_municipio_estado_nome"),)
    id = Column(Integer, primary_key=True)
    estado_id = Column(Integer, ForeignKey("estados.id"), nullable=False)
    nome = Column(String(120), nullable=False)
    codigo_ibge = Column(String(12), nullable=True, unique=True)
    criado_em = Column(DateTime, server_default=func.now())


class Localidade(Base):
    __tablename__ = "localidades"
    __table_args__ = (UniqueConstraint("municipio_id", "nome", name="uq_localidade_municipio_nome"),)
    id = Column(Integer, primary_key=True)
    municipio_id = Column(Integer, ForeignKey("municipios.id"), nullable=False)
    nome = Column(String(140), nullable=False)
    tipo = Column(String(40), nullable=False, default="bairro")
    osm_id = Column(String(40), nullable=True)
    latitude = Column(String(30), nullable=True)
    longitude = Column(String(30), nullable=True)
    criado_em = Column(DateTime, server_default=func.now())


class Zona(Base):
    __tablename__ = "zonas"
    id = Column(Integer, primary_key=True)
    nome = Column(String(80), nullable=False, unique=True)
    ativo = Column(Integer, nullable=False, default=1)
    criado_em = Column(DateTime, server_default=func.now())




class AreaLocalidade(Base):
    __tablename__ = "area_localidades"
    __table_args__ = (UniqueConstraint("area_id", "localidade_id", name="uq_area_localidade"),)
    id = Column(Integer, primary_key=True)
    area_id = Column(Integer, ForeignKey("zonas.id"), nullable=False)
    localidade_id = Column(Integer, ForeignKey("localidades.id"), nullable=False)
    criado_em = Column(DateTime, server_default=func.now())



class RegraValidacao(Base):
    __tablename__ = "regras_validacao"
    id = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False)
    tipo = Column(String(50), nullable=False, default="catalogo_obrigatorio")
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    valor_obrigatorio = Column(String(60), nullable=True)
    mensagem_bloqueio = Column(Text, nullable=True)
    ativo = Column(Integer, nullable=False, default=1)
    criado_em = Column(DateTime, server_default=func.now())


class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False, unique=True)
    ativo = Column(Integer, nullable=False, default=1)
    criado_em = Column(DateTime, server_default=func.now())


class CatalogoItem(Base):
    __tablename__ = "catalogo_itens"
    id = Column(Integer, primary_key=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    nome = Column(String(140), nullable=False)
    ativo = Column(Integer, nullable=False, default=1)
    criado_em = Column(DateTime, server_default=func.now())


class SolicitacaoCatalogo(Base):
    __tablename__ = "solicitacoes_catalogo"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    categoria_sugerida = Column(String(100), nullable=False)
    item_sugerido = Column(String(140), nullable=False)
    observacao = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="Pendente")
    criado_em = Column(DateTime, server_default=func.now())




class UsuarioZona(Base):
    __tablename__ = "usuario_zonas"
    __table_args__ = (UniqueConstraint("usuario_id", "zona_id", name="uq_usuario_zona"),)
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    zona_id = Column(Integer, ForeignKey("zonas.id"), nullable=False)
    criado_em = Column(DateTime, server_default=func.now())


class UsuarioCategoria(Base):
    __tablename__ = "usuario_categorias"
    __table_args__ = (UniqueConstraint("usuario_id", "categoria_id", name="uq_usuario_categoria"),)
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)


class UsuarioCatalogoItem(Base):
    __tablename__ = "usuario_catalogo_itens"
    __table_args__ = (UniqueConstraint("usuario_id", "catalogo_item_id", name="uq_usuario_catalogo_item"),)
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    catalogo_item_id = Column(Integer, ForeignKey("catalogo_itens.id"), nullable=False)


class UsuarioItem(Base):
    __tablename__ = "usuario_itens"
    __table_args__ = (UniqueConstraint("usuario_id", "item_id", name="uq_usuario_item"),)
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("itens.id"), nullable=True)
    catalogo_item_id = Column(Integer, ForeignKey("catalogo_itens.id"), nullable=True)
    item_solicitado_texto = Column(String(180), nullable=True)


class Indicacao(Base):
    __tablename__ = "indicacoes"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("itens.id"), nullable=False)
    data_evento = Column(Date, nullable=True)
    zona = Column(String(80), nullable=False, default="Aguardando classificação")
    localidade_id = Column(Integer, ForeignKey("localidades.id"), nullable=True)
    area_id = Column(Integer, ForeignKey("zonas.id"), nullable=True)
    local_texto = Column(String(220), nullable=True)
    pedido_token = Column(String(40), nullable=True, index=True)
    whatsapp = Column(String(30), nullable=False)
    indicado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    recebido_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    status = Column(String(30), nullable=False, default="Aguardando sorteio")
    criado_em = Column(DateTime, server_default=func.now())
    encerrado_em = Column(DateTime, nullable=True)
    sorteio_rodada = Column(Integer, nullable=False, default=1)
    whatsapp_encaminhado_em = Column(DateTime, nullable=True)
    observacao = Column(Text, nullable=True)
    equipamentos_json = Column(Text, nullable=True)
    tipos_servico_json = Column(Text, nullable=True)


class Tentativa(Base):
    __tablename__ = "tentativas"
    __table_args__ = (UniqueConstraint("indicacao_id", "usuario_id", "rodada", name="uq_tentativa_usuario_rodada"),)
    id = Column(Integer, primary_key=True)
    indicacao_id = Column(Integer, ForeignKey("indicacoes.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    resultado = Column(Text, nullable=False, default="Em atendimento")
    sorteado_em = Column(DateTime, server_default=func.now())
    aceite_em = Column(DateTime, nullable=True)
    finalizado_em = Column(DateTime, nullable=True)
    rodada = Column(Integer, nullable=False, default=1)


class SorteioAuditoria(Base):
    __tablename__ = "sorteio_auditoria"
    id = Column(Integer, primary_key=True)
    indicacao_id = Column(Integer, ForeignKey("indicacoes.id"), nullable=False, index=True)
    rodada = Column(Integer, nullable=False, default=1)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    zona_indicacao = Column(String(80), nullable=True)
    zona_usuario = Column(String(80), nullable=True)
    ordem_zona = Column(Integer, nullable=True)
    elegivel = Column(Integer, nullable=False, default=0)
    creditos_prioridade = Column(Integer, nullable=False, default=0)
    selecionado = Column(Integer, nullable=False, default=0)
    motivo = Column(Text, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health", include_in_schema=False)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "postgresql" if IS_POSTGRES else "sqlite"}
    except Exception:
        return JSONResponse({"status": "error"}, status_code=503)


def gerar_hash_senha(senha: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 120000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        metodo, salt, esperado = senha_hash.split("$", 2)
        if metodo != "pbkdf2_sha256":
            return False
        atual = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 120000).hex()
        return hmac.compare_digest(atual, esperado)
    except Exception:
        return False


def assinatura(login: str) -> str:
    return hmac.new(CHAVE_SESSAO.encode(), f"lokafest:{login}".encode(), hashlib.sha256).hexdigest()


# O Firebase Hosting remove cookies comuns antes de encaminhar requisições ao
# Cloud Run. O cookie especial __session é o único permitido nesse fluxo.
COOKIE_SESSAO = "__session"
COOKIE_SESSAO_ANTIGO = "lokafest_sessao"


def normalizar_login(valor: str) -> str:
    """Login nunca contém espaços; aceita entrada antiga com espaços e compacta."""
    return re.sub(r"\s+", "", (valor or "").strip())


def login_cookie(request: Request):
    valor = request.cookies.get(COOKIE_SESSAO, "") or request.cookies.get(COOKIE_SESSAO_ANTIGO, "")
    if "." not in valor:
        return None
    login, sig = valor.rsplit(".", 1)
    return login if hmac.compare_digest(sig, assinatura(login)) else None


def usuario_logado(request: Request, db: Session = Depends(get_db)) -> Usuario:
    login = login_cookie(request)
    usuario = db.query(Usuario).filter(Usuario.usuario == login, Usuario.ativo == 1).first() if login else None
    if not usuario:
        raise HTTPException(status_code=303, headers={"Location": "/entrar"})
    return usuario


def exigir_admin(usuario: Usuario):
    if not usuario.is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")



def _humiat_validar_ticket(ticket: str) -> dict:
    if not HUMIAT_SSO_SECRET:
        raise HTTPException(status_code=503, detail="HUMIAT_SSO_SECRET não configurado no LokaFest")
    data = urllib.parse.urlencode({"ticket": ticket}).encode("utf-8")
    headers = {
        "X-Humiat-SSO-Secret": HUMIAT_SSO_SECRET,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": "LokaFest-Humiat-SSO/1.0",
    }
    req = urllib.request.Request(HUMIAT_SSO_VALIDATE_URL, data=data, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao validar acesso Humiat: {exc}")


def _normalizar_email(valor: str) -> str:
    return (valor or "").strip().lower()


def _normalizar_humiat_user_id(valor) -> str:
    return str(valor or "").strip()


def _vinculo_humiat_compativel(usuario_obj: Usuario, humiat_user_id: str) -> bool:
    """Evita relink silencioso de um perfil já preso a outro Humiat ID."""
    atual = _normalizar_humiat_user_id(getattr(usuario_obj, "humiat_user_id", ""))
    recebido = _normalizar_humiat_user_id(humiat_user_id)
    return not atual or not recebido or atual == recebido


def _usuario_por_identidade_humiat(
    db: Session,
    humiat_user_id: str = "",
    email: str = "",
    documento: str = "",
    telefone: str = "",
):
    """Concilia o Humiat ID com um cadastro LokaFest já existente.

    Ordem deliberada: vínculo Humiat -> e-mail -> CPF -> WhatsApp.
    WhatsApp permanece como último fallback para compatibilidade com a 1.0.8.
    """
    hid = _normalizar_humiat_user_id(humiat_user_id)
    email_n = _normalizar_email(email)
    cpf = normalizar_cpf(documento or "")
    whats = normalizar_whatsapp(telefone or "")

    base = db.query(Usuario).order_by(
        Usuario.ativo.desc(), Usuario.aprovado.desc(), Usuario.is_admin.desc(), Usuario.id.asc()
    )

    # 1) Depois do primeiro vínculo, este é o caminho principal e inequívoco.
    if hid:
        encontrado = base.filter(Usuario.humiat_user_id == hid).first()
        if encontrado:
            return encontrado

    # 2) E-mail da identidade central. Compatibilidade: cadastros antigos podem
    # ter usado o próprio e-mail como campo `usuario`.
    if email_n:
        candidatos = base.filter(
            or_(func.lower(Usuario.email) == email_n, func.lower(Usuario.usuario) == email_n)
        ).all()
        for u in candidatos:
            if _vinculo_humiat_compativel(u, hid):
                return u

    # 3) CPF pessoal. Não substitui um vínculo Humiat já existente e diferente.
    if cpf and cpf_valido(cpf):
        for u in base.all():
            if _vinculo_humiat_compativel(u, hid) and normalizar_cpf(u.cpf or "") == cpf:
                return u

    # 4) Fallback legado por WhatsApp. Útil quando o Organiza tem CNPJ e o
    # LokaFest mantém o CPF da pessoa responsável.
    if whats:
        for u in base.all():
            if _vinculo_humiat_compativel(u, hid) and normalizar_whatsapp(u.whatsapp or "") == whats:
                return u
    return None


def _vincular_identidade_humiat(usuario_obj: Usuario, identidade: dict) -> None:
    """Grava somente a identidade central; não altera permissões/histórico."""
    hid = _normalizar_humiat_user_id(identidade.get("id"))
    email_n = _normalizar_email(identidade.get("email") or "")
    documento = normalizar_cpf(identidade.get("documento") or "")
    telefone = normalizar_whatsapp(identidade.get("telefone") or "")

    if hid:
        atual = _normalizar_humiat_user_id(getattr(usuario_obj, "humiat_user_id", ""))
        if atual and atual != hid:
            raise HTTPException(status_code=409, detail="Este cadastro LokaFest já está vinculado a outro Humiat ID")
        usuario_obj.humiat_user_id = hid
    if email_n:
        usuario_obj.email = email_n
    # CPF/WhatsApp só preenchem lacunas; não sobrescrevem o cadastro local.
    if not normalizar_cpf(usuario_obj.cpf or "") and cpf_valido(documento):
        usuario_obj.cpf = documento
    if not normalizar_whatsapp(usuario_obj.whatsapp or "") and telefone:
        usuario_obj.whatsapp = telefone


def _status_pacote_humiat(db: Session, usuario_obj: Usuario) -> dict:
    vinculo = db.query(UsuarioCategoria).filter(UsuarioCategoria.usuario_id == usuario_obj.id).first()
    categoria = db.get(Categoria, vinculo.categoria_id) if vinculo else None
    if not categoria:
        return {"apto": False, "status": "cadastro_pendente", "mensagem": "Finalize seu cadastro para receber indicações."}

    if _normalizar_texto(categoria.nome) != "karaoke":
        return {"apto": bool(usuario_obj.ativo and usuario_obj.aprovado), "status": "atualizado", "mensagem": "Cadastro apto para receber indicações."}

    validacao = validar_usuario_regras(db, usuario_obj, categoria.id)
    pacote = validacao.get("pacote_real") or (usuario_obj.krj_atualizacao or "").strip() or None
    ultima = validacao.get("ultima_atualizacao") or None
    if not bool(validacao.get("apto")):
        return {
            "apto": False, "status": "bloqueado", "pacote": pacote, "ultima": ultima,
            "mensagem": "Regularize sua situação para voltar a ter acesso às indicações.",
        }
    if validacao.get("atualizacao_pendente"):
        return {
            "apto": True, "status": "falta_1", "pacote": pacote, "ultima": ultima,
            "mensagem": "Cuidado: você está a 1 pacote de ficar de fora das indicações.",
        }
    return {
        "apto": True, "status": "atualizado", "pacote": pacote, "ultima": ultima,
        "mensagem": "Você está apto a receber indicações.",
    }


@app.get("/_lokafest/sso/humiat", include_in_schema=False)
def lokafest_sso_humiat(humiat_ticket: str, db: Session = Depends(get_db)):
    dados = _humiat_validar_ticket(humiat_ticket)
    if not dados.get("ok") or (dados.get("produto") or "").upper() != "LOKAFEST":
        raise HTTPException(status_code=401, detail="Acesso Humiat inválido para o LokaFest")
    identidade = dados.get("usuario") or {}
    usuario_local = _usuario_por_identidade_humiat(
        db,
        humiat_user_id=identidade.get("id"),
        email=identidade.get("email") or "",
        documento=identidade.get("documento") or "",
        telefone=identidade.get("telefone") or "",
    )
    if not usuario_local:
        return RedirectResponse("/cadastro?erro=Finalize seu cadastro no LokaFest para receber indicações.", status_code=303)
    if not int(usuario_local.ativo or 0):
        return RedirectResponse("/entrar?erro=Seu cadastro LokaFest está inativo.", status_code=303)

    # O SSO apenas vincula a identidade central ao cadastro existente.
    # Não recria usuário e não altera admin/aprovação/créditos/zonas/histórico.
    _vincular_identidade_humiat(usuario_local, identidade)
    usuario_local.online = 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este Humiat ID já está vinculado a outro cadastro LokaFest")

    # Administrador existente entra no mesmo painel usado pelo login próprio.
    if int(usuario_local.is_admin or 0):
        destino = "/painel"
    else:
        destino = "/painel" if int(usuario_local.aprovado or 0) else "/meu-cadastro?humiat=1&ok=Complete+seu+cadastro+para+ficar+apto+às+indicações"
    resposta = RedirectResponse(destino, status_code=303)
    resposta.set_cookie(
        COOKIE_SESSAO,
        f"{usuario_local.usuario}.{assinatura(usuario_local.usuario)}",
        httponly=True, secure=IS_PRODUCTION, samesite="none" if IS_PRODUCTION else "lax",
        max_age=60 * 60 * 24, path="/"
    )
    return resposta


@app.post("/api/humiat/painel", include_in_schema=False)
@app.post("/_lokafest/api/humiat/painel", include_in_schema=False)
def lokafest_resumo_humiat(
    documento: str = Form(""),
    telefone: str = Form(""),
    x_humiat_sso_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    if not HUMIAT_SSO_SECRET or not hmac.compare_digest(x_humiat_sso_secret or "", HUMIAT_SSO_SECRET):
        raise HTTPException(status_code=401, detail="Integração Humiat não autorizada")

    total_global = int(db.query(func.count(Indicacao.id)).scalar() or 0)
    usuario_local = _usuario_por_identidade_humiat(db, documento=documento, telefone=telefone)
    if not usuario_local:
        return {
            "ok": True, "usuario_existe": False, "total_global": total_global,
            "cadastro_url": f"{LOKAFEST_PUBLIC_URL}/cadastro",
            "mensagem": "Seu cadastro de usuário LokaFest ainda não foi concluído.",
        }

    recebidas = int(db.query(func.count(func.distinct(Tentativa.indicacao_id))).filter(Tentativa.usuario_id == usuario_local.id).scalar() or 0)
    repassadas = int(db.query(func.count(func.distinct(Tentativa.indicacao_id))).filter(
        Tentativa.usuario_id == usuario_local.id,
        Tentativa.resultado.like("Repassou%"),
    ).scalar() or 0)
    pacote = _status_pacote_humiat(db, usuario_local)
    cadastro_ativo = bool(int(usuario_local.ativo or 0))
    cadastro_aprovado = bool(int(usuario_local.aprovado or 0))
    apto = bool(cadastro_ativo and cadastro_aprovado and pacote.get("apto"))

    return {
        "ok": True,
        "usuario_existe": True,
        "cadastro_ativo": cadastro_ativo,
        "cadastro_aprovado": cadastro_aprovado,
        "apto_indicacoes": apto,
        "total_global": total_global,
        "recebidas": recebidas,
        "repassadas": repassadas,
        "prioridades": int(usuario_local.prioridade_creditos or 0),
        "grupo_whatsapp": bool(int(usuario_local.grupo_locadores or 0)),
        "grupo_url": LOKAFEST_GRUPO_WHATSAPP_URL,
        "pacote": pacote.get("pacote") or "",
        "pacote_mais_recente": pacote.get("ultima") or "",
        "status_pacote": pacote.get("status") or "",
        "mensagem": pacote.get("mensagem") or "",
        "cadastro_url": f"{LOKAFEST_PUBLIC_URL}/meu-cadastro",
    }

def _validar_segredo_humiat(x_humiat_sso_secret: str) -> None:
    if not HUMIAT_SSO_SECRET or not hmac.compare_digest(x_humiat_sso_secret or "", HUMIAT_SSO_SECRET):
        raise HTTPException(status_code=401, detail="Integração Humiat não autorizada")


@app.get("/api/humiat/usuarios", include_in_schema=False)
@app.get("/_lokafest/api/humiat/usuarios", include_in_schema=False)
def lokafest_usuarios_humiat(
    usuario_id: int | None = None,
    x_humiat_sso_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Base de migração inicial LokaFest -> Humiat ID.

    Não expõe senha/hash. O e-mail não existe na base histórica do LokaFest e
    deve ser obtido no Organiza durante a conciliação.
    """
    _validar_segredo_humiat(x_humiat_sso_secret)
    consulta = db.query(Usuario).filter(Usuario.is_admin == 0)
    if usuario_id:
        consulta = consulta.filter(Usuario.id == int(usuario_id))
    usuarios = consulta.order_by(Usuario.nome.asc(), Usuario.id.asc()).all()
    itens = []
    for u in usuarios:
        vinculo = db.query(UsuarioCategoria).filter(UsuarioCategoria.usuario_id == u.id).first()
        categoria = db.get(Categoria, vinculo.categoria_id) if vinculo else None
        itens.append({
            "id": int(u.id),
            "nome": u.nome or "",
            "cpf": u.cpf or "",
            "whatsapp": u.whatsapp or "",
            "zona": u.zona or "",
            "ativo": bool(int(u.ativo or 0)),
            "aprovado": bool(int(u.aprovado or 0)),
            "grupo_locadores": bool(int(u.grupo_locadores or 0)),
            "categoria": categoria.nome if categoria else "",
            # Estado real do vínculo local. O Humiat usa este campo para montar
            # a fila de pendências; não depende mais do histórico de migração.
            "humiat_user_id": _normalizar_humiat_user_id(u.humiat_user_id),
            "krj_cliente_id": u.krj_cliente_id or "",
            "krj_atualizacao": u.krj_atualizacao or "",
        })
    return {"ok": True, "total": len(itens), "usuarios": itens}


def _sincronizar_perfil_humiat_organiza(db: Session, usuario_obj: Usuario, *, nome: str, cpf: str, whats: str, zona_nome: str) -> dict:
    """Completa o perfil LokaFest usando o Organiza como fonte de verdade."""
    zona_obj = db.query(Zona).filter(Zona.nome == (zona_nome or "").strip(), Zona.ativo == 1).first()
    if not zona_obj:
        zona_obj = db.query(Zona).filter(Zona.nome == "Outros RJ", Zona.ativo == 1).first()
    if not zona_obj:
        zona_obj = db.query(Zona).filter(Zona.ativo == 1).order_by(Zona.id.asc()).first()
    if not zona_obj:
        raise HTTPException(status_code=500, detail="Nenhuma zona ativa cadastrada no LokaFest")

    usuario_obj.nome = normalizar_nome_exibicao(nome or usuario_obj.nome or "Cliente Humiat")
    if cpf_valido(cpf):
        usuario_obj.cpf = cpf
    usuario_obj.whatsapp = whats
    usuario_obj.ativo = 1
    # Perfil criado/conciliado pelo Humiat não depende mais de aprovação manual:
    # os dados principais são validados a partir do cadastro do Organiza.
    usuario_obj.aprovado = 1

    # Só reposiciona a zona principal quando o usuário ainda não personalizou
    # suas regiões. Assim não apagamos escolhas posteriores feitas no LokaFest.
    if not usuario_obj.zonas_bloqueadas_json:
        definir_zona_gratuita(db, usuario_obj, zona_obj.nome)
        usuario_obj.zonas_bloqueadas_json = None
        usuario_obj.zonas_bloqueadas_atualizadas_em = None

    resultado = consultar_organiza_cliente(cpf, whats)
    if not resultado.get("ok"):
        raise HTTPException(
            status_code=503,
            detail=str(resultado.get("mensagem") or "Não foi possível consultar o Organiza para montar o perfil LokaFest"),
        )
    if not resultado.get("encontrado"):
        raise HTTPException(status_code=409, detail="Cliente não localizado no Organiza para montar o perfil LokaFest")

    karaoke_id = _categoria_karaoke_id(db)
    if resultado.get("nome"):
        usuario_obj.nome = normalizar_nome_exibicao(resultado.get("nome") or usuario_obj.nome)
    if karaoke_id:
        resultado = _aplicar_regra_catalogo_no_resultado(db, resultado, karaoke_id)
    aplicar_cache_krj(usuario_obj, resultado)
    # Equivale ao botão "Carregar dados" da tela administrativa: além do
    # cache de equipamentos, sincroniza categorias e itens oferecidos.
    sincronizar_categorias_por_equipamentos(db, usuario_obj)

    token_atual = (usuario_obj.indicacao_token or "").strip().upper()
    if token_atual:
        usuario_obj.indicacao_token = token_atual
    else:
        while True:
            token = secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:10].upper()
            if token and not db.query(Usuario).filter(Usuario.indicacao_token == token).first():
                usuario_obj.indicacao_token = token
                break
    return resultado


@app.post("/api/humiat/vincular-id", include_in_schema=False)
@app.post("/_lokafest/api/humiat/vincular-id", include_in_schema=False)
def lokafest_vincular_id_humiat(
    usuario_id: int = Form(...),
    humiat_user_id: str = Form(...),
    x_humiat_sso_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Recebe o Humiat ID no evento de aprovação e grava localmente.

    A tela /admin/usuarios não consulta Humiat/Organiza; ela apenas lê este
    campo local.
    """
    _validar_segredo_humiat(x_humiat_sso_secret)
    usuario_obj = db.get(Usuario, int(usuario_id))
    if not usuario_obj:
        raise HTTPException(status_code=404, detail="Usuário LokaFest não encontrado")
    hid = _normalizar_humiat_user_id(humiat_user_id)
    if not hid:
        raise HTTPException(status_code=400, detail="Humiat ID obrigatório")
    atual = _normalizar_humiat_user_id(usuario_obj.humiat_user_id)
    if atual and atual != hid:
        raise HTTPException(status_code=409, detail="Usuário LokaFest já vinculado a outro Humiat ID")
    outro = db.query(Usuario).filter(Usuario.humiat_user_id == hid, Usuario.id != usuario_obj.id).first()
    if outro:
        raise HTTPException(status_code=409, detail="Humiat ID já vinculado a outro usuário LokaFest")
    usuario_obj.humiat_user_id = hid
    db.commit()
    return {"ok": True, "usuario_id": int(usuario_obj.id), "humiat_user_id": hid}


@app.post("/api/humiat/garantir-usuario", include_in_schema=False)
@app.post("/_lokafest/api/humiat/garantir-usuario", include_in_schema=False)
def lokafest_garantir_usuario_humiat(
    nome: str = Form(""),
    documento: str = Form(""),
    telefone: str = Form(""),
    zona: str = Form(""),
    x_humiat_sso_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Cria ou completa o perfil LokaFest a partir do Organiza/Humiat.

    A origem é confiável e servidor-servidor; por isso o perfil já nasce ativo
    e aprovado, sem a antiga etapa de conferência manual no LokaFest.
    """
    _validar_segredo_humiat(x_humiat_sso_secret)
    cpf_informado = normalizar_cpf(documento or "")
    cpf = cpf_informado if cpf_valido(cpf_informado) else ""
    whats = normalizar_whatsapp(telefone or "")
    if not whatsapp_valido(whats):
        raise HTTPException(status_code=400, detail="WhatsApp válido é obrigatório para criar ou vincular o usuário LokaFest")

    # Primeiro procura pelo telefone. Assim um perfil LokaFest com CPF continua
    # sendo o mesmo usuário quando o Organiza possui CNPJ para aquele telefone.
    existente = _usuario_por_identidade_humiat(db, documento=cpf, telefone=whats)
    if existente:
        cpf_perfil = cpf if cpf else normalizar_cpf(existente.cpf or "")
        resultado = _sincronizar_perfil_humiat_organiza(
            db, existente, nome=nome or existente.nome, cpf=cpf_perfil, whats=whats, zona_nome=zona
        )
        db.commit()
        return {
            "ok": True,
            "criado": False,
            "usuario_id": int(existente.id),
            "aprovado": True,
            "ativo": True,
            "zona": existente.zona or "",
            "krj_cliente_id": existente.krj_cliente_id or "",
            "pacote": existente.krj_atualizacao or "",
            "cadastro_url": f"{LOKAFEST_PUBLIC_URL}/meu-cadastro",
        }

    # A zona é calculada pelo Humiat a partir do endereço do Organiza.
    zona_obj = db.query(Zona).filter(Zona.nome == (zona or "").strip(), Zona.ativo == 1).first()
    if not zona_obj:
        zona_obj = db.query(Zona).filter(Zona.nome == "Outros RJ", Zona.ativo == 1).first()
    if not zona_obj:
        zona_obj = db.query(Zona).filter(Zona.ativo == 1).order_by(Zona.id.asc()).first()
    if not zona_obj:
        raise HTTPException(status_code=500, detail="Nenhuma zona ativa cadastrada no LokaFest")

    novo = Usuario(
        nome=normalizar_nome_exibicao(nome or "Cliente Humiat"),
        usuario=gerar_login_interno(db),
        whatsapp=whats,
        cpf=cpf or None,
        senha_hash=gerar_hash_senha(secrets.token_urlsafe(32)),
        zona=zona_obj.nome,
        is_admin=0,
        ativo=1,
        aprovado=1,
    )
    db.add(novo)
    db.flush()
    novo.zonas_bloqueadas_json = None
    novo.zonas_bloqueadas_atualizadas_em = None

    resultado = _sincronizar_perfil_humiat_organiza(
        db, novo, nome=nome or novo.nome, cpf=cpf, whats=whats, zona_nome=zona_obj.nome
    )
    db.commit()
    return {
        "ok": True,
        "criado": True,
        "usuario_id": int(novo.id),
        "aprovado": True,
        "ativo": True,
        "zona": novo.zona or "",
        "krj_cliente_id": novo.krj_cliente_id or "",
        "pacote": novo.krj_atualizacao or "",
        "cadastro_url": f"{LOKAFEST_PUBLIC_URL}/meu-cadastro",
    }


def _retorno_admin_sorteio(valor: str = "", chave: str = "", mensagem: str = "") -> str:
    """Preserva os filtros da tela de sorteio após ações administrativas."""
    valor = (valor or "").strip()
    if not valor.startswith("/admin/sorteio") or valor.startswith("//"):
        valor = "/admin/sorteio"
    partes = urllib.parse.urlsplit(valor)
    consulta = dict(urllib.parse.parse_qsl(partes.query, keep_blank_values=True))
    if chave and mensagem:
        consulta[chave] = mensagem
    nova_consulta = urllib.parse.urlencode(consulta)
    return urllib.parse.urlunsplit(("", "", partes.path or "/admin/sorteio", nova_consulta, ""))





def _somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def _categoria_karaoke_id(db: Session):
    for categoria in db.query(Categoria).filter(Categoria.ativo == 1).all():
        if _normalizar_texto(categoria.nome) == "karaoke":
            return categoria.id
    return None


def _categoria_fliperama_id(db: Session):
    for categoria in db.query(Categoria).filter(Categoria.ativo == 1).all():
        if _normalizar_texto(categoria.nome) == "fliperama":
            return categoria.id
    return None


def consultar_organiza_cliente(cpf: str = "", whatsapp: str = "", cliente_id: str = "", maquina: str = ""):
    """
    Consulta o Organiza sem expor sua base diretamente ao navegador.

    ORGANIZA_API_URL deve apontar para um endpoint que aceite:
      ?cpf=...&whatsapp=...&cliente_id=...&maquina=...

    Resposta esperada:
    {
      "encontrado": true,
      "cliente_id": "123",
      "cpf": "00000000000",
      "atualizacao": "2026.1",
      "equipamentos": {
        "jukebox": 1,
        "portatil": 0,
        "iphone": 1,
        "fliperama": 1
      }
    }
    """
    if not ORGANIZA_API_URL:
        return {
            "ok": False,
            "configurado": False,
            "mensagem": "Integração com Organiza ainda não configurada."
        }

    params = urllib.parse.urlencode({
        "cpf": _somente_digitos(cpf),
        "whatsapp": _somente_digitos(whatsapp),
        "cliente_id": _somente_digitos(cliente_id),
        "maquina": (maquina or "").strip(),
    })
    sep = "&" if "?" in ORGANIZA_API_URL else "?"
    url = f"{ORGANIZA_API_URL}{sep}{params}"

    headers = {
        "User-Agent": "LokaFest/1.0",
        "Accept": "application/json",
    }
    if ORGANIZA_API_TOKEN:
        headers["Authorization"] = f"Bearer {ORGANIZA_API_TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return {
            "ok": False,
            "configurado": True,
            "mensagem": f"Não foi possível consultar o Organiza: {exc}"
        }

    if not payload or not payload.get("encontrado"):
        return {
            "ok": True,
            "encontrado": False,
            "mensagem": "Cliente não encontrado no Organiza."
        }

    equipamentos = payload.get("equipamentos") or {}
    return {
        "ok": True,
        "encontrado": True,
        "cliente_id": str(payload.get("cliente_id") or ""),
        "nome": str(payload.get("nome") or ""),
        "cpf": _somente_digitos(payload.get("cpf") or cpf),
        "whatsapp": str(payload.get("whatsapp") or ""),
        "atualizacao": str(payload.get("atualizacao") or ""),
        "jukebox": int(equipamentos.get("jukebox") or 0),
        "portatil": int(equipamentos.get("portatil") or 0),
        "iphone": int(equipamentos.get("iphone") or 0),
        "fliperama": int(equipamentos.get("fliperama") or 0),
        "detalhes": payload.get("detalhes") or [],
    }


def aplicar_cache_krj(usuario_obj: Usuario, resultado: dict):
    usuario_obj.krj_validado = 1 if resultado.get("encontrado") else 0
    usuario_obj.krj_cliente_id = resultado.get("cliente_id") or None
    usuario_obj.cpf = resultado.get("cpf") or usuario_obj.cpf
    usuario_obj.krj_jukebox_qtd = int(resultado.get("jukebox") or 0)
    usuario_obj.krj_portatil_qtd = int(resultado.get("portatil") or 0)
    usuario_obj.krj_iphone_qtd = int(resultado.get("iphone") or 0)
    usuario_obj.krj_fliperama_qtd = int(resultado.get("fliperama") or 0)

    detalhes = resultado.get("detalhes") or []
    # O campo agregado retornado pela integração pode representar a versão
    # atual do catálogo do sistema, e não a versão real de todos os aparelhos.
    # Quando existem equipamentos detalhados, o banco passa a guardar a maior
    # versão real encontrada entre eles.
    pacote_real = _pacote_real_dos_equipamentos(detalhes)
    total_equipamentos = (
        int(resultado.get("jukebox") or 0)
        + int(resultado.get("portatil") or 0)
        + int(resultado.get("iphone") or 0)
    )
    if pacote_real:
        usuario_obj.krj_atualizacao = pacote_real
    elif total_equipamentos > 0 and resultado.get("atualizacao"):
        # Compatibilidade com integrações antigas que informavam quantidade e
        # pacote agregado, mas ainda não devolviam a lista detalhada.
        usuario_obj.krj_atualizacao = str(resultado.get("atualizacao")).strip() or None
    else:
        # Cliente encontrado, porém sem equipamento de Karaokê. A versão global
        # disponível no Organiza não pode virar pacote do cliente.
        usuario_obj.krj_atualizacao = None

    usuario_obj.krj_validado_em = datetime.now()
    usuario_obj.krj_equipamentos_json = json.dumps(
        detalhes,
        ensure_ascii=False
    )


def limpar_cache_organiza_usuario(usuario_obj: Usuario):
    """Limpa somente o cache de equipamentos quando o Organiza confirma que o cliente não foi encontrado."""
    usuario_obj.krj_validado = 0
    usuario_obj.krj_cliente_id = None
    usuario_obj.krj_jukebox_qtd = 0
    usuario_obj.krj_portatil_qtd = 0
    usuario_obj.krj_iphone_qtd = 0
    usuario_obj.krj_fliperama_qtd = 0
    usuario_obj.krj_atualizacao = None
    usuario_obj.krj_validado_em = datetime.now()
    usuario_obj.krj_equipamentos_json = "[]"


def _chave_pacote_catalogo(valor):
    """Converte versões como 2025.2/2026.1 em tupla comparável."""
    texto = str(valor or "").strip()
    if not texto:
        return None

    match = re.fullmatch(r"(\d{4})\s*[.]\s*(\d+)", texto)
    if not match:
        return None

    return int(match.group(1)), int(match.group(2))


def _pacote_atende_obrigatorio(pacote_atual, pacote_obrigatorio):
    """
    Um equipamento está apto quando seu pacote é igual ou posterior ao
    catálogo mínimo obrigatório. Ex.: 2026.1 >= 2025.2.
    """
    atual = _chave_pacote_catalogo(pacote_atual)
    obrigatorio = _chave_pacote_catalogo(pacote_obrigatorio)

    if atual is not None and obrigatorio is not None:
        return atual >= obrigatorio

    # Compatibilidade defensiva para valores antigos fora do padrão YYYY.N.
    return str(pacote_atual or "").strip() == str(pacote_obrigatorio or "").strip()


def _regra_catalogo_ativa(db: Session, categoria_id: int):
    """Retorna a regra ativa mais recente de catálogo obrigatório da categoria."""
    return db.query(RegraValidacao).filter(
        RegraValidacao.ativo == 1,
        RegraValidacao.tipo == "catalogo_obrigatorio",
        RegraValidacao.categoria_id == categoria_id
    ).order_by(RegraValidacao.id.desc()).first()


def _aplicar_regra_catalogo_no_resultado(db: Session, resultado: dict, categoria_id: int):
    """
    Separa três informações diferentes:
    1. pacote real do equipamento;
    2. catálogo mínimo para participar do sorteio;
    3. última atualização disponível no Organiza.
    """
    regra = _regra_catalogo_ativa(db, categoria_id)
    if not regra or not (regra.valor_obrigatorio or "").strip():
        return resultado

    minimo_sorteio = regra.valor_obrigatorio.strip()
    detalhes = resultado.get("detalhes") or []

    # O Organiza devolve a última atualização disponível no campo geral
    # "atualizacao" e/ou no pacote_obrigatorio de cada equipamento.
    ultima_geral = str(resultado.get("atualizacao") or "").strip()

    for eq in detalhes:
        pacote_real = str((eq or {}).get("pacote") or "").strip()
        ultima_eq = str(
            (eq or {}).get("ultima_atualizacao")
            or (eq or {}).get("pacote_obrigatorio")
            or ultima_geral
            or ""
        ).strip()

        eq["ultima_atualizacao"] = ultima_eq or None
        eq["catalogo_sorteio"] = minimo_sorteio
        eq["pacote_obrigatorio"] = minimo_sorteio
        eq["apto_sorteio"] = _pacote_atende_obrigatorio(pacote_real, minimo_sorteio)
        eq["atualizacao_disponivel"] = bool(
            ultima_eq and not _pacote_atende_obrigatorio(pacote_real, ultima_eq)
        )
        # Compatibilidade com as telas existentes.
        eq["atualizado"] = eq["apto_sorteio"]

    pacote_maior = _pacote_real_dos_equipamentos(detalhes)
    ultima_disponivel = _ultima_atualizacao_disponivel(detalhes) or ultima_geral or None

    resultado["detalhes"] = detalhes
    resultado["catalogo_obrigatorio"] = minimo_sorteio
    resultado["catalogo_sorteio"] = minimo_sorteio
    resultado["ultima_atualizacao"] = ultima_disponivel
    resultado["mensagem_bloqueio"] = (regra.mensagem_bloqueio or "").strip()
    resultado["apto"] = any(bool((eq or {}).get("apto_sorteio")) for eq in detalhes) if detalhes else False
    resultado["tem_atualizacao_disponivel"] = any(
        bool((eq or {}).get("atualizacao_disponivel")) for eq in detalhes
    )

    # "atualizacao" passa a representar a versão real mais alta do cliente.
    if pacote_maior:
        resultado["atualizacao"] = pacote_maior

    return resultado


def _pacote_real_dos_equipamentos(detalhes):
    """
    Retorna a maior versão real encontrada nos equipamentos.
    Para a regra inicial do LokaFest, considera o equipamento
    mais atualizado do cliente como referência de elegibilidade.
    """
    versoes = []
    for eq in detalhes or []:
        pacote = str((eq or {}).get("pacote") or "").strip()
        chave = _chave_pacote_catalogo(pacote)
        if chave is not None:
            versoes.append((chave, pacote))

    if not versoes:
        return None

    versoes.sort(key=lambda item: item[0], reverse=True)
    return versoes[0][1]


def _ultima_atualizacao_disponivel(detalhes):
    """Retorna a maior versão marcada pela integração como última disponível."""
    versoes = []
    for eq in detalhes or []:
        valor = str(
            (eq or {}).get("ultima_atualizacao")
            or (eq or {}).get("catalogo_mais_recente")
            or ""
        ).strip()
        chave = _chave_pacote_catalogo(valor)
        if chave is not None:
            versoes.append((chave, valor))

    if not versoes:
        return None

    versoes.sort(key=lambda item: item[0], reverse=True)
    return versoes[0][1]


def validar_usuario_regras(db: Session, usuario_obj: Usuario, categoria_id: int):
    """
    Valida as regras locais do LokaFest.
    Nesta fase, basta pelo menos um equipamento atingir o catálogo obrigatório.
    """
    regra = _regra_catalogo_ativa(db, categoria_id)
    if not regra:
        return {"apto": True, "mensagens": [], "equipamentos_pendentes": []}

    obrigatorio = (regra.valor_obrigatorio or "").strip()
    if not obrigatorio:
        return {"apto": True, "mensagens": [], "equipamentos_pendentes": []}

    try:
        detalhes = json.loads(usuario_obj.krj_equipamentos_json or "[]")
        if not isinstance(detalhes, list):
            detalhes = []
    except Exception:
        detalhes = []

    equipamentos_pendentes = []
    equipamentos_aptos = []

    if detalhes:
        for eq in detalhes:
            # Fliperama não participa da regra de catálogo/atualização do Karaokê.
            if _normalizar_texto(str((eq or {}).get("tipo") or "")) == "fliperama":
                continue
            pacote = str((eq or {}).get("pacote") or "").strip()
            identificacao = str((eq or {}).get("identificacao") or "").strip()
            numero = str((eq or {}).get("numero_maquina") or "").strip()
            modelo = str((eq or {}).get("modelo") or (eq or {}).get("tipo") or "Equipamento").strip()
            rotulo = identificacao or modelo
            if numero:
                rotulo += f" ({numero})"

            if _pacote_atende_obrigatorio(pacote, obrigatorio):
                equipamentos_aptos.append(rotulo)
            else:
                equipamentos_pendentes.append(rotulo)
    else:
        qtd_jukebox = int(usuario_obj.krj_jukebox_qtd or 0)
        qtd_portatil = int(usuario_obj.krj_portatil_qtd or 0)
        qtd_iphone = int(usuario_obj.krj_iphone_qtd or 0)
        total_equipamentos = qtd_jukebox + qtd_portatil + qtd_iphone
        atual = (usuario_obj.krj_atualizacao or "").strip()

        # Sem equipamento real, nunca pode ficar apto apenas porque existe uma
        # versão de catálogo/atualização armazenada no cache.
        if total_equipamentos > 0 and _pacote_atende_obrigatorio(atual, obrigatorio):
            equipamentos_aptos.append("Cadastro")
        else:
            if qtd_jukebox > 0:
                equipamentos_pendentes.append("Jukebox")
            if qtd_portatil > 0:
                equipamentos_pendentes.append("Portátil")
            if qtd_iphone > 0:
                equipamentos_pendentes.append("iPhone")

    apto = len(equipamentos_aptos) > 0
    mensagens = []

    if not apto:
        mensagem_base = (regra.mensagem_bloqueio or "").strip()
        if not mensagem_base:
            mensagem_base = (
                "Você ainda não está apto para receber indicações. "
                "Atualize pelo menos um equipamento para o catálogo obrigatório."
            )
        lista = ", ".join(equipamentos_pendentes)
        complemento = f" Catálogo obrigatório vigente: {obrigatorio}."
        if lista:
            complemento += f" Equipamento(s) pendente(s): {lista}."
        mensagens.append(mensagem_base + complemento)

    ultima_disponivel = _ultima_atualizacao_disponivel(detalhes)
    pacote_real = _pacote_real_dos_equipamentos(detalhes) or (usuario_obj.krj_atualizacao or "").strip() or None
    atualizacao_pendente = bool(
        ultima_disponivel
        and pacote_real
        and not _pacote_atende_obrigatorio(pacote_real, ultima_disponivel)
    )

    equipamentos_para_atualizar = []
    if ultima_disponivel:
        for eq in detalhes:
            if _normalizar_texto(str((eq or {}).get("tipo") or "")) == "fliperama":
                continue
            pacote = str((eq or {}).get("pacote") or "").strip()
            if pacote and not _pacote_atende_obrigatorio(pacote, ultima_disponivel):
                identificacao = str((eq or {}).get("identificacao") or "").strip()
                numero = str((eq or {}).get("numero_maquina") or "").strip()
                modelo = str((eq or {}).get("modelo") or (eq or {}).get("tipo") or "Equipamento").strip()
                rotulo = identificacao or modelo
                if numero:
                    rotulo += f" ({numero})"
                equipamentos_para_atualizar.append(rotulo)

    return {
        "apto": apto,
        "mensagens": mensagens,
        "equipamentos_pendentes": equipamentos_pendentes,
        "equipamentos_aptos": equipamentos_aptos,
        "catalogo_obrigatorio": obrigatorio,
        "pacote_real": pacote_real,
        "ultima_atualizacao": ultima_disponivel,
        "atualizacao_pendente": atualizacao_pendente,
        "equipamentos_para_atualizar": equipamentos_para_atualizar,
    }


def definir_categoria_gratuita(db: Session, usuario_obj: Usuario, categoria_id: int, catalogo_ids=None):
    """Compatibilidade com cadastros de uma única categoria."""
    return definir_categorias_limitadas(db, usuario_obj, [categoria_id], catalogo_ids, maximo=1)


def definir_categorias_limitadas(db: Session, usuario_obj: Usuario, categoria_ids, catalogo_ids=None, maximo: int = 2):
    """Permite até duas categorias ativas no cadastro do usuário."""
    ids = []
    for valor in (categoria_ids or []):
        if str(valor).isdigit():
            cid = int(valor)
            if cid not in ids:
                ids.append(cid)
    if not ids or len(ids) > int(maximo or 2):
        return False

    categorias_validas = db.query(Categoria).filter(
        Categoria.id.in_(ids), Categoria.ativo == 1
    ).all()
    validos_ids = {c.id for c in categorias_validas}
    if validos_ids != set(ids):
        return False

    db.query(UsuarioCategoria).filter(
        UsuarioCategoria.usuario_id == usuario_obj.id
    ).delete(synchronize_session=False)
    db.query(UsuarioCatalogoItem).filter(
        UsuarioCatalogoItem.usuario_id == usuario_obj.id
    ).delete(synchronize_session=False)

    for cid in ids:
        db.add(UsuarioCategoria(usuario_id=usuario_obj.id, categoria_id=cid))

    itens_ids = {int(x) for x in (catalogo_ids or []) if str(x).isdigit()}
    if itens_ids:
        itens_validos = db.query(CatalogoItem).filter(
            CatalogoItem.id.in_(itens_ids),
            CatalogoItem.categoria_id.in_(ids),
            CatalogoItem.ativo == 1,
        ).all()
        for item in itens_validos:
            db.add(UsuarioCatalogoItem(
                usuario_id=usuario_obj.id,
                catalogo_item_id=item.id
            ))
    return True


def sincronizar_categorias_por_equipamentos(db: Session, usuario_obj: Usuario):
    """Sincroniza categorias e itens Karaokê/Fliperama com o Organiza.

    É a mesma regra usada tanto no botão manual quanto no onboarding pelo
    Humiat, para o cadastro já nascer com Jukebox/iPhone/Portátil/Fliperama
    marcados conforme os equipamentos ativos encontrados.
    """
    karaoke_id = _categoria_karaoke_id(db)
    fliperama_id = _categoria_fliperama_id(db)
    gerenciadas = {x for x in (karaoke_id, fliperama_id) if x}
    desejadas = set()
    total_karaoke = int(usuario_obj.krj_jukebox_qtd or 0) + int(usuario_obj.krj_portatil_qtd or 0) + int(usuario_obj.krj_iphone_qtd or 0)
    if karaoke_id and total_karaoke > 0:
        desejadas.add(karaoke_id)
    if fliperama_id and int(usuario_obj.krj_fliperama_qtd or 0) > 0:
        desejadas.add(fliperama_id)

    atuais = {x.categoria_id for x in db.query(UsuarioCategoria).filter(
        UsuarioCategoria.usuario_id == usuario_obj.id
    ).all()}

    # Remove somente as categorias controladas pelo Organiza que deixaram de existir.
    remover = (atuais & gerenciadas) - desejadas
    if remover:
        db.query(UsuarioCategoria).filter(
            UsuarioCategoria.usuario_id == usuario_obj.id,
            UsuarioCategoria.categoria_id.in_(remover),
        ).delete(synchronize_session=False)

    # Adiciona automaticamente cada categoria confirmada pelo Organiza.
    for cid in desejadas - atuais:
        db.add(UsuarioCategoria(usuario_id=usuario_obj.id, categoria_id=cid))

    # Itens gerenciados automaticamente. Mantém outros itens/categorias que não
    # fazem parte de Karaokê/Fliperama.
    itens_gerenciados = db.query(CatalogoItem).filter(
        CatalogoItem.ativo == 1,
        CatalogoItem.categoria_id.in_(list(gerenciadas)) if gerenciadas else False,
    ).all() if gerenciadas else []
    desejados_itens = set()
    itens_por_nome = {}
    itens_fliperama = []
    for item in itens_gerenciados:
        nome = _normalizar_texto(item.nome)
        itens_por_nome.setdefault((int(item.categoria_id), nome), item)
        if fliperama_id and int(item.categoria_id) == int(fliperama_id):
            itens_fliperama.append(item)

    def adicionar_item_categoria(cid, termo):
        if not cid:
            return
        termo_n = _normalizar_texto(termo)
        for item in itens_gerenciados:
            if int(item.categoria_id) == int(cid) and termo_n in _normalizar_texto(item.nome):
                desejados_itens.add(int(item.id))
                return

    if karaoke_id:
        if int(usuario_obj.krj_jukebox_qtd or 0) > 0: adicionar_item_categoria(karaoke_id, "jukebox")
        if int(usuario_obj.krj_portatil_qtd or 0) > 0: adicionar_item_categoria(karaoke_id, "portatil")
        if int(usuario_obj.krj_iphone_qtd or 0) > 0: adicionar_item_categoria(karaoke_id, "iphone")
    if fliperama_id and int(usuario_obj.krj_fliperama_qtd or 0) > 0:
        antes = len(desejados_itens)
        adicionar_item_categoria(fliperama_id, "fliperama")
        # Se a categoria tem um único item com outro nome, ele representa o serviço.
        if len(desejados_itens) == antes and len(itens_fliperama) == 1:
            desejados_itens.add(int(itens_fliperama[0].id))

    ids_gerenciados = {int(i.id) for i in itens_gerenciados}
    links_atuais = db.query(UsuarioCatalogoItem).filter(
        UsuarioCatalogoItem.usuario_id == usuario_obj.id
    ).all()
    atuais_itens = {int(x.catalogo_item_id) for x in links_atuais}
    remover_itens = (atuais_itens & ids_gerenciados) - desejados_itens
    if remover_itens:
        db.query(UsuarioCatalogoItem).filter(
            UsuarioCatalogoItem.usuario_id == usuario_obj.id,
            UsuarioCatalogoItem.catalogo_item_id.in_(remover_itens),
        ).delete(synchronize_session=False)
    for item_id in desejados_itens - atuais_itens:
        db.add(UsuarioCatalogoItem(usuario_id=usuario_obj.id, catalogo_item_id=item_id))

    return desejadas


def definir_zona_gratuita(db: Session, usuario_obj: Usuario, zona_nome: str):
    """Plano inicial/gratuito: exatamente uma zona vinculada por usuário."""
    zona = db.query(Zona).filter(Zona.nome == zona_nome, Zona.ativo == 1).first()
    if not zona:
        return False
    db.query(UsuarioZona).filter(UsuarioZona.usuario_id == usuario_obj.id).delete(synchronize_session=False)
    db.add(UsuarioZona(usuario_id=usuario_obj.id, zona_id=zona.id))
    # Mantém compatibilidade com as rotinas atuais de sorteio.
    usuario_obj.zona = zona.nome
    return True



def _normalizar_texto(valor):
    """Ignora acentos, caixa e espaços extras nas comparações."""
    valor = str(valor or "").strip().casefold()
    valor = unicodedata.normalize("NFKD", valor)
    valor = "".join(ch for ch in valor if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", valor)

def resolver_codigo_ibge(uf: str, municipio_nome: str):
    """Consulta oficial do IBGE e retorna o código do município quando houver correspondência exata."""
    try:
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{urllib.parse.quote(uf)}/municipios"
        dados = _http_json(url)
        alvo = _normalizar_texto(municipio_nome)
        for item in dados:
            if _normalizar_texto(item.get("nome", "")) == alvo:
                return str(item.get("id") or "")
    except Exception:
        return None
    return None


def obter_ou_criar_localidade(db: Session, nome: str, municipio_nome: str, uf: str, estado_nome: str = "",
                              tipo: str = "bairro", osm_id: str = "", lat: str = "", lon: str = ""):
    uf = (uf or "").strip().upper()
    nome = (nome or "").strip()
    municipio_nome = (municipio_nome or "").strip()
    if not nome or not municipio_nome or len(uf) != 2:
        return None

    estado = db.query(Estado).filter(Estado.uf == uf).first()
    if not estado:
        estado = Estado(uf=uf, nome=(estado_nome or uf).strip())
        db.add(estado)
        db.flush()

    municipio = db.query(Municipio).filter(
        Municipio.estado_id == estado.id,
        func.lower(Municipio.nome) == municipio_nome.lower()
    ).first()
    if not municipio:
        codigo = resolver_codigo_ibge(uf, municipio_nome)
        municipio = Municipio(estado_id=estado.id, nome=municipio_nome, codigo_ibge=codigo or None)
        db.add(municipio)
        db.flush()

    localidade = db.query(Localidade).filter(
        Localidade.municipio_id == municipio.id,
        func.lower(Localidade.nome) == nome.lower()
    ).first()
    if not localidade:
        localidade = Localidade(
            municipio_id=municipio.id, nome=nome, tipo=tipo or "bairro",
            osm_id=osm_id or None, latitude=lat or None, longitude=lon or None
        )
        db.add(localidade)
        db.flush()
    return localidade



def item_legado_para_catalogo(db: Session, catalogo_item: CatalogoItem):
    """Mantém compatibilidade com a tabela antiga de indicações enquanto migramos o sorteio."""
    item = db.query(Item).filter(func.lower(Item.nome) == catalogo_item.nome.lower()).first()
    if not item:
        item = Item(nome=catalogo_item.nome, tipo="Serviço", ativo=1)
        db.add(item)
        db.flush()
    return item


def area_da_localidade(db: Session, localidade_id: int):
    vinculo = db.query(AreaLocalidade).filter(AreaLocalidade.localidade_id == localidade_id).first()
    return db.get(Zona, vinculo.area_id) if vinculo else None


def _zona_por_nome_normalizado(db: Session, nomes):
    alvos = {_normalizar_texto(n) for n in nomes}
    for zona in db.query(Zona).filter(Zona.ativo == 1).all():
        if _normalizar_texto(zona.nome) in alvos:
            return zona
    return None


def preclassificar_localidade(db: Session, localidade: Localidade):
    """Pré-classifica automaticamente e grava o vínculo para reutilização."""
    existente = area_da_localidade(db, localidade.id)
    if existente:
        return existente

    municipio = db.get(Municipio, localidade.municipio_id)
    municipio_nome = _normalizar_texto(municipio.nome if municipio else "")
    bairro = _normalizar_texto(localidade.nome)

    def vincular(nomes_zona):
        zona = _zona_por_nome_normalizado(db, nomes_zona)
        if zona:
            db.add(AreaLocalidade(area_id=zona.id, localidade_id=localidade.id))
            db.flush()
        return zona

    if municipio_nome == "rio de janeiro":
        grupos = [
            (["barra / recreio / jacarepagua / vargens"], {
                "barra da tijuca", "recreio dos bandeirantes", "jacarepagua",
                "vargem grande", "vargem pequena", "itanhanga", "joa",
                "camorim", "curicica", "freguesia de jacarepagua",
                "pechincha", "taquara", "tanque", "praca seca", "anil"
            }),
            (["santa cruz / guaratiba"], {
                "santa cruz", "guaratiba", "barra de guaratiba",
                "pedra de guaratiba", "ilha de guaratiba", "paciencia", "sepetiba"
            }),
            (["campo grande"], {
                "campo grande", "cosmos", "senador vasconcelos",
                "santissimo", "augusto vasconcelos"
            }),
            (["centro"], {
                "centro", "lapa", "santa teresa", "gloria", "saude",
                "gamboa", "santo cristo", "cidade nova", "catumbi",
                "estacio", "rio comprido"
            }),
            (["zona sul"], {
                "copacabana", "ipanema", "leblon", "botafogo", "flamengo",
                "laranjeiras", "catete", "cosme velho", "humaita", "gavea",
                "jardim botanico", "lagoa", "leme", "urca", "vidigal",
                "sao conrado", "rocinha"
            }),
            (["zona norte"], {
                "ramos", "penha", "penha circular", "olaria", "bonsucesso",
                "manguinhos", "mare", "ilha do governador", "tijuca",
                "vila isabel", "grajau", "andarai", "maracana", "meier",
                "engenho de dentro", "engenho novo", "piedade", "cachambi",
                "del castilho", "inhauma", "iraja", "vila da penha",
                "vicente de carvalho", "madureira", "cascadura", "quintino",
                "bento ribeiro", "oswaldo cruz", "vaz lobo", "rocha miranda",
                "coelho neto", "acari", "pavuna", "anchieta", "guadalupe"
            }),
        ]
        for zonas_nomes, bairros in grupos:
            if bairro in bairros:
                zona = vincular(zonas_nomes)
                if zona:
                    return zona

        # Para bairro carioca ainda não conhecido, usa uma área ampla provisória.
        return vincular(["Zona Oeste"])

    if municipio_nome in {
        "duque de caxias", "nova iguacu", "sao joao de meriti", "belford roxo",
        "nilopolis", "mesquita", "queimados", "japeri", "mage", "guapimirim",
        "seropedica", "itaguai", "paracambi"
    }:
        return vincular(["Baixada Fluminense"])

    if municipio_nome in {"niteroi", "sao goncalo", "marica", "itaborai", "tangua"}:
        return vincular(["Niterói / São Gonçalo", "Niteroi / Sao Goncalo"])

    return vincular(["Outros RJ"])


def usuario_tem_aberta(db: Session, usuario_id: int) -> bool:
    return db.query(Indicacao).filter(Indicacao.recebido_por_id == usuario_id, Indicacao.status == "Em atendimento").first() is not None


def usuario_tem_aberta_conflitante(db: Session, usuario_id: int, data_evento) -> bool:
    """Bloqueia somente indicações abertas sem data ou da mesma data do novo evento."""
    abertas = db.query(Indicacao).filter(
        Indicacao.recebido_por_id == usuario_id,
        Indicacao.status == "Em atendimento",
    ).all()
    if not abertas:
        return False
    if not data_evento:
        return True
    return any(not existente.data_evento or existente.data_evento == data_evento for existente in abertas)


def zonas_proximas(nome_zona: str):
    """Retorna as zonas vizinhas em ordem de proximidade operacional."""
    normal = _normalizar_texto(nome_zona or "")
    mapa = {
        "zona norte": ["centro", "baixada fluminense", "niteroi / sao goncalo", "zona oeste", "zona sul"],
        "zona sul": ["centro", "barra / recreio / jacarepagua / vargens", "zona norte", "zona oeste"],
        "centro": ["zona sul", "zona norte", "niteroi / sao goncalo", "zona oeste"],
        "barra / recreio / jacarepagua / vargens": ["zona oeste", "zona sul", "campo grande", "santa cruz / guaratiba"],
        "zona oeste": ["barra / recreio / jacarepagua / vargens", "campo grande", "zona norte", "centro"],
        "campo grande": ["zona oeste", "santa cruz / guaratiba", "barra / recreio / jacarepagua / vargens"],
        "santa cruz / guaratiba": ["campo grande", "zona oeste", "costa verde"],
        "baixada fluminense": ["zona norte", "zona oeste", "medio paraiba"],
        "niteroi / sao goncalo": ["marica / itaborai", "centro", "zona norte", "norte / noroeste fluminense"],
        "marica / itaborai": ["niteroi / sao goncalo", "norte / noroeste fluminense", "zona norte"],
        "costa verde": ["santa cruz / guaratiba", "zona oeste", "medio paraiba"],
        "medio paraiba": ["baixada fluminense", "costa verde", "zona oeste"],
    }
    return mapa.get(normal, [])



def normalizar_whatsapp(valor: str) -> str:
    """Normaliza telefone brasileiro, inclusive quando colado do WhatsApp com caracteres invisíveis."""
    texto = unicodedata.normalize("NFKC", str(valor or ""))
    digitos = re.sub(r"\D", "", texto)

    if digitos.startswith("00"):
        digitos = digitos[2:]
    if digitos.startswith("55") and len(digitos) in (12, 13):
        digitos = digitos[2:]
    if digitos.startswith("0") and len(digitos) > 11:
        digitos = digitos[1:]

    return digitos[:11]


def whatsapp_valido(valor: str) -> bool:
    """Exige um número utilizável para cadastro/token."""
    digitos = normalizar_whatsapp(valor)
    return 10 <= len(digitos) <= 15


def normalizar_cpf(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def cpf_valido(valor: str) -> bool:
    cpf = normalizar_cpf(valor)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(cpf[tamanho]):
            return False
    return True


def formatar_cpf(valor: str) -> str:
    digitos = normalizar_cpf(valor)[:11]
    if len(digitos) != 11:
        return digitos or "—"
    return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"


def formatar_telefone(valor: str) -> str:
    digitos = normalizar_whatsapp(valor)
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return digitos or "—"


templates.env.filters["cpf_br"] = formatar_cpf
templates.env.filters["telefone_br"] = formatar_telefone


def normalizar_nome_exibicao(valor: str) -> str:
    partes = re.sub(r"\s+", " ", (valor or "").strip()).split(" ")
    minusculas = {"da", "das", "de", "do", "dos", "e"}
    resultado = []
    for i, parte in enumerate(partes):
        p = parte.lower()
        resultado.append(p if i > 0 and p in minusculas else p[:1].upper() + p[1:])
    return " ".join(resultado)


def nome_completo_valido(valor: str) -> bool:
    nome = normalizar_nome_exibicao(valor)
    partes = [re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ'-]", "", p) for p in nome.split()]
    partes_validas = [p for p in partes if len(p.replace("-", "").replace("'", "")) >= 2]
    return len(partes_validas) >= 2


def buscar_usuario_por_documento_ou_telefone(db: Session, valor: str):
    digitos = re.sub(r"\D", "", valor or "")
    if not digitos:
        return None
    telefone = normalizar_whatsapp(digitos)
    cpf = normalizar_cpf(digitos)

    # Contas ativas e aprovadas sempre têm prioridade. A ordenação evita que
    # um cadastro antigo duplicado/inativo intercepte o login correto.
    usuarios = db.query(Usuario).order_by(
        Usuario.ativo.desc(), Usuario.aprovado.desc(), Usuario.id.asc()
    ).all()
    for usuario in usuarios:
        if cpf and normalizar_cpf(usuario.cpf or "") == cpf:
            return usuario
        if telefone and normalizar_whatsapp(usuario.whatsapp or "") == telefone:
            return usuario
    return None


def gerar_login_interno(db: Session) -> str:
    while True:
        login = "u_" + secrets.token_hex(8)
        if not db.query(Usuario).filter(Usuario.usuario == login).first():
            return login


def garantir_token_indicacao_usuario(db: Session, usuario: Usuario) -> str:
    """Garante um link pessoal de indicação para qualquer usuário autenticado.

    Cadastros antigos podem não possuir token porque a geração anterior dependia
    de WhatsApp válido. O painel não deve esconder o botão por esse motivo.
    """
    token_atual = (usuario.indicacao_token or "").strip().upper()
    if token_atual:
        if usuario.indicacao_token != token_atual:
            usuario.indicacao_token = token_atual
            db.commit()
        return token_atual

    while True:
        token = secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:10].upper()
        if token and not db.query(Usuario).filter(Usuario.indicacao_token == token).first():
            break

    usuario.indicacao_token = token
    db.commit()
    db.refresh(usuario)
    return token


def garantir_tokens_indicacao(db: Session) -> int:
    """Gera tokens faltantes para todos os usuários com WhatsApp válido."""
    usuarios = db.query(Usuario).all()
    tokens_usados = {u.indicacao_token for u in usuarios if u.indicacao_token}
    gerados = 0
    for u in usuarios:
        if u.indicacao_token or not whatsapp_valido(u.whatsapp):
            continue
        while True:
            token = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8].upper()
            if token and token not in tokens_usados:
                break
        u.indicacao_token = token
        tokens_usados.add(token)
        gerados += 1
    if gerados:
        db.commit()
    return gerados


def existe_indicacao_aberta_mesma_categoria(
    db: Session,
    whatsapp: str,
    item_id: int,
):
    """
    Bloqueia somente:
      mesmo WhatsApp + mesma categoria/item + oportunidade ainda aberta.

    O mesmo cliente pode voltar depois que a oportunidade anterior estiver encerrada.
    Futuramente, categorias diferentes poderão coexistir para o mesmo WhatsApp.
    """
    telefone = normalizar_whatsapp(whatsapp)
    if not telefone:
        return None

    status_abertos = {
        "Aguardando classificação",
        "Aguardando sorteio",
        "Em atendimento",
    }

    candidatas = db.query(Indicacao).filter(
        Indicacao.item_id == item_id,
        Indicacao.status.in_(list(status_abertos))
    ).all()

    for ind in candidatas:
        if normalizar_whatsapp(ind.whatsapp) == telefone:
            return ind
    return None



def garantir_cpf_whatsapp_unicos():
    """Normaliza cadastros, bloqueia duplicados antigos e cria proteção no banco.

    Mantém ativo o cadastro mais antigo entre os aprovados/ativos. Os demais
    ficam inativos até o administrador corrigir CPF e WhatsApp. Nenhum registro
    é apagado.
    """
    db = SessionLocal()
    try:
        usuarios = db.query(Usuario).order_by(
            Usuario.ativo.desc(), Usuario.aprovado.desc(), Usuario.id.asc()
        ).all()

        vistos_cpf = {}
        vistos_whatsapp = {}
        for u in usuarios:
            cpf_norm = normalizar_cpf(u.cpf or "")
            tel_norm = normalizar_whatsapp(u.whatsapp or "")
            if cpf_norm:
                u.cpf = cpf_norm
            if tel_norm:
                u.whatsapp = tel_norm

            conflito = False
            if cpf_norm and cpf_norm in vistos_cpf:
                conflito = True
            if tel_norm and tel_norm in vistos_whatsapp:
                conflito = True

            if conflito and not int(u.is_admin or 0):
                u.ativo = 0
                u.aprovado = 0
            else:
                if cpf_norm:
                    vistos_cpf[cpf_norm] = u.id
                if tel_norm:
                    vistos_whatsapp[tel_norm] = u.id

        db.commit()
    finally:
        db.close()

    # Índices parciais garantem unicidade entre contas ativas. Cadastros antigos
    # duplicados permanecem preservados, porém inativos, até serem corrigidos.
    with engine.begin() as conn:
        if IS_POSTGRES:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_cpf_ativo "
                "ON usuarios (cpf) WHERE ativo = 1 AND cpf IS NOT NULL AND cpf <> ''"
            ))
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_whatsapp_ativo "
                "ON usuarios (whatsapp) WHERE ativo = 1 AND whatsapp IS NOT NULL AND whatsapp <> ''"
            ))
        elif IS_SQLITE:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_cpf_ativo "
                "ON usuarios (cpf) WHERE ativo = 1 AND cpf IS NOT NULL AND cpf <> ''"
            ))
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_whatsapp_ativo "
                "ON usuarios (whatsapp) WHERE ativo = 1 AND whatsapp IS NOT NULL AND whatsapp <> ''"
            ))


def aplicar_migracoes_simples():
    """Migrações leves para bancos antigos sem apagar dados existentes."""
    # PostgreSQL não reconhece o tipo DATETIME usado pelo SQLite.
    # As migrações precisam escolher o tipo correto conforme o banco em produção.
    tipo_data_hora = "TIMESTAMP" if IS_POSTGRES else "DATETIME"
    inspector = inspect(engine)
    tabelas = set(inspector.get_table_names())

    # Cache de validação do cliente/equipamentos Karaoke RJ.
    if "usuarios" in tabelas:
        colunas = {c["name"] for c in inspector.get_columns("usuarios")}
        comandos_usuarios = []
        if "email" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN email VARCHAR(180)")
        if "humiat_user_id" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN humiat_user_id VARCHAR(64)")
        if "cpf" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN cpf VARCHAR(20)")
        if "krj_validado" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN krj_validado INTEGER NOT NULL DEFAULT 0")
        if "krj_cliente_id" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN krj_cliente_id VARCHAR(60)")
        if "krj_jukebox_qtd" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN krj_jukebox_qtd INTEGER NOT NULL DEFAULT 0")
        if "krj_portatil_qtd" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN krj_portatil_qtd INTEGER NOT NULL DEFAULT 0")
        if "krj_iphone_qtd" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN krj_iphone_qtd INTEGER NOT NULL DEFAULT 0")
        if "krj_fliperama_qtd" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN krj_fliperama_qtd INTEGER NOT NULL DEFAULT 0")
        if "krj_atualizacao" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN krj_atualizacao VARCHAR(40)")
        if "krj_validado_em" not in colunas:
            comandos_usuarios.append(f"ALTER TABLE usuarios ADD COLUMN krj_validado_em {tipo_data_hora}")
        if "krj_equipamentos_json" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN krj_equipamentos_json TEXT")
        if "indicacao_token" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN indicacao_token VARCHAR(32)")
        if "somente_zona_propria" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN somente_zona_propria INTEGER NOT NULL DEFAULT 0")
        if "zonas_bloqueadas_json" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN zonas_bloqueadas_json TEXT")
        if "zonas_bloqueadas_atualizadas_em" not in colunas:
            comandos_usuarios.append(f"ALTER TABLE usuarios ADD COLUMN zonas_bloqueadas_atualizadas_em {tipo_data_hora}")
        if "grupo_locadores" not in colunas:
            comandos_usuarios.append("ALTER TABLE usuarios ADD COLUMN grupo_locadores INTEGER NOT NULL DEFAULT 0")
        for comando in comandos_usuarios:
            with engine.begin() as conn:
                conn.execute(text(comando))
        # Índices leves para o SSO. `humiat_user_id` é único quando preenchido.
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_humiat_user_id "
                "ON usuarios (humiat_user_id) WHERE humiat_user_id IS NOT NULL AND humiat_user_id <> ''"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_usuarios_email_lower "
                "ON usuarios (lower(email))"
            ))

    # usuarios.aprovado
    if "usuarios" in tabelas:
        colunas = {c["name"] for c in inspector.get_columns("usuarios")}
        if "aprovado" not in colunas:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN aprovado INTEGER NOT NULL DEFAULT 1"))

    # Controle de tempo/aceite das oportunidades.
    if "tentativas" in tabelas:
        definicoes_tentativas = {c["name"]: c for c in inspector.get_columns("tentativas")}
        colunas_tentativas = set(definicoes_tentativas)

        # O resultado pode incluir o motivo informado pelo participante. Bancos
        # antigos criaram esta coluna como VARCHAR(30), causando erro ao finalizar
        # ou repassar com mensagens maiores, como "Cliente não deseja: Não respondeu".
        # No PostgreSQL, convertemos definitivamente para TEXT. No SQLite, o tipo
        # VARCHAR não impõe esse limite e não precisa reconstruir a tabela.
        if IS_POSTGRES and "resultado" in colunas_tentativas:
            tipo_resultado = definicoes_tentativas["resultado"].get("type")
            if not isinstance(tipo_resultado, Text):
                with engine.begin() as conn:
                    conn.execute(text(
                        "ALTER TABLE tentativas "
                        "ALTER COLUMN resultado TYPE TEXT "
                        "USING resultado::TEXT"
                    ))

        if "aceite_em" not in colunas_tentativas:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE tentativas ADD COLUMN aceite_em {tipo_data_hora}"))
        if "rodada" not in colunas_tentativas:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE tentativas ADD COLUMN rodada INTEGER NOT NULL DEFAULT 1"))
        # Permite que o mesmo participante volte somente quando o administrador
        # iniciar conscientemente uma nova rodada. Dentro da mesma rodada ele
        # continua podendo receber a indicação apenas uma vez.
        if IS_POSTGRES:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE tentativas DROP CONSTRAINT IF EXISTS uq_tentativa_usuario"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_tentativa_usuario_rodada ON tentativas (indicacao_id, usuario_id, rodada)"))

    # Novos campos geográficos em indicacoes.
    if "indicacoes" in tabelas:
        colunas = {c["name"] for c in inspector.get_columns("indicacoes")}
        comandos = []
        if "localidade_id" not in colunas:
            comandos.append("ALTER TABLE indicacoes ADD COLUMN localidade_id INTEGER")
        if "area_id" not in colunas:
            comandos.append("ALTER TABLE indicacoes ADD COLUMN area_id INTEGER")
        if "local_texto" not in colunas:
            comandos.append("ALTER TABLE indicacoes ADD COLUMN local_texto VARCHAR(220)")
        if "catalogo_item_id" not in colunas:
            comandos.append("ALTER TABLE indicacoes ADD COLUMN catalogo_item_id INTEGER")
        if "categoria_id" not in colunas:
            comandos.append("ALTER TABLE indicacoes ADD COLUMN categoria_id INTEGER")
        if "pedido_token" not in colunas:
            comandos.append("ALTER TABLE indicacoes ADD COLUMN pedido_token VARCHAR(40)")
        if "item_solicitado_texto" not in colunas:
            comandos.append("ALTER TABLE indicacoes ADD COLUMN item_solicitado_texto VARCHAR(180)")
        if "sorteio_rodada" not in colunas:
            comandos.append("ALTER TABLE indicacoes ADD COLUMN sorteio_rodada INTEGER NOT NULL DEFAULT 1")
        if "whatsapp_encaminhado_em" not in colunas:
            comandos.append(f"ALTER TABLE indicacoes ADD COLUMN whatsapp_encaminhado_em {tipo_data_hora}")
        if "observacao" not in colunas:
            comandos.append("ALTER TABLE indicacoes ADD COLUMN observacao TEXT")
        if "equipamentos_json" not in colunas:
            comandos.append("ALTER TABLE indicacoes ADD COLUMN equipamentos_json TEXT")
        if "tipos_servico_json" not in colunas:
            comandos.append("ALTER TABLE indicacoes ADD COLUMN tipos_servico_json TEXT")
        for comando in comandos:
            with engine.begin() as conn:
                conn.execute(text(comando))
@app.on_event("startup")
def iniciar_banco():
    if IS_PRODUCTION:
        erros = []
        if IS_SQLITE:
            erros.append("DATABASE_URL não pode usar SQLite em produção")
        if ADMIN_SENHA == "admin123":
            erros.append("Defina LOKAFEST_ADMIN_SENHA com uma senha forte")
        if CHAVE_SESSAO == "lokafest-dev-key-change-me":
            erros.append("Defina LOKAFEST_SESSION_KEY com uma chave secreta forte")
        if erros:
            raise RuntimeError("Configuração de produção inválida: " + " | ".join(erros))

    Base.metadata.create_all(bind=engine)
    aplicar_migracoes_simples()
    garantir_cpf_whatsapp_unicos()
    db = SessionLocal()
    try:
        admin_existente = db.query(Usuario).filter(Usuario.usuario == ADMIN_USUARIO).first()
        if admin_existente:
            # Não sobrescreve a senha em cada inicialização/redeploy. A senha
            # redefinida pelo usuário deve permanecer válida no banco.
            if IS_PRODUCTION:
                admin_existente.is_admin = 1
                admin_existente.ativo = 1
                admin_existente.aprovado = 1
        elif not db.query(Usuario).first():
            db.add(Usuario(nome="Administrador", usuario=ADMIN_USUARIO, whatsapp="", senha_hash=gerar_hash_senha(ADMIN_SENHA), zona="Zona Norte", is_admin=1, ativo=1, aprovado=1))

        # Corrige logins antigos que foram cadastrados com espaços. Ex.:
        # "Carlos Henrique" -> "CarlosHenrique". Só altera quando não há conflito.
        db.flush()
        for usuario_existente in db.query(Usuario).all():
            login_antigo = usuario_existente.usuario or ""
            login_novo = normalizar_login(login_antigo)
            if login_novo and login_novo != login_antigo:
                conflito = db.query(Usuario).filter(
                    Usuario.usuario == login_novo, Usuario.id != usuario_existente.id
                ).first()
                if conflito:
                    print(
                        f"AVISO LOGIN: não foi possível remover espaços de '{login_antigo}' "
                        f"porque '{login_novo}' já existe.",
                        flush=True,
                    )
                else:
                    usuario_existente.usuario = login_novo
                    print(f"LOGIN NORMALIZADO: '{login_antigo}' -> '{login_novo}'", flush=True)

        if not db.query(Item).filter(func.lower(Item.nome) == "karaokê".lower()).first():
            db.add(Item(nome="Karaokê", tipo="Produto", ativo=1))
        if not any(_normalizar_texto(i.nome) == "fliperama" for i in db.query(Item).all()):
            db.add(Item(nome="Fliperama", tipo="Produto", ativo=1))
        if not any(_normalizar_texto(i.nome) == "karaoke + fliperama" for i in db.query(Item).all()):
            db.add(Item(nome="Karaokê + Fliperama", tipo="Produto", ativo=1))
        # Seed idempotente das zonas. Em Cloud Run mais de uma instância pode
        # iniciar ao mesmo tempo; ON CONFLICT evita UniqueViolation nesse cenário.
        zonas_iniciais = [
            "Centro",
            "Zona Norte",
            "Zona Sul",
            "Zona Oeste",
            "Barra / Recreio / Jacarepaguá / Vargens",
            "Campo Grande",
            "Santa Cruz / Guaratiba",
            "Baixada Fluminense",
            "Niterói / São Gonçalo",
            "Maricá / Itaboraí",
            "Região Serrana",
            "Região dos Lagos",
            "Costa Verde",
            "Médio Paraíba",
            "Norte / Noroeste Fluminense",
            "Outros RJ",
        ]
        if IS_SQLITE:
            for nome_zona in zonas_iniciais:
                db.execute(
                    text("INSERT OR IGNORE INTO zonas (nome, ativo) VALUES (:nome, 1)"),
                    {"nome": nome_zona},
                )
        else:
            for nome_zona in zonas_iniciais:
                db.execute(
                    text(
                        "INSERT INTO zonas (nome, ativo) VALUES (:nome, 1) "
                        "ON CONFLICT (nome) DO NOTHING"
                    ),
                    {"nome": nome_zona},
                )
        db.flush()

        if not db.query(Categoria).first():
            cat = Categoria(nome="Karaokê", ativo=1)
            db.add(cat)
            db.flush()
            for nome_item in ["Portátil", "Jukebox", "iPhone"]:
                db.add(CatalogoItem(categoria_id=cat.id, nome=nome_item, ativo=1))
        # Fliperama passa a ser uma categoria disponível. A aptidão não depende
        # de catálogo/atualização; basta existir ao menos um fliperama ativo no Organiza.
        fliperama_cat = next((c for c in db.query(Categoria).all() if _normalizar_texto(c.nome) == "fliperama"), None)
        if not fliperama_cat:
            fliperama_cat = Categoria(nome="Fliperama", ativo=1)
            db.add(fliperama_cat)
            db.flush()
        if not db.query(CatalogoItem).filter(
            CatalogoItem.categoria_id == fliperama_cat.id,
            func.lower(CatalogoItem.nome) == "fliperama"
        ).first():
            db.add(CatalogoItem(categoria_id=fliperama_cat.id, nome="Fliperama", ativo=1))
        db.flush()

        # Garante tokens também para usuários antigos com WhatsApp válido.
        garantir_tokens_indicacao(db)

        # Migra usuários antigos para a nova tabela de vínculo de zonas.
        for usuario_existente in db.query(Usuario).all():
            if not db.query(UsuarioZona).filter(UsuarioZona.usuario_id == usuario_existente.id).first():
                zona_existente = db.query(Zona).filter(Zona.nome == usuario_existente.zona).first()
                if zona_existente:
                    db.add(UsuarioZona(usuario_id=usuario_existente.id, zona_id=zona_existente.id))
        # Fase atual: Karaokê e Fliperama ficam disponíveis.
        for categoria_inicio in db.query(Categoria).all():
            categoria_inicio.ativo = 1 if _normalizar_texto(categoria_inicio.nome) in {"karaoke", "fliperama"} else 0

        # Primeira regra de validação: catálogo obrigatório para Karaokê.
        karaoke_cat = next(
            (c for c in db.query(Categoria).all() if _normalizar_texto(c.nome) == "karaoke"),
            None
        )
        if karaoke_cat and not db.query(RegraValidacao).filter(
            RegraValidacao.tipo == "catalogo_obrigatorio",
            RegraValidacao.categoria_id == karaoke_cat.id
        ).first():
            db.add(RegraValidacao(
                nome="Catálogo obrigatório Karaokê",
                tipo="catalogo_obrigatorio",
                categoria_id=karaoke_cat.id,
                valor_obrigatorio="2026.1",
                mensagem_bloqueio="Você não está apto no momento. Favor atualizar o equipamento ou os equipamentos da Karaoke RJ para o catálogo obrigatório.",
                ativo=1
            ))
        db.commit()
    finally:
        db.close()


def _logo_parceira_otimizada(data: bytes) -> tuple[bytes, str]:
    """Gera a miniatura local usada apenas pela faixa pública da LokaFest."""
    from PIL import Image
    if not data:
        raise ValueError("Logo vazia")
    with Image.open(BytesIO(data)) as img:
        try:
            img.seek(0)
        except Exception:
            pass
        tem_alpha = img.mode in {"RGBA", "LA"} or (img.mode == "P" and "transparency" in img.info)
        img = img.convert("RGBA" if tem_alpha else "RGB")
        img.thumbnail((220, 100), Image.Resampling.LANCZOS)
        saida = BytesIO()
        img.save(saida, format="WEBP", quality=80, method=6)
        return saida.getvalue(), "image/webp"


def _empresas_parceiras_locais(db: Session) -> list[dict]:
    """Lista somente o banco local. Nunca consulta o Organiza durante a Home."""
    rows = (
        db.query(EmpresaParceira)
        .filter(EmpresaParceira.ativo == 1, EmpresaParceira.logo_data.isnot(None))
        .order_by(EmpresaParceira.nome.asc())
        .all()
    )
    itens = []
    for row in rows:
        versao = str(row.logo_hash or "")[:12]
        url = f"/media/empresas-parceiras/{int(row.id)}/logo"
        if versao:
            url += f"?v={versao}"
        itens.append({
            "id": int(row.id),
            "organiza_id": int(row.organiza_id),
            "nome": str(row.nome or "").strip(),
            "slug": str(row.slug or "").strip(),
            "logo_url": url,
            "sincronizado_em": row.sincronizado_em,
        })
    return itens


def _organiza_empresas_para_sync() -> list[dict]:
    """Consulta o Organiza somente quando o administrador clicar em atualizar."""
    url = f"{ORGANIZA_PUBLIC_BASE_URL}/api/publico/lokafest/empresas"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": f"LokaFest/{APP_VERSION}"},
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return list((payload or {}).get("empresas") or [])


def _baixar_logo_parceira(url: str) -> bytes:
    logo_url = str(url or "").strip()
    if not logo_url:
        raise ValueError("Empresa sem logo")
    if not logo_url.startswith(("http://", "https://")):
        logo_url = ORGANIZA_PUBLIC_BASE_URL.rstrip("/") + "/" + logo_url.lstrip("/")
    req = urllib.request.Request(
        logo_url,
        headers={
            "Accept": "image/webp,image/png,image/jpeg,image/*;q=0.8",
            "User-Agent": f"LokaFest/{APP_VERSION}",
        },
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        ctype = str(resp.headers.get("Content-Type") or "").lower()
        if ctype and not ctype.startswith("image/"):
            raise ValueError("O Organiza não retornou uma imagem")
        data = resp.read(3 * 1024 * 1024 + 1)
    if len(data) > 3 * 1024 * 1024:
        raise ValueError("Logo maior que 3 MB")
    if not data:
        raise ValueError("Logo vazia")
    return data


def _sincronizar_empresas_parceiras(db: Session) -> dict:
    """Copia empresas/logos do Organiza para o banco local do LokaFest."""
    origem = _organiza_empresas_para_sync()
    agora = datetime.now()
    vistos: set[int] = set()
    criadas = atualizadas = iguais = erros = 0

    for item in origem:
        try:
            organiza_id = int(item.get("id") or 0)
        except Exception:
            organiza_id = 0
        nome = str(item.get("nome") or "").strip()[:160]
        slug = str(item.get("slug") or "").strip()[:120]
        logo_url = str(item.get("logo_url") or "").strip()
        if not organiza_id or not nome or not logo_url:
            continue
        vistos.add(organiza_id)
        row = db.query(EmpresaParceira).filter(EmpresaParceira.organiza_id == organiza_id).first()
        nova = row is None
        if nova:
            row = EmpresaParceira(organiza_id=organiza_id, nome=nome, slug=slug, ativo=1)
            db.add(row)
            db.flush()
            criadas += 1
        row.nome = nome
        row.slug = slug
        row.ativo = 1
        row.sincronizado_em = agora
        try:
            raw = _baixar_logo_parceira(logo_url)
            mini, mime = _logo_parceira_otimizada(raw)
            digest = hashlib.sha256(mini).hexdigest()
            if digest != str(row.logo_hash or "") or not row.logo_data:
                row.logo_data = mini
                row.logo_mime = mime
                row.logo_hash = digest
                atualizadas += 1
            else:
                iguais += 1
        except Exception as exc:
            erros += 1
            print(f"[LOKAFEST EMPRESAS] Falha na logo {nome}: {exc}")

    if vistos:
        for row in db.query(EmpresaParceira).filter(EmpresaParceira.ativo == 1).all():
            if int(row.organiza_id or 0) not in vistos:
                row.ativo = 0
                row.sincronizado_em = agora
    db.commit()
    return {
        "recebidas": len(origem),
        "criadas": criadas,
        "logos_atualizadas": atualizadas,
        "logos_iguais": iguais,
        "erros": erros,
        "ativas": db.query(EmpresaParceira).filter(EmpresaParceira.ativo == 1, EmpresaParceira.logo_data.isnot(None)).count(),
    }


@app.get("/api/publico/empresas-parceiras", include_in_schema=False)
def api_publico_empresas_parceiras(db: Session = Depends(get_db)):
    empresas = _empresas_parceiras_locais(db)
    return JSONResponse(
        {"ok": True, "total": len(empresas), "empresas": empresas, "origem": "lokafest_local"},
        headers={"Cache-Control": "public, max-age=300, stale-while-revalidate=3600"},
    )


@app.get("/media/empresas-parceiras/{empresa_id}/logo", include_in_schema=False)
def empresa_parceira_logo(empresa_id: int, db: Session = Depends(get_db)):
    row = db.query(EmpresaParceira).filter(EmpresaParceira.id == int(empresa_id), EmpresaParceira.ativo == 1).first()
    if not row or not row.logo_data:
        raise HTTPException(status_code=404, detail="Logo não disponível")
    data = bytes(row.logo_data)
    etag = str(row.logo_hash or hashlib.sha256(data).hexdigest())
    return Response(
        content=data,
        media_type=str(row.logo_mime or "image/webp"),
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": f'"{etag}"',
        },
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "empresas_parceiras": _empresas_parceiras_locais(db)},
    )


@app.get("/admin/empresas-parceiras", response_class=HTMLResponse)
def admin_empresas_parceiras(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    empresas = db.query(EmpresaParceira).order_by(EmpresaParceira.ativo.desc(), EmpresaParceira.nome.asc()).all()
    ultima = db.query(func.max(EmpresaParceira.sincronizado_em)).scalar()
    return templates.TemplateResponse("empresas_parceiras.html", {
        "request": request,
        "usuario": usuario,
        "empresas": empresas,
        "ultima_sincronizacao": ultima,
        "total_ativas": sum(1 for e in empresas if int(e.ativo or 0) and e.logo_data),
    })


@app.post("/admin/empresas-parceiras/atualizar")
def admin_empresas_parceiras_atualizar(usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    try:
        r = _sincronizar_empresas_parceiras(db)
        msg = (
            f"Atualização concluída: {r['ativas']} empresa(s) ativa(s), "
            f"{r['logos_atualizadas']} logo(s) atualizada(s) e {r['erros']} erro(s)."
        )
        return RedirectResponse(f"/admin/empresas-parceiras?ok={quote_plus(msg)}", status_code=303)
    except Exception as exc:
        db.rollback()
        return RedirectResponse(
            f"/admin/empresas-parceiras?erro={quote_plus('Não foi possível atualizar: ' + str(exc))}",
            status_code=303,
        )


@app.get("/api/organiza/validar-cliente")
def validar_cliente_organiza(
    cpf: str = "",
    whatsapp: str = "",
    cliente_id: str = "",
    maquina: str = "",
    db: Session = Depends(get_db),
):
    if (
        not _somente_digitos(cpf)
        and not _somente_digitos(whatsapp)
        and not _somente_digitos(cliente_id)
        and not (maquina or "").strip()
    ):
        return JSONResponse({
            "ok": False,
            "mensagem": "Informe CPF, WhatsApp ou número da máquina."
        }, status_code=400)

    resultado = consultar_organiza_cliente(cpf, whatsapp, cliente_id=cliente_id, maquina=maquina)

    karaoke_id = _categoria_karaoke_id(db)
    if resultado.get("ok") and resultado.get("encontrado") and karaoke_id:
        resultado = _aplicar_regra_catalogo_no_resultado(db, resultado, karaoke_id)

    status = 200 if resultado.get("ok") else 503
    return JSONResponse(resultado, status_code=status)


@app.get("/cadastro", response_class=HTMLResponse)
def cadastro_publico_form(request: Request, db: Session = Depends(get_db)):
    zonas = [z.nome for z in db.query(Zona).filter(Zona.ativo == 1).order_by(Zona.nome).all()]
    categorias = db.query(Categoria).filter(Categoria.ativo == 1).order_by(Categoria.nome).all()
    catalogo_itens = db.query(CatalogoItem).filter(CatalogoItem.ativo == 1).order_by(CatalogoItem.nome).all()
    itens_por_categoria = {}
    for ci in catalogo_itens:
        itens_por_categoria.setdefault(ci.categoria_id, []).append(ci)
    return templates.TemplateResponse("cadastro_publico.html", {
        "request": request,
        "zonas": zonas,
        "categorias": categorias,
        "itens_por_categoria": itens_por_categoria
    })


@app.post("/cadastro")
async def cadastro_publico_criar(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    nome = normalizar_nome_exibicao(form.get("nome") or "")
    whatsapp = (form.get("whatsapp") or "").strip()
    cpf = normalizar_cpf(form.get("cpf") or "")
    senha = form.get("senha") or ""
    zona_nome = (form.get("zona") or "").strip()

    if not nome_completo_valido(nome):
        return RedirectResponse("/cadastro?erro=Favor informar um nome completo correto. Essa informação será exibida ao cliente final.", status_code=303)
    if not whatsapp or not cpf or not senha:
        return RedirectResponse("/cadastro?erro=Nome completo, CPF, WhatsApp e senha são obrigatórios", status_code=303)
    if not whatsapp_valido(whatsapp):
        return RedirectResponse("/cadastro?erro=Informe um WhatsApp válido com DDD", status_code=303)
    if not cpf_valido(cpf):
        return RedirectResponse("/cadastro?erro=Informe um CPF válido", status_code=303)
    if any(normalizar_cpf(u.cpf or "") == cpf for u in db.query(Usuario).all()):
        return RedirectResponse("/cadastro?erro=Este CPF já está cadastrado", status_code=303)
    telefone_normalizado = normalizar_whatsapp(whatsapp)
    if any(normalizar_whatsapp(u.whatsapp or "") == telefone_normalizado for u in db.query(Usuario).all()):
        return RedirectResponse("/cadastro?erro=Este WhatsApp já está cadastrado", status_code=303)

    zona_obj = db.query(Zona).filter(Zona.nome == zona_nome, Zona.ativo == 1).first()
    if not zona_obj:
        return RedirectResponse("/cadastro?erro=Selecione uma zona válida", status_code=303)

    zonas_ativas = {zona.nome for zona in db.query(Zona).filter(Zona.ativo == 1).all()}
    zonas_bloqueadas = [z for z in form.getlist("zonas_bloqueadas") if z in zonas_ativas]
    if len(zonas_bloqueadas) >= len(zonas_ativas):
        return RedirectResponse(
            "/admin/usuarios/novo?erro=Desmarque pelo menos uma zona que este usuário atende",
            status_code=303,
        )

    novo = Usuario(
        nome=nome,
        usuario=gerar_login_interno(db),
        whatsapp=telefone_normalizado,
        cpf=cpf,
        senha_hash=gerar_hash_senha(senha),
        zona=zona_obj.nome,
        is_admin=0,
        ativo=1,
        aprovado=0
    )
    db.add(novo)
    db.flush()
    definir_zona_gratuita(db, novo, zona_obj.nome)

    categoria_id_raw = (form.get("categoria_principal") or "").strip()
    if not categoria_id_raw.isdigit():
        db.rollback()
        return RedirectResponse("/cadastro?erro=Escolha uma categoria principal", status_code=303)

    categoria_id = int(categoria_id_raw)
    karaoke_id = _categoria_karaoke_id(db)
    fliperama_id = _categoria_fliperama_id(db)

    if karaoke_id and categoria_id == karaoke_id:
        # A validação de Karaokê nunca deve depender apenas do JavaScript ou de
        # campos ocultos enviados pelo navegador. Consulta novamente o Organiza
        # no servidor para garantir que clientes antigos e celulares com falha
        # de script consigam concluir o cadastro com segurança.
        resultado_krj = consultar_organiza_cliente(cpf, telefone_normalizado)
        if resultado_krj.get("ok") and resultado_krj.get("encontrado"):
            resultado_krj = _aplicar_regra_catalogo_no_resultado(db, resultado_krj, karaoke_id)
        else:
            db.rollback()
            mensagem = resultado_krj.get("mensagem") or (
                "Não foi possível validar seus equipamentos da Karaoke RJ. "
                "Confira o CPF e o WhatsApp ou tente novamente."
            )
            return RedirectResponse(
                f"/cadastro?erro={quote_plus(mensagem)}",
                status_code=303
            )

        aplicar_cache_krj(novo, resultado_krj)

        if (
            not resultado_krj.get("cliente_id")
            or (
                int(resultado_krj.get("jukebox") or 0) <= 0
                and int(resultado_krj.get("portatil") or 0) <= 0
                and int(resultado_krj.get("iphone") or 0) <= 0
            )
        ):
            db.rollback()
            return RedirectResponse(
                "/cadastro?erro=Cliente localizado, mas nenhum equipamento válido de Karaokê foi encontrado no Organiza",
                status_code=303
            )

    if fliperama_id and categoria_id == fliperama_id:
        # Para Fliperama não existe regra de catálogo: basta possuir ao menos um
        # Fliperama ativo no Organiza.
        resultado_flip = consultar_organiza_cliente(cpf, telefone_normalizado)
        if not (resultado_flip.get("ok") and resultado_flip.get("encontrado")):
            db.rollback()
            mensagem = resultado_flip.get("mensagem") or "Não foi possível validar seus equipamentos no Organiza."
            return RedirectResponse(f"/cadastro?erro={quote_plus(mensagem)}", status_code=303)
        aplicar_cache_krj(novo, resultado_flip)
        if int(resultado_flip.get("fliperama") or 0) <= 0:
            db.rollback()
            return RedirectResponse(
                "/cadastro?erro=Cliente localizado, mas nenhum Fliperama ativo foi encontrado no Organiza",
                status_code=303
            )

    catalogo_ids = [x for x in form.getlist("catalogo_itens") if str(x).isdigit()]
    if not definir_categoria_gratuita(db, novo, categoria_id, catalogo_ids):
        db.rollback()
        return RedirectResponse("/cadastro?erro=Categoria inválida", status_code=303)

    validacao_local = validar_usuario_regras(db, novo, categoria_id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(
            "/cadastro?erro=CPF ou WhatsApp já cadastrado. Cada CPF e telefone podem pertencer a apenas uma conta.",
            status_code=303
        )

    categoria_criada = db.get(Categoria, categoria_id)
    params = (
        f"nome={quote_plus(novo.nome)}"
        f"&categoria={quote_plus(categoria_criada.nome if categoria_criada else '')}"
        f"&zona={quote_plus(novo.zona or '')}"
        f"&jukebox={int(novo.krj_jukebox_qtd or 0)}"
        f"&portatil={int(novo.krj_portatil_qtd or 0)}"
        f"&iphone={int(novo.krj_iphone_qtd or 0)}"
        f"&fliperama={int(novo.krj_fliperama_qtd or 0)}"
        f"&atualizacao={quote_plus(novo.krj_atualizacao or '—')}"
        f"&apto={'1' if validacao_local['apto'] else '0'}"
    )
    return RedirectResponse(f"/cadastro/sucesso?{params}", status_code=303)



@app.get("/cadastro/sucesso", response_class=HTMLResponse)
def cadastro_sucesso(request: Request):
    return templates.TemplateResponse("cadastro_sucesso.html", {
        "request": request,
        "usuario": None,
        "nome": request.query_params.get("nome", ""),
        "categoria": request.query_params.get("categoria", "Karaokê"),
        "zona": request.query_params.get("zona", ""),
        "jukebox": request.query_params.get("jukebox", "0"),
        "portatil": request.query_params.get("portatil", "0"),
        "iphone": request.query_params.get("iphone", "0"),
        "fliperama": request.query_params.get("fliperama", "0"),
        "atualizacao": request.query_params.get("atualizacao", "—"),
        "apto": request.query_params.get("apto", "0") == "1",
    })


@app.get("/entrar", response_class=HTMLResponse)
def login(request: Request, erro: str = "", diagnostico: str = "", next: str = ""):
    destino = next if next.startswith("/") and not next.startswith("//") else ""
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "erro": erro, "diagnostico": diagnostico, "next": destino}
    )


def _token_diagnostico_login(login: str) -> str:
    """Token curto assinado para diagnosticar o redirecionamento sem expor segredos."""
    ts = str(int(datetime.utcnow().timestamp()))
    payload = f"{login}|{ts}"
    sig = hmac.new(CHAVE_SESSAO.encode(), f"diag:{payload}".encode(), hashlib.sha256).hexdigest()
    return urllib.parse.quote_plus(f"{payload}|{sig}")


def _ler_token_diagnostico(token: str):
    try:
        bruto = urllib.parse.unquote_plus(token or "")
        login, ts, sig = bruto.rsplit("|", 2)
        esperado = hmac.new(CHAVE_SESSAO.encode(), f"diag:{login}|{ts}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, esperado):
            return None, "Token de diagnóstico com assinatura inválida."
        idade = int(datetime.utcnow().timestamp()) - int(ts)
        if idade < 0 or idade > 300:
            return None, "Token de diagnóstico expirado. Faça o login novamente."
        return login, None
    except Exception:
        return None, "Token de diagnóstico inválido."


@app.post("/entrar")
def entrar(
    identificador: str = Form(...),
    senha: str = Form(...),
    next: str = Form(""),
    db: Session = Depends(get_db)
):
    login_digitado = normalizar_login(identificador or "")

    # Diagnóstico detalhado: consulta primeiro sem filtros para informar exatamente
    # em qual etapa a autenticação foi interrompida. Nunca exibe senha ou hash.
    encontrado = buscar_usuario_por_documento_ou_telefone(db, identificador)
    if not encontrado and login_digitado == ADMIN_USUARIO:
        encontrado = db.query(Usuario).filter(Usuario.usuario == ADMIN_USUARIO).first()
    if not encontrado:
        return RedirectResponse(
            f"/entrar?erro={quote_plus('LOGIN-01: CPF ou telefone não encontrado no banco conectado pela aplicação.')}"
            f"&diagnostico={quote_plus('Verifique se o Cloud Run está apontando para o mesmo DATABASE_URL/Supabase que você está visualizando.')}" ,
            status_code=303
        )

    if int(encontrado.ativo or 0) != 1:
        return RedirectResponse(
            f"/entrar?erro={quote_plus('LOGIN-02: Usuário encontrado, porém está inativo (ativo != 1).')}",
            status_code=303
        )

    if int(encontrado.aprovado or 0) != 1:
        return RedirectResponse(
            f"/entrar?erro={quote_plus('LOGIN-03: Usuário encontrado e ativo, porém não está aprovado (aprovado != 1).')}",
            status_code=303
        )

    hash_valido = isinstance(encontrado.senha_hash, str) and encontrado.senha_hash.startswith("pbkdf2_sha256$")
    if not hash_valido:
        return RedirectResponse(
            f"/entrar?erro={quote_plus('LOGIN-04: O formato do hash de senha salvo no banco é incompatível com esta versão do sistema.')}",
            status_code=303
        )

    senha_ok = verificar_senha(senha, encontrado.senha_hash)

    # Senha de emergência do administrador.
    if encontrado.usuario == ADMIN_USUARIO and hmac.compare_digest(senha, ADMIN_SENHA):
        if not senha_ok:
            encontrado.senha_hash = gerar_hash_senha(ADMIN_SENHA)
        encontrado.is_admin = 1
        encontrado.ativo = 1
        encontrado.aprovado = 1
        senha_ok = True

    if not senha_ok:
        return RedirectResponse(
            f"/entrar?erro={quote_plus('LOGIN-05: Usuário encontrado, ativo e aprovado, mas a senha não confere com o hash salvo no banco.')}",
            status_code=303
        )

    try:
        encontrado.online = 1
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"LOGIN-06 erro ao gravar online: {type(exc).__name__}: {exc}", flush=True)
        return RedirectResponse(
            f"/entrar?erro={quote_plus('LOGIN-06: Senha correta, mas ocorreu erro ao gravar a sessão do usuário no banco. Consulte o log do Cloud Run.')}",
            status_code=303
        )

    # Links de oportunidade retornam diretamente ao endereço solicitado após o login.
    # Nos demais acessos, preserva a tela de diagnóstico já usada pelo sistema.
    destino_seguro = next if next.startswith("/") and not next.startswith("//") else ""
    if destino_seguro:
        resposta = RedirectResponse(destino_seguro, status_code=303)
    else:
        resposta = RedirectResponse("/painel", status_code=303)
    resposta.set_cookie(
        COOKIE_SESSAO,
        f"{encontrado.usuario}.{assinatura(encontrado.usuario)}",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="none" if IS_PRODUCTION else "lax",
        max_age=60 * 60 * 24 * 30,
        path="/"
    )
    return resposta


@app.get("/login-diagnostico", response_class=HTMLResponse)
def login_diagnostico(request: Request, token: str = "", db: Session = Depends(get_db)):
    login_esperado, erro_token = _ler_token_diagnostico(token)
    etapas = []

    if erro_token:
        etapas.append(("LOGIN-07", False, erro_token))
        return templates.TemplateResponse("login_diagnostico.html", {"request": request, "etapas": etapas, "sucesso": False})

    etapas.append(("LOGIN-01 a LOGIN-06", True, "Usuário, status, senha e gravação no banco foram validados com sucesso."))

    cookie_bruto = request.cookies.get(COOKIE_SESSAO, "")
    if not cookie_bruto:
        etapas.append(("LOGIN-08", False, "O servidor enviou o cookie de sessão, mas ele NÃO voltou na requisição seguinte. O bloqueio está no cookie/domínio/HTTPS/proxy Firebase-Cloud Run."))
        print(f"LOGIN-08 cookie ausente para usuario={login_esperado} host={request.headers.get('host')} proto={request.headers.get('x-forwarded-proto')}", flush=True)
        return templates.TemplateResponse("login_diagnostico.html", {"request": request, "etapas": etapas, "sucesso": False})

    etapas.append(("LOGIN-08", True, "Cookie __session retornou corretamente ao servidor pelo Firebase Hosting."))

    login_cookie_validado = login_cookie(request)
    if not login_cookie_validado:
        etapas.append(("LOGIN-09", False, "O cookie existe, mas a assinatura da sessão é inválida. Provável divergência da variável LOKAFEST_SESSION_KEY entre instâncias/revisões."))
        print(f"LOGIN-09 assinatura invalida host={request.headers.get('host')}", flush=True)
        return templates.TemplateResponse("login_diagnostico.html", {"request": request, "etapas": etapas, "sucesso": False})

    etapas.append(("LOGIN-09", True, "Assinatura criptográfica da sessão é válida."))

    if login_cookie_validado != login_esperado:
        etapas.append(("LOGIN-10", False, "O cookie pertence a outro usuário/sessão. Limpe os cookies do domínio e tente novamente."))
        return templates.TemplateResponse("login_diagnostico.html", {"request": request, "etapas": etapas, "sucesso": False})

    u = db.query(Usuario).filter(Usuario.usuario == login_cookie_validado).first()
    if not u:
        etapas.append(("LOGIN-11", False, "Sessão válida, mas o usuário não foi encontrado no banco nesta requisição. Isso indica possível troca de banco/instância/configuração."))
        return templates.TemplateResponse("login_diagnostico.html", {"request": request, "etapas": etapas, "sucesso": False})
    if int(u.ativo or 0) != 1:
        etapas.append(("LOGIN-12", False, "Sessão válida, mas o usuário chegou como inativo na nova requisição."))
        return templates.TemplateResponse("login_diagnostico.html", {"request": request, "etapas": etapas, "sucesso": False})

    etapas.append(("LOGIN-10 a LOGIN-12", True, "Usuário da sessão encontrado e ativo no banco."))
    etapas.append(("LOGIN-OK", True, "Autenticação e sessão concluídas."))
    return RedirectResponse("/painel", status_code=303)


@app.get("/esqueci-senha", response_class=HTMLResponse)
def esqueci_senha_form(request: Request, erro: str = "", sucesso: str = ""):
    return templates.TemplateResponse(
        "esqueci_senha.html",
        {"request": request, "erro": erro, "sucesso": sucesso}
    )


@app.post("/esqueci-senha")
def esqueci_senha(
    request: Request,
    cpf: str = Form(...),
    whatsapp: str = Form(...),
    db: Session = Depends(get_db)
):
    cpf_digits = normalizar_cpf(cpf)
    telefone = normalizar_whatsapp(whatsapp)

    encontrado = None
    for candidato in db.query(Usuario).filter(Usuario.ativo == 1).all():
        if normalizar_cpf(candidato.cpf or "") == cpf_digits and normalizar_whatsapp(candidato.whatsapp or "") == telefone:
            encontrado = candidato
            break

    if not encontrado or not cpf_valido(cpf_digits) or not telefone:
        return RedirectResponse(
            "/esqueci-senha?erro=Não foi possível validar o CPF e o WhatsApp informados.",
            status_code=303
        )

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    agora = datetime.now()
    for pedido in db.query(RedefinicaoSenha).filter(
        RedefinicaoSenha.usuario_id == encontrado.id,
        RedefinicaoSenha.usado_em.is_(None)
    ).all():
        pedido.usado_em = agora

    db.add(RedefinicaoSenha(
        usuario_id=encontrado.id,
        token_hash=token_hash,
        expira_em=agora + timedelta(minutes=30)
    ))
    db.commit()
    return RedirectResponse(f"/redefinir-senha/{token}", status_code=303)


@app.get("/redefinir-senha/{token}", response_class=HTMLResponse)
def redefinir_senha_form(token: str, request: Request, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    pedido = db.query(RedefinicaoSenha).filter(
        RedefinicaoSenha.token_hash == token_hash,
        RedefinicaoSenha.usado_em.is_(None)
    ).first()

    valido = bool(pedido and pedido.expira_em >= datetime.now())
    return templates.TemplateResponse(
        "redefinir_senha.html",
        {"request": request, "token": token, "valido": valido, "erro": ""}
    )


@app.post("/redefinir-senha/{token}")
def redefinir_senha(
    token: str,
    request: Request,
    nova_senha: str = Form(...),
    confirmar_senha: str = Form(...),
    db: Session = Depends(get_db)
):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    pedido = db.query(RedefinicaoSenha).filter(
        RedefinicaoSenha.token_hash == token_hash,
        RedefinicaoSenha.usado_em.is_(None)
    ).first()

    if not pedido or pedido.expira_em < datetime.now():
        return templates.TemplateResponse(
            "redefinir_senha.html",
            {"request": request, "token": token, "valido": False, "erro": "Este link expirou ou já foi utilizado."},
            status_code=400
        )

    if len(nova_senha) < 8:
        return templates.TemplateResponse(
            "redefinir_senha.html",
            {"request": request, "token": token, "valido": True, "erro": "A nova senha precisa ter pelo menos 8 caracteres."},
            status_code=400
        )

    if nova_senha != confirmar_senha:
        return templates.TemplateResponse(
            "redefinir_senha.html",
            {"request": request, "token": token, "valido": True, "erro": "As senhas não conferem."},
            status_code=400
        )

    usuario = db.get(Usuario, pedido.usuario_id)
    if not usuario:
        return templates.TemplateResponse(
            "redefinir_senha.html",
            {"request": request, "token": token, "valido": False, "erro": "Não foi possível concluir a redefinição."},
            status_code=400
        )

    usuario.senha_hash = gerar_hash_senha(nova_senha)
    pedido.usado_em = datetime.now()
    db.commit()

    return RedirectResponse(
        "/entrar?erro=Senha alterada com sucesso. Entre com a nova senha.",
        status_code=303
    )



@app.get("/sair")
def sair(request: Request, db: Session = Depends(get_db)):
    login = login_cookie(request)
    if login:
        u = db.query(Usuario).filter(Usuario.usuario == login).first()
        if u:
            u.online = 0
            db.commit()
    resposta = RedirectResponse("/", status_code=303)
    resposta.delete_cookie(COOKIE_SESSAO, path="/")
    resposta.delete_cookie(COOKIE_SESSAO_ANTIGO, path="/")
    return resposta



@app.get("/api/minha-oportunidade-atual")
def minha_oportunidade_atual(
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db)
):
    # Qualquer usuário online ajuda a processar oportunidades vencidas.
    expirar_oportunidades_sem_aceite(db)

    ind = (
        db.query(Indicacao)
        .filter(
            Indicacao.recebido_por_id == usuario.id,
            Indicacao.status == "Em atendimento"
        )
        .order_by(Indicacao.id.desc())
        .first()
    )
    if not ind:
        return {"tem": False}

    tent = (
        db.query(Tentativa)
        .filter(
            Tentativa.indicacao_id == ind.id,
            Tentativa.usuario_id == usuario.id,
            Tentativa.finalizado_em.is_(None)
        )
        .order_by(Tentativa.id.desc())
        .first()
    )

    aguardando_aceite = bool(tent and tent.resultado == "Aguardando aceite" and not tent.aceite_em)

    item = db.get(Item, ind.item_id)
    return {
        "tem": True,
        "id": ind.id,
        "categoria": item.nome if item else "Karaokê",
        "bairro": ind.local_texto or ind.zona or "Local a confirmar",
        "data": ind.data_evento.strftime("%d/%m/%Y") if ind.data_evento else "Data indefinida",
        "aguardando_aceite": aguardando_aceite,
        "sem_expiracao_automatica": True,
    }



@app.get("/painel", response_class=HTMLResponse)
def painel(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    expirar_oportunidades_sem_aceite(db)
    # Todo cliente autenticado precisa receber seu link pessoal, inclusive
    # cadastros antigos criados antes da coluna/token de indicação.
    token_indicacao = garantir_token_indicacao_usuario(db, usuario)
    abertas = db.query(Indicacao).filter(
        Indicacao.recebido_por_id == usuario.id,
        Indicacao.status == "Em atendimento"
    ).all()
    aguardando = db.query(Indicacao).filter(Indicacao.status == "Aguardando sorteio").count()
    aguardando_admin = db.query(Indicacao).filter(Indicacao.status == "Aguardando admin").count()
    itens = {i.id: i for i in db.query(Item).all()}
    oportunidade_nova = max(abertas, key=lambda x: x.id) if abertas else None
    tentativa_oportunidade = None
    if oportunidade_nova:
        tentativa_oportunidade = (
            db.query(Tentativa)
            .filter(
                Tentativa.indicacao_id == oportunidade_nova.id,
                Tentativa.usuario_id == usuario.id,
                Tentativa.finalizado_em.is_(None),
            )
            .order_by(Tentativa.id.desc())
            .first()
        )
    nome_oportunidade = None
    if oportunidade_nova:
        if getattr(oportunidade_nova, "catalogo_item_id", None):
            ci = db.get(CatalogoItem, oportunidade_nova.catalogo_item_id)
            nome_oportunidade = ci.nome if ci else None
        if not nome_oportunidade and getattr(oportunidade_nova, "categoria_id", None):
            cat = db.get(Categoria, oportunidade_nova.categoria_id)
            nome_oportunidade = cat.nome if cat else None
        if not nome_oportunidade:
            item_base = itens.get(oportunidade_nova.item_id)
            nome_oportunidade = item_base.nome if item_base else "Nova oportunidade"

    vinculo_categoria = db.query(UsuarioCategoria).filter(
        UsuarioCategoria.usuario_id == usuario.id
    ).first()
    categoria_usuario = db.get(Categoria, vinculo_categoria.categoria_id) if vinculo_categoria else None

    mensagem_sistema = None
    status_sistema = None
    detalhes_status = []

    if categoria_usuario:
        validacao = validar_usuario_regras(db, usuario, categoria_usuario.id)

        if _normalizar_texto(categoria_usuario.nome) == "karaoke":
            if usuario.krj_validado and usuario.krj_cliente_id:
                total = int(usuario.krj_jukebox_qtd or 0) + int(usuario.krj_portatil_qtd or 0) + int(usuario.krj_iphone_qtd or 0)
                if validacao["apto"]:
                    status_sistema = "apto"
                    pacote_real = validacao.get("pacote_real") or usuario.krj_atualizacao or "—"
                    minimo = validacao.get("catalogo_obrigatorio") or "—"
                    ultima = validacao.get("ultima_atualizacao")

                    mensagem_sistema = (
                        f"Você está apto para receber indicações de Karaokê. "
                        f"Seu catálogo {pacote_real} atende à regra mínima do sorteio ({minimo})."
                    )

                    if validacao.get("atualizacao_pendente") and ultima:
                        mensagem_sistema += (
                            f" Atenção: a última atualização disponível é {ultima}. "
                            "Você pode participar do sorteio, mas ainda possui atualização para fazer."
                        )
                        detalhes_status = validacao.get("equipamentos_para_atualizar") or []
                    else:
                        mensagem_sistema += " Seus equipamentos estão na última atualização disponível."
                else:
                    status_sistema = "nao_apto"
                    mensagem_sistema = " ".join(validacao["mensagens"])
                    detalhes_status = validacao.get("equipamentos_pendentes") or []
            else:
                status_sistema = "nao_apto"
                mensagem_sistema = (
                    "Seu cadastro de Karaokê ainda não foi validado. "
                    "Carregue os dados da Karaoke RJ para ficar apto a receber indicações."
                )
        elif _normalizar_texto(categoria_usuario.nome) == "fliperama":
            qtd_flip = int(usuario.krj_fliperama_qtd or 0)
            if usuario.krj_validado and usuario.krj_cliente_id and qtd_flip > 0:
                status_sistema = "apto"
                mensagem_sistema = f"Você está apto para receber indicações de Fliperama. Possui {qtd_flip} Fliperama(s) ativo(s) no Organiza."
            else:
                status_sistema = "nao_apto"
                mensagem_sistema = "Seu cadastro ainda não possui Fliperama ativo validado no Organiza. Carregue os dados do cadastro para participar dos sorteios de Fliperama."
        else:
            status_sistema = "apto"
            mensagem_sistema = f"Você está apto para receber indicações da categoria {categoria_usuario.nome}."

    if oportunidade_nova and tentativa_oportunidade and tentativa_oportunidade.aceite_em:
        etapa_usuario = "em_atendimento"
        etapa_titulo = "Em atendimento"
        etapa_descricao = "Você aceitou uma indicação e está atendendo o cliente. Finalize o atendimento para voltar a receber novas oportunidades."
    elif oportunidade_nova:
        etapa_usuario = "aguardando_decisao"
        etapa_titulo = "Nova indicação"
        etapa_descricao = "Existe uma indicação vinculada a você. Aceite para iniciar o atendimento ou repasse para liberar seu cadastro."
    elif status_sistema == "nao_apto":
        etapa_usuario = "impedido"
        etapa_titulo = "Cadastro pendente"
        etapa_descricao = "Você está livre, mas ainda não pode participar dos sorteios até regularizar o cadastro."
    else:
        etapa_usuario = "livre"
        etapa_titulo = "Livre para receber"
        etapa_descricao = "Você não possui atendimento aberto e está disponível para receber uma nova indicação."

    return templates.TemplateResponse("painel.html", {
        "request": request,
        "usuario": usuario,
        "abertas": abertas,
        "aguardando": aguardando,
        "aguardando_admin": aguardando_admin,
        "max_repasses": MAX_REPASSES_INDICACAO,
        "itens": itens, "oportunidade_nova": oportunidade_nova, "nome_oportunidade": nome_oportunidade,
        "categoria_usuario": categoria_usuario,
        "mensagem_sistema": mensagem_sistema,
        "status_sistema": status_sistema,
        "detalhes_status": detalhes_status,
        "link_indicacao": f"/indicar/{token_indicacao}",
        "tempo_aceite_segundos": TEMPO_ACEITE_SEGUNDOS,
        "etapa_usuario": etapa_usuario,
        "etapa_titulo": etapa_titulo,
        "etapa_descricao": etapa_descricao,
    })

@app.get("/api/catalogo/buscar")
def buscar_catalogo(q: str = "", db: Session = Depends(get_db)):
    termo = (q or "").strip()
    if len(termo) < 3:
        return {"resultados": [], "existe_inativo": False}

    termo_norm = _normalizar_texto(termo)
    resultados = []

    # Primeiro verifica todo o catálogo, inclusive desativado,
    # apenas para impedir que algo já existente seja solicitado como "novo".
    categorias_todas = db.query(Categoria).order_by(Categoria.nome).all()
    itens_todos = (
        db.query(CatalogoItem, Categoria)
        .join(Categoria, Categoria.id == CatalogoItem.categoria_id)
        .order_by(Categoria.nome, CatalogoItem.nome)
        .all()
    )

    existe_inativo = False

    for categoria in categorias_todas:
        cat_norm = _normalizar_texto(categoria.nome)
        if termo_norm in cat_norm and not categoria.ativo:
            existe_inativo = True

    for item, categoria in itens_todos:
        nome_norm = _normalizar_texto(item.nome)
        cat_norm = _normalizar_texto(categoria.nome)
        if termo_norm in nome_norm or termo_norm in cat_norm:
            if not item.ativo or not categoria.ativo:
                existe_inativo = True

    # Só devolve ao usuário categorias e itens ATIVOS.
    categorias_ativas = [c for c in categorias_todas if c.ativo]
    for categoria in categorias_ativas:
        cat_norm = _normalizar_texto(categoria.nome)
        if termo_norm in cat_norm:
            resultados.append({
                "tipo_resultado": "categoria",
                "id": categoria.id,
                "nome": categoria.nome,
                "categoria": "Categoria principal",
                "label": categoria.nome,
            })

    vistos = set()
    for item, categoria in itens_todos:
        if not item.ativo or not categoria.ativo:
            continue

        nome_norm = _normalizar_texto(item.nome)
        cat_norm = _normalizar_texto(categoria.nome)

        if termo_norm in nome_norm or termo_norm in cat_norm:
            chave = (item.id, categoria.id)
            if chave in vistos:
                continue
            vistos.add(chave)

            resultados.append({
                "tipo_resultado": "item",
                "id": item.id,
                "categoria_id": categoria.id,
                "nome": item.nome,
                "categoria": categoria.nome,
                "label": f"{item.nome} — {categoria.nome}",
            })

    return {
        "resultados": resultados[:15],
        "existe_inativo": existe_inativo,
    }


@app.get("/api/localidades/buscar")
def buscar_localidades(q: str):
    termo = (q or "").strip()
    if len(termo) < 3:
        return JSONResponse({"resultados": []})

    # Busca no Nominatim limitada ao Estado do Rio de Janeiro.
    # Não depende apenas de state_code, pois vários bairros do RJ retornam
    # somente "state" / códigos ISO em níveis diferentes.
    consultas = [
        f"{termo}, Rio de Janeiro, RJ, Brasil",
        f"{termo}, Estado do Rio de Janeiro, Brasil",
    ]

    dados = []
    ultimo_erro = None
    for consulta in consultas:
        params = urllib.parse.urlencode({
            "q": consulta,
            "format": "jsonv2",
            "addressdetails": 1,
            "countrycodes": "br",
            "limit": 10,
            "dedupe": 1,
        })
        try:
            req = urllib.request.Request(
                f"https://nominatim.openstreetmap.org/search?{params}",
                headers={
                    "User-Agent": "LokaFest/1.0 contato@humiat.com.br",
                    "Accept": "application/json",
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                parcial = json.loads(resp.read().decode("utf-8"))
            if parcial:
                dados.extend(parcial)
        except Exception as exc:
            ultimo_erro = exc

    if not dados and ultimo_erro:
        # Contingência: não bloqueia a indicação por indisponibilidade do geocodificador.
        # O local digitado segue como pendente de classificação administrativa.
        return {
            "resultados": [],
            "servico_indisponivel": True,
            "termo_digitado": termo,
            "fallback": {
                "nome": termo.title(),
                "municipio": "Rio de Janeiro",
                "uf": "RJ",
                "estado": "Rio de Janeiro",
                "tipo": "informado",
                "osm_id": "",
                "lat": "",
                "lon": "",
                "label": f"{termo.title()} — Rio de Janeiro/RJ"
            }
        }

    resultados = []
    vistos = set()

    for r in dados:
        a = r.get("address") or {}

        estado = (a.get("state") or "").strip()
        uf = (a.get("state_code") or "").strip().upper()

        # O Nominatim nem sempre entrega state_code para bairros.
        if not uf:
            for campo_iso in ("ISO3166-2-lvl4", "ISO3166-2-lvl6", "ISO3166-2-lvl8"):
                iso = (a.get(campo_iso) or "").strip().upper()
                if iso.endswith("-RJ"):
                    uf = "RJ"
                    break

        # Fallback pelo nome do estado.
        if not uf and _normalizar_texto(estado) in {
            "rio de janeiro",
            "estado do rio de janeiro",
        }:
            uf = "RJ"

        if uf != "RJ":
            continue

        # Para bairro/localidade, o campo 'name' do resultado é um ótimo fallback.
        localidade = (
            a.get("suburb")
            or a.get("neighbourhood")
            or a.get("quarter")
            or a.get("city_district")
            or a.get("village")
            or a.get("town")
            or r.get("name")
        )

        municipio = (
            a.get("city")
            or a.get("town")
            or a.get("municipality")
            or a.get("county")
            or "Rio de Janeiro"
        )

        # Em resultados do município do Rio, county pode vir como "Rio de Janeiro".
        # Para bairros como Ramos, preservamos o nome retornado do bairro.
        if not localidade:
            display = (r.get("display_name") or "").split(",")
            localidade = display[0].strip() if display else termo

        if not localidade:
            continue

        chave = (
            _normalizar_texto(localidade),
            _normalizar_texto(municipio),
            "RJ",
        )
        if chave in vistos:
            continue
        vistos.add(chave)

        resultados.append({
            "nome": localidade,
            "municipio": municipio,
            "uf": "RJ",
            "estado": estado or "Rio de Janeiro",
            "tipo": r.get("type") or "bairro",
            "osm_id": str(r.get("osm_id") or ""),
            "lat": str(r.get("lat") or ""),
            "lon": str(r.get("lon") or ""),
            "label": f"{localidade} — {municipio}/RJ",
        })

    # Prioriza correspondência exata/mais próxima do que foi digitado.
    termo_norm = _normalizar_texto(termo)
    resultados.sort(
        key=lambda x: (
            0 if _normalizar_texto(x["nome"]) == termo_norm else
            1 if termo_norm in _normalizar_texto(x["nome"]) else 2,
            x["nome"]
        )
    )

    return {"resultados": resultados[:8]}

@app.get("/indicar/{token}", response_class=HTMLResponse)
def indicar_publico_pessoal(token: str, request: Request, db: Session = Depends(get_db)):
    indicador = db.query(Usuario).filter(
        Usuario.indicacao_token == token.upper(),
        Usuario.ativo == 1
    ).first()
    if not indicador:
        raise HTTPException(status_code=404, detail="Link de indicação inválido")

    return templates.TemplateResponse("indicar.html", {
        "request": request,
        "usuario": None,
        "modo_publico": True,
        "indicador_publico": indicador,
        "indicador_token": indicador.indicacao_token,
    })


@app.get("/solicitar", response_class=HTMLResponse)
def solicitar_publico(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("indicar.html", {
        "request": request, "usuario": None, "modo_publico": True
    })


@app.get("/indicar", response_class=HTMLResponse)
def indicar_form(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    # O Connect pode abrir este formulário já preenchido via query string.
    # Importante: isto NÃO cria nem envia indicação automaticamente; a pessoa revisa e clica em INDICAR.
    qp = request.query_params
    tipos = [x for x in qp.getlist("tipos_servico") if x in {"karaoke", "fliperama"}]
    equipamentos = [x for x in qp.getlist("equipamentos") if x in {"portatil", "jukebox", "iphone"}]
    prefill = {
        "origem": str(qp.get("origem") or "")[:40],
        "empresa": str(qp.get("empresa") or "")[:120],
        "whatsapp": str(qp.get("whatsapp") or "")[:40],
        "data_evento": str(qp.get("data_evento") or "")[:10],
        "observacao": str(qp.get("observacao") or "")[:1000],
        "localidade_nome": str(qp.get("localidade_nome") or "")[:160],
        "municipio_nome": str(qp.get("municipio_nome") or "")[:160],
        "uf": str(qp.get("uf") or "")[:2],
        "estado_nome": str(qp.get("estado_nome") or "")[:160],
        "localidade_tipo": str(qp.get("localidade_tipo") or "")[:60],
        "tipos_servico": tipos or (["karaoke"] if qp.get("origem") == "connect" else []),
        "equipamentos": equipamentos,
    }
    return templates.TemplateResponse("indicar.html", {
        "request": request, "usuario": usuario, "modo_publico": False, "prefill": prefill
    })



def tipos_servico_indicacao(ind: Indicacao) -> list[str]:
    """Serviços exigidos pela indicação. Registros antigos equivalem a Karaokê."""
    try:
        valores = json.loads(ind.tipos_servico_json or "[]")
    except (TypeError, ValueError, json.JSONDecodeError):
        valores = []
    if not isinstance(valores, list):
        valores = []
    selecionados = []
    for valor in valores:
        chave = _normalizar_texto(str(valor)).replace(" ", "")
        if chave in {"karaoke", "fliperama"} and chave not in selecionados:
            selecionados.append(chave)
    return selecionados or ["karaoke"]


def tipos_servico_indicacao_texto(ind: Indicacao) -> str:
    nomes = {"karaoke": "Karaokê", "fliperama": "Fliperama"}
    return " + ".join(nomes.get(x, x.title()) for x in tipos_servico_indicacao(ind))


def equipamentos_indicacao(ind: Indicacao) -> list[str]:
    """Tipos de Karaokê aceitos. Registros antigos aceitam os três tipos."""
    try:
        valores = json.loads(ind.equipamentos_json or "[]")
    except (TypeError, ValueError, json.JSONDecodeError):
        valores = []
    if not isinstance(valores, list):
        valores = []
    selecionados = []
    for valor in valores:
        chave = _normalizar_texto(str(valor)).replace(" ", "")
        mapa = {"portatil": "portatil", "jukebox": "jukebox", "iphone": "iphone"}
        if chave in mapa and mapa[chave] not in selecionados:
            selecionados.append(mapa[chave])
    return selecionados or list(EQUIPAMENTOS_INDICACAO.keys())


def equipamentos_indicacao_texto(ind: Indicacao) -> str:
    servicos = tipos_servico_indicacao(ind)
    partes = []
    if "karaoke" in servicos:
        partes.append(", ".join(EQUIPAMENTOS_INDICACAO.get(x, x.title()) for x in equipamentos_indicacao(ind)))
    if "fliperama" in servicos:
        partes.append("Fliperama")
    return " + ".join(partes) or "—"


templates.env.globals["equipamentos_indicacao_texto"] = equipamentos_indicacao_texto
templates.env.globals["tipos_servico_indicacao_texto"] = tipos_servico_indicacao_texto


def _tipo_equipamento_detalhe(eq: dict) -> str | None:
    texto = _normalizar_texto(" ".join(str((eq or {}).get(k) or "") for k in ("tipo", "tipo_original", "tipo_origem", "modelo", "identificacao", "descricao", "equipamento", "nome")))
    if "fliperama" in texto or "arcade" in texto:
        return "fliperama"
    if "iphone" in texto or "i phone" in texto:
        return "iphone"
    if "jukebox" in texto or "juke box" in texto or "juke" in texto:
        return "jukebox"
    if "portatil" in texto or "maleta" in texto:
        return "portatil"
    return None


def usuario_atende_equipamento_indicacao(db: Session, usuario: Usuario, ind: Indicacao, categoria_id: int) -> tuple[bool, str]:
    """Valida somente a parte Karaokê da indicação."""
    selecionados = equipamentos_indicacao(ind)
    quantidades = {
        "portatil": int(usuario.krj_portatil_qtd or 0),
        "jukebox": int(usuario.krj_jukebox_qtd or 0),
        "iphone": int(usuario.krj_iphone_qtd or 0),
    }
    possui = [tipo for tipo in selecionados if quantidades.get(tipo, 0) > 0]
    if not possui:
        nomes = ", ".join(EQUIPAMENTOS_INDICACAO[x] for x in selecionados)
        return False, f"Não possui nenhum equipamento de Karaokê solicitado ({nomes})"

    regra = _regra_catalogo_ativa(db, categoria_id)
    obrigatorio = (regra.valor_obrigatorio or "").strip() if regra else ""
    if not obrigatorio:
        return True, "Possui Karaokê compatível"

    try:
        detalhes = json.loads(usuario.krj_equipamentos_json or "[]")
        if not isinstance(detalhes, list):
            detalhes = []
    except Exception:
        detalhes = []

    reconhecidos = []
    for eq in detalhes:
        tipo = _tipo_equipamento_detalhe(eq or {})
        if tipo in possui:
            reconhecidos.append((tipo, eq or {}))

    if reconhecidos:
        for tipo, eq in reconhecidos:
            pacote = str(eq.get("pacote") or "").strip()
            if _pacote_atende_obrigatorio(pacote, obrigatorio):
                return True, f"Possui {EQUIPAMENTOS_INDICACAO[tipo]} apto ao catálogo {obrigatorio}"
        nomes = ", ".join(EQUIPAMENTOS_INDICACAO[x] for x in possui)
        return False, f"Possui {nomes}, mas nenhum deles atende ao catálogo obrigatório {obrigatorio}"

    validacao = validar_usuario_regras(db, usuario, categoria_id)
    if validacao.get("apto"):
        nomes = ", ".join(EQUIPAMENTOS_INDICACAO[x] for x in possui)
        return True, f"Possui equipamento compatível ({nomes})"
    return False, validacao.get("mensagem") or (validacao.get("mensagens") or ["Equipamento não atende à regra vigente"])[0]


def usuario_atende_fliperama(usuario: Usuario) -> tuple[bool, str]:
    qtd = int(usuario.krj_fliperama_qtd or 0)
    if qtd <= 0:
        return False, "Não possui Fliperama ativo no Organiza"
    return True, f"Possui {qtd} Fliperama(s) ativo(s)"


def capacidades_servico_usuario(usuario: Usuario) -> dict[str, int]:
    return {
        "karaoke": max(0, int(usuario.krj_jukebox_qtd or 0) + int(usuario.krj_portatil_qtd or 0) + int(usuario.krj_iphone_qtd or 0)),
        "fliperama": max(0, int(usuario.krj_fliperama_qtd or 0)),
    }


def consumos_servico_na_data(db: Session, usuario_id: int, data_evento, ignorar_indicacao_id: int | None = None) -> dict[str, int]:
    consumos = {"karaoke": 0, "fliperama": 0}
    if not data_evento:
        return consumos
    consulta = db.query(Indicacao).filter(
        Indicacao.recebido_por_id == usuario_id,
        Indicacao.data_evento == data_evento,
        Indicacao.status == "Sucesso",
    )
    if ignorar_indicacao_id:
        consulta = consulta.filter(Indicacao.id != ignorar_indicacao_id)
    for existente in consulta.all():
        for servico in tipos_servico_indicacao(existente):
            if servico in consumos:
                consumos[servico] += 1
    return consumos


def usuario_tem_capacidade_na_data(db: Session, usuario: Usuario, ind: Indicacao) -> tuple[bool, str]:
    """Verifica capacidade separadamente por Karaokê e Fliperama."""
    if not ind.data_evento:
        return True, "Data do evento ainda não definida"
    capacidades = capacidades_servico_usuario(usuario)
    consumos = consumos_servico_na_data(db, usuario.id, ind.data_evento, ind.id)
    indisponiveis = []
    saldos = []
    for servico in tipos_servico_indicacao(ind):
        capacidade = int(capacidades.get(servico, 0))
        usado = int(consumos.get(servico, 0))
        nome = "Karaokê" if servico == "karaoke" else "Fliperama"
        if capacidade <= usado:
            indisponiveis.append(f"{nome}: {usado}/{capacidade} já comprometido(s)")
        else:
            saldos.append(f"{nome}: {capacidade - usado} disponível(is)")
    if indisponiveis:
        data_txt = ind.data_evento.strftime("%d/%m/%Y")
        return False, f"Sem capacidade em {data_txt}. " + " · ".join(indisponiveis)
    return True, " · ".join(saldos) if saldos else "Capacidade disponível"


def executar_sorteio_automatico(db: Session, ind: Indicacao):
    """Distribui a oportunidade e grava a justificativa completa da escolha."""
    if not ind or ind.status != "Aguardando sorteio":
        return None

    servicos_exigidos = tipos_servico_indicacao(ind)
    exige_karaoke = "karaoke" in servicos_exigidos
    exige_fliperama = "fliperama" in servicos_exigidos

    karaoke_cat = next(
        (c for c in db.query(Categoria).filter(Categoria.ativo == 1).all()
         if _normalizar_texto(c.nome) == "karaoke"),
        None
    )
    if exige_karaoke and not karaoke_cat:
        return None

    vinculados_karaoke = set()
    if karaoke_cat:
        vinculados_karaoke = {x.usuario_id for x in db.query(UsuarioCategoria).filter(
            UsuarioCategoria.categoria_id == karaoke_cat.id).all()}
    rodada_atual = max(1, int(ind.sorteio_rodada or 1))
    tentativas_existentes = db.query(Tentativa).filter(
        Tentativa.indicacao_id == ind.id,
        Tentativa.rodada == rodada_atual,
    ).all()
    ja_tentaram = {x.usuario_id for x in tentativas_existentes}
    # A auditoria registra cada tentativa de distribuição dentro da rodada atual.
    rodada = rodada_atual

    zonas_ativas_normalizadas = {
        _normalizar_texto(z.nome) for z in db.query(Zona).filter(Zona.ativo == 1).all()
        if (z.nome or "").strip()
    }

    def zonas_bloqueadas_usuario(u: Usuario) -> set[str]:
        # Sem configuração anterior, a zona principal sempre começa como ATENDE
        # e as demais começam como NÃO ATENDE. Mesmo em cadastros gravados
        # incorretamente, a zona principal nunca fica bloqueada.
        zona_principal = _normalizar_texto(u.zona or "")
        try:
            valores = json.loads(u.zonas_bloqueadas_json or "[]")
        except (TypeError, ValueError, json.JSONDecodeError):
            valores = []
        if not isinstance(valores, list) or "__CONFIGURADO__" not in valores:
            bloqueadas = set(zonas_ativas_normalizadas)
        else:
            bloqueadas = {
                _normalizar_texto(str(z)) for z in valores
                if str(z).strip() and str(z) != "__CONFIGURADO__"
            }
        bloqueadas.discard(zona_principal)
        return bloqueadas

    def avaliar(u: Usuario):
        if u.is_admin:
            return False, "Administrador não participa do sorteio"
        if not u.ativo:
            return False, "Cadastro inativo"
        if not u.aprovado:
            return False, "Cadastro ainda não aprovado"
        if exige_karaoke and u.id not in vinculados_karaoke:
            return False, "Não está vinculado à categoria Karaokê"
        if u.id in ja_tentaram:
            return False, "Já recebeu esta indicação em uma rodada anterior"
        zonas_bloqueadas = zonas_bloqueadas_usuario(u)
        zona_indicacao = _normalizar_texto(ind.zona or "")
        if zona_indicacao in zonas_bloqueadas:
            return False, f"Cadastro configurado para não receber indicações de {ind.zona}"
        # Compatibilidade com cadastros salvos na versão anterior.
        if not zonas_bloqueadas and int(u.somente_zona_propria or 0) == 1 and _normalizar_texto(u.zona or "") != zona_indicacao:
            return False, f"Cadastro antigo configurado para receber somente indicações da própria zona ({u.zona})"
        if ind.indicado_por_id and u.id == ind.indicado_por_id:
            return False, "Quem indicou não pode receber a própria indicação"
        if usuario_tem_aberta_conflitante(db, u.id, ind.data_evento):
            if ind.data_evento:
                return False, "Já possui indicação em atendimento nesta data ou com data indefinida"
            return False, "Já possui outra indicação em atendimento"
        tem_capacidade, motivo_capacidade = usuario_tem_capacidade_na_data(db, u, ind)
        if not tem_capacidade:
            return False, motivo_capacidade
        if not u.krj_validado or not u.krj_cliente_id:
            return False, "Cadastro do Organiza ainda não validado"

        motivos_ok = []
        if exige_karaoke:
            validacao = validar_usuario_regras(db, u, karaoke_cat.id)
            if not bool(validacao.get("apto")):
                mensagens = validacao.get("mensagens") or []
                return False, mensagens[0] if mensagens else "Não atende às regras de Karaokê"
            atende_equipamento, motivo_equipamento = usuario_atende_equipamento_indicacao(db, u, ind, karaoke_cat.id)
            if not atende_equipamento:
                return False, motivo_equipamento
            motivos_ok.append(motivo_equipamento)

        if exige_fliperama:
            atende_flip, motivo_flip = usuario_atende_fliperama(u)
            if not atende_flip:
                return False, motivo_flip
            motivos_ok.append(motivo_flip)

        return True, " · ".join(motivos_ok) or "Atende aos serviços solicitados"

    todos_usuarios = db.query(Usuario).all()
    avaliacoes = {u.id: avaliar(u) for u in todos_usuarios}
    todos = [u for u in todos_usuarios if avaliacoes[u.id][0]]

    zona_alvo = _normalizar_texto(ind.zona or "")
    # Primeiro tenta usuários cuja zona principal é a própria zona da indicação.
    # Quando todos eles já foram chamados ou estão indisponíveis, usa os usuários
    # que marcaram essa zona como atendimento secundário.
    candidatos_principais = [u for u in todos if _normalizar_texto(u.zona or "") == zona_alvo]
    candidatos_secundarios = [u for u in todos if _normalizar_texto(u.zona or "") != zona_alvo]
    candidatos = candidatos_principais or candidatos_secundarios
    zona_escolhida = zona_alvo if candidatos_principais else "atendimento secundário"
    ordem = [zona_alvo, "atendimento secundário"]

    escolhido = None
    maior_credito = 0
    pool = []
    if candidatos:
        maior_credito = max(int(u.prioridade_creditos or 0) for u in candidatos)
        pool = ([u for u in candidatos if int(u.prioridade_creditos or 0) == maior_credito]
                if maior_credito > 0 else candidatos)
        escolhido = secrets.choice(pool)

    # Registra todos os participantes e o motivo da inclusão/exclusão nesta rodada.
    for u in todos_usuarios:
        apto, motivo = avaliacoes[u.id]
        zona_u = _normalizar_texto(u.zona or "")
        ordem_zona = ordem.index(zona_u) + 1 if zona_u in ordem else None
        selecionado = bool(escolhido and u.id == escolhido.id)
        if apto:
            if not candidatos:
                motivo = "Apto, mas nenhuma zona elegível foi encontrada"
            elif candidatos_principais and zona_u != zona_alvo:
                motivo = f"Apto como atendimento secundário, mas ainda havia participante com {ind.zona} como zona principal"
            elif selecionado:
                motivo = "Selecionado nesta rodada"
            elif maior_credito > 0 and int(u.prioridade_creditos or 0) < maior_credito:
                motivo = f"Apto na zona escolhida, mas outro participante tinha maior prioridade ({maior_credito})"
            elif u in pool:
                motivo = "Apto na mesma prioridade; não foi escolhido no desempate aleatório"
            else:
                motivo = "Apto na zona escolhida, mas ficou fora do grupo de maior prioridade"
        db.add(SorteioAuditoria(
            indicacao_id=ind.id, rodada=rodada, usuario_id=u.id,
            zona_indicacao=ind.zona, zona_usuario=u.zona, ordem_zona=ordem_zona,
            elegivel=1 if apto else 0, creditos_prioridade=int(u.prioridade_creditos or 0),
            selecionado=1 if selecionado else 0, motivo=motivo
        ))

    if not escolhido:
        # Ninguém atendeu simultaneamente às regras de região + equipamento + disponibilidade.
        # Encaminha o caso para a fila administrativa, sem forçar um participante incompatível.
        ind.status = "Aguardando admin"
        ind.recebido_por_id = None
        ind.pedido_token = None
        db.flush()
        return None

    ind.pedido_token = secrets.token_urlsafe(24)
    ind.whatsapp_encaminhado_em = None
    ind.recebido_por_id = escolhido.id
    ind.status = "Em atendimento"
    db.add(Tentativa(
        indicacao_id=ind.id, usuario_id=escolhido.id,
        resultado="Aguardando aceite", rodada=rodada_atual
    ))
    if int(escolhido.prioridade_creditos or 0) > 0:
        escolhido.prioridade_creditos -= 1
    db.flush()
    return escolhido


def expirar_oportunidades_sem_aceite(db: Session):
    """Não expira automaticamente: quem não responde permanece bloqueado até agir."""
    return 0


def reprocessar_sorteios_pendentes(db: Session):
    """Tenta distribuir oportunidades ainda aguardando, sem ação do administrador."""
    distribuidas = 0
    pendentes = db.query(Indicacao).filter(
        Indicacao.status == "Aguardando sorteio"
    ).order_by(Indicacao.criado_em).all()
    for ind in pendentes:
        if executar_sorteio_automatico(db, ind):
            distribuidas += 1
    if distribuidas:
        db.commit()
    return distribuidas


def _numero_whatsapp(valor: str) -> str:
    numero = re.sub(r"\D", "", valor or "")
    if numero and not numero.startswith("55"):
        numero = "55" + numero
    return numero


def _url_whatsapp(numero: str, mensagem: str) -> str:
    return "https://wa.me/" + _numero_whatsapp(numero) + "?text=" + urllib.parse.quote(mensagem)


def _link_oportunidade(request: Request, ind: Indicacao) -> str:
    return str(request.base_url).rstrip("/") + f"/oportunidade/{ind.pedido_token}"


def _mensagem_nova_oportunidade(request: Request, ind: Indicacao, usuario: Usuario, item: Item | None) -> str:
    produto = item.nome if item else "Karaokê"
    local = ind.local_texto or ind.zona or "Local a confirmar"
    data_txt = ind.data_evento.strftime("%d/%m/%Y") if ind.data_evento else "Data a definir"
    primeiro_nome = (usuario.nome or "Participante").strip().split()[0]
    observacao = (ind.observacao or "").strip()
    linha_observacao = f"*Observação:* {observacao}\n" if observacao else ""
    return (
        f"Olá, *{primeiro_nome}*! Você foi sorteado(a) para uma nova indicação no *LokaFest*.\n\n"
        f"*Produto:* {produto}\n"
        f"*Equipamento:* {equipamentos_indicacao_texto(ind)}\n"
        f"*Data:* {data_txt}\n"
        f"*Local:* {local}\n"
        f"{linha_observacao}\n"
        "Abra o link para escolher *ACEITAR* ou *REPASSAR*.\n\n"
        f"{_link_oportunidade(request, ind)}\n\n"
        "Enquanto você não responder, ficará impossibilitado(a) de receber novas indicações."
    )


def _tentativa_atual(db: Session, ind: Indicacao) -> Tentativa | None:
    return (db.query(Tentativa).filter(
        Tentativa.indicacao_id == ind.id,
        Tentativa.usuario_id == ind.recebido_por_id,
        Tentativa.finalizado_em.is_(None)
    ).order_by(Tentativa.id.desc()).first())


async def _salvar_solicitacao_multi(request: Request, db: Session, usuario: Usuario | None):
    form = await request.form()

    indicador_efetivo = usuario
    if not indicador_efetivo:
        token_indicador = (form.get("indicador_token") or "").strip().upper()
        if token_indicador:
            indicador_efetivo = db.query(Usuario).filter(
                Usuario.indicacao_token == token_indicador,
                Usuario.ativo == 1
            ).first()

    whatsapp = normalizar_whatsapp(form.get("whatsapp") or "")
    if len(whatsapp) < 10:
        return RedirectResponse(
            ("/indicar" if usuario else "/solicitar") + "?erro=Informe um WhatsApp válido",
            status_code=303
        )

    data = None
    data_evento = (form.get("data_evento") or "").strip()
    if data_evento:
        try:
            data = date.fromisoformat(data_evento)
        except ValueError:
            return RedirectResponse(
                ("/indicar" if usuario else "/solicitar") + "?erro=Data inválida",
                status_code=303
            )

    localidade = obter_ou_criar_localidade(
        db,
        form.get("localidade_nome") or "",
        form.get("municipio_nome") or "",
        form.get("uf") or "",
        form.get("estado_nome") or "",
        form.get("localidade_tipo") or "bairro",
        form.get("osm_id") or "",
        form.get("lat") or "",
        form.get("lon") or "",
    )
    if not localidade:
        return RedirectResponse(
            ("/indicar" if usuario else "/solicitar") + "?erro=Busque e selecione um bairro/local válido do RJ",
            status_code=303
        )

    area = area_da_localidade(db, localidade.id)
    if not area:
        area = preclassificar_localidade(db, localidade)

    # Tipo da oportunidade: Karaokê é o padrão. Fliperama pode ser marcado
    # sozinho ou junto; quando os dois são marcados, o sorteado precisa ter ambos.
    tipos_servico = []
    for valor in form.getlist("tipos_servico"):
        chave = _normalizar_texto(str(valor)).replace(" ", "")
        if chave in {"karaoke", "fliperama"} and chave not in tipos_servico:
            tipos_servico.append(chave)
    if not tipos_servico:
        tipos_servico = ["karaoke"]

    if set(tipos_servico) == {"karaoke", "fliperama"}:
        item_nome = "Karaokê + Fliperama"
    elif "fliperama" in tipos_servico:
        item_nome = "Fliperama"
    else:
        item_nome = "Karaokê"

    item = next(
        (x for x in db.query(Item).all() if _normalizar_texto(x.nome) == _normalizar_texto(item_nome)),
        None
    )
    if not item:
        item = Item(nome=item_nome, tipo="Serviço", ativo=1)
        db.add(item)
        db.flush()

    status = "Aguardando sorteio" if area else "Aguardando classificação"
    zona_indicacao = area.nome if area else "Aguardando classificação"

    equipamentos_selecionados = []
    for valor in form.getlist("equipamentos"):
        chave = _normalizar_texto(str(valor)).replace(" ", "")
        if chave in EQUIPAMENTOS_INDICACAO and chave not in equipamentos_selecionados:
            equipamentos_selecionados.append(chave)
    if "karaoke" in tipos_servico and not equipamentos_selecionados:
        destino = "/indicar" if usuario else (
            f"/indicar/{indicador_efetivo.indicacao_token}"
            if indicador_efetivo and indicador_efetivo.indicacao_token
            else "/solicitar"
        )
        return RedirectResponse(
            destino + "?erro=Para Karaokê, selecione pelo menos um tipo de equipamento",
            status_code=303
        )
    observacao = (form.get("observacao") or "").strip()[:1000] or None

    duplicada = existe_indicacao_aberta_mesma_categoria(db, whatsapp, item.id)
    if duplicada:
        destino = "/indicar" if usuario else (
            f"/indicar/{indicador_efetivo.indicacao_token}"
            if indicador_efetivo and indicador_efetivo.indicacao_token
            else "/"
        )
        return RedirectResponse(
            destino + f"?erro=Este cliente já possui uma indicação aberta para {quote_plus(item_nome)}. Nenhuma nova oportunidade foi criada e nenhum crédito foi gerado.",
            status_code=303
        )

    nova_indicacao = Indicacao(
        item_id=item.id,
        data_evento=data,
        zona=zona_indicacao,
        area_id=area.id if area else None,
        localidade_id=localidade.id,
        local_texto=f"{localidade.nome} — {form.get('municipio_nome')}/{(form.get('uf') or '').upper()}",
        whatsapp=whatsapp,
        indicado_por_id=indicador_efetivo.id if indicador_efetivo else None,
        status=status,
        observacao=observacao,
        equipamentos_json=json.dumps(equipamentos_selecionados, ensure_ascii=False),
        tipos_servico_json=json.dumps(tipos_servico, ensure_ascii=False),
    )
    db.add(nova_indicacao)
    db.flush()

    if indicador_efetivo:
        indicador_efetivo.prioridade_creditos = int(indicador_efetivo.prioridade_creditos or 0) + 1

    if nova_indicacao.status == "Aguardando sorteio":
        executar_sorteio_automatico(db, nova_indicacao)

    db.commit()

    # O WhatsApp só é aberto quando existe um indicador responsável pelo link/formulário
    # e o telefone do sorteado é diferente do telefone informado na indicação. Assim,
    # nunca abrimos uma conversa do cliente consigo mesmo.
    pode_encaminhar = bool(usuario or indicador_efetivo)
    if pode_encaminhar and nova_indicacao.recebido_por_id and nova_indicacao.pedido_token:
        sorteado = db.get(Usuario, nova_indicacao.recebido_por_id)
        mesmo_numero_da_indicacao = bool(
            sorteado and
            normalizar_whatsapp(sorteado.whatsapp) == normalizar_whatsapp(nova_indicacao.whatsapp)
        )
        if sorteado and whatsapp_valido(sorteado.whatsapp) and not mesmo_numero_da_indicacao:
            nova_indicacao.whatsapp_encaminhado_em = datetime.now()
            db.commit()
            mensagem = _mensagem_nova_oportunidade(request, nova_indicacao, sorteado, item)
            return RedirectResponse(_url_whatsapp(sorteado.whatsapp, mensagem), status_code=303)

    if usuario:
        msg = f"Indicação de {item_nome} cadastrada"
        if not area:
            msg += "; local aguardando classificação"
        elif nova_indicacao.recebido_por_id:
            msg += "; participante sorteado, mas o WhatsApp não foi aberto porque os números são iguais"
        elif nova_indicacao.status == "Aguardando admin":
            msg += "; nenhum colaborador atende às regras de região e equipamento; encaminhada ao administrador"
        else:
            msg += "; aguardando participante disponível"
        return RedirectResponse(f"/painel?ok={quote_plus(msg)}", status_code=303)

    return RedirectResponse("/solicitar?ok=1", status_code=303)


@app.post("/solicitar")
async def solicitar_publico_salvar(request: Request, db: Session = Depends(get_db)):
    return await _salvar_solicitacao_multi(request, db, None)


@app.post("/indicar")
async def indicar_salvar(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    return await _salvar_solicitacao_multi(request, db, usuario)


@app.get("/minhas", response_class=HTMLResponse)
def minhas(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    indicacoes = db.query(Indicacao).filter(Indicacao.recebido_por_id == usuario.id).order_by(Indicacao.criado_em.desc()).all()
    itens = {i.id: i for i in db.query(Item).all()}
    return templates.TemplateResponse("minhas.html", {"request": request, "usuario": usuario, "indicacoes": indicacoes, "itens": itens})




def _usuario_da_oportunidade(token: str, request: Request, db: Session) -> tuple[Indicacao, Usuario]:
    """Exige login e garante que somente o responsável atual acesse a indicação."""
    ind = db.query(Indicacao).filter(Indicacao.pedido_token == token).first()
    if not ind or not ind.recebido_por_id:
        raise HTTPException(status_code=404, detail="Oportunidade indisponível")

    login = login_cookie(request)
    if not login:
        destino = urllib.parse.quote(f"/oportunidade/{token}", safe="/")
        raise HTTPException(status_code=303, headers={"Location": f"/entrar?next={destino}"})

    usuario = db.query(Usuario).filter(Usuario.usuario == login, Usuario.ativo == 1).first()
    if not usuario or usuario.id != ind.recebido_por_id:
        raise HTTPException(
            status_code=403,
            detail="Esta indicação não está mais disponível para você."
        )
    return ind, usuario


@app.get("/oportunidade/{token}", response_class=HTMLResponse)
def oportunidade_publica(token: str, request: Request, db: Session = Depends(get_db)):
    try:
        ind, responsavel = _usuario_da_oportunidade(token, request, db)
    except HTTPException as exc:
        # Links antigos deixam de pertencer ao usuário após aceitar, repassar ou
        # quando o administrador movimenta a indicação. Em vez de exibir 404/403,
        # volta ao painel mostrando claramente que ele já está liberado.
        if exc.status_code in {403, 404} and login_cookie(request):
            mensagem = quote_plus(
                "Esta indicação não está mais com você. Consulte seu estágio atual abaixo."
            )
            return RedirectResponse(f"/painel?ok={mensagem}", status_code=303)
        raise
    item = db.get(Item, ind.item_id)
    tent = _tentativa_atual(db, ind)
    aceitou = bool(tent and tent.aceite_em)
    encerrada = ind.status not in {"Em atendimento"}
    return templates.TemplateResponse("oportunidade.html", {
        "request": request, "ind": ind, "responsavel": responsavel, "item": item,
        "tent": tent, "aceitou": aceitou, "encerrada": encerrada,
    })


@app.post("/oportunidade/{token}/aceitar")
def oportunidade_aceitar(token: str, request: Request, db: Session = Depends(get_db)):
    ind, responsavel = _usuario_da_oportunidade(token, request, db)
    if ind.status != "Em atendimento":
        raise HTTPException(status_code=404, detail="Oportunidade indisponível")
    tent = _tentativa_atual(db, ind)
    if not tent:
        raise HTTPException(status_code=404, detail="Tentativa não encontrada")
    tem_capacidade, motivo_capacidade = usuario_tem_capacidade_na_data(db, responsavel, ind)
    if not tem_capacidade:
        tent.resultado = "Sem equipamento disponível na data"
        tent.finalizado_em = datetime.now()
        ind.recebido_por_id = None
        ind.pedido_token = None
        ind.status = "Aguardando admin"
        db.commit()
        return RedirectResponse(
            f"/painel?erro={urllib.parse.quote(motivo_capacidade)}. A indicação foi enviada ao administrador.",
            status_code=303,
        )
    if not tent.aceite_em:
        tent.aceite_em = datetime.now()
        tent.resultado = "Em atendimento"
    db.commit()
    mensagem = (
        "*LOKAFEST — ATENDIMENTO EM ANDAMENTO*\n\n"
        "Enquanto você não finalizar este atendimento, ficará impossibilitado(a) de receber novas indicações.\n\n"
        "Use este link para acompanhar e concluir:\n"
        f"{_link_oportunidade(request, ind)}"
    )
    return RedirectResponse(_url_whatsapp(responsavel.whatsapp, mensagem), status_code=303)


@app.get("/oportunidade/{token}/cliente")
def oportunidade_chamar_cliente(token: str, request: Request, db: Session = Depends(get_db)):
    ind, usuario = _usuario_da_oportunidade(token, request, db)
    if ind.status != "Em atendimento":
        raise HTTPException(status_code=404, detail="Oportunidade indisponível")
    tent = _tentativa_atual(db, ind)
    if not tent or not tent.aceite_em:
        raise HTTPException(status_code=403, detail="Aceite a oportunidade antes de acessar o cliente")
    item = db.get(Item, ind.item_id)
    produto = item.nome if item else "Karaokê"
    local = ind.local_texto or ind.zona or "local a confirmar"
    data_txt = ind.data_evento.strftime("%d/%m/%Y") if ind.data_evento else "Data indefinida"
    primeiro_nome = (usuario.nome or "Atendente").strip().split()[0]
    mensagem = (
        "*LOKAFEST*\n*Sua festa começa aqui!*\n\n"
        f"Olá! Meu nome é *{primeiro_nome}*.\n\n"
        "Recebi sua solicitação através do *LokaFest* e vi que você está procurando:\n\n"
        f"*Produto:* {produto}\n*Equipamento:* {equipamentos_indicacao_texto(ind)}\n*Data:* {data_txt}\n*Local:* {local}\n\n"
        "Vou te atender e apresentar as melhores opções para a sua festa.\n\n"
        "*Posso te mostrar as opções disponíveis?*\n\n"
        "--------------------\n*Indicação LokaFest*\n"
        "_Você imagina a festa. O LokaFest faz acontecer._\nwww.lokafest.com.br"
    )
    return RedirectResponse(_url_whatsapp(ind.whatsapp, mensagem), status_code=302)


@app.post("/oportunidade/{token}/repassar")
def oportunidade_repassar(token: str, request: Request, db: Session = Depends(get_db)):
    ind, _usuario = _usuario_da_oportunidade(token, request, db)
    if ind.status != "Em atendimento":
        raise HTTPException(status_code=404, detail="Oportunidade indisponível")
    tent = _tentativa_atual(db, ind)
    if tent:
        tent.resultado = "Repassou"
        tent.finalizado_em = datetime.now()
    # Guarde os identificadores antes de qualquer flush. Se o banco rejeitar
    # uma alteração, os objetos ORM ficam expirados até o rollback.
    indicacao_id = ind.id
    usuario_id = _usuario.id
    ind.recebido_por_id = None
    ind.status = "Aguardando sorteio"
    ind.pedido_token = None
    try:
        db.flush()
        proximo = executar_sorteio_automatico(db, ind)
        db.commit()
    except Exception as exc:
        # O repasse nunca pode manter o participante preso por causa de erro técnico
        # ou de alguma regra de distribuição. Recarrega a indicação após o rollback,
        # encerra a tentativa atual e envia o caso para decisão administrativa.
        db.rollback()
        print(f"ERRO AO REPASSAR INDICAÇÃO {indicacao_id}: {type(exc).__name__}: {exc}", flush=True)
        try:
            ind_erro = db.get(Indicacao, indicacao_id)
            if ind_erro:
                tentativa_erro = db.query(Tentativa).filter(
                    Tentativa.indicacao_id == indicacao_id,
                    Tentativa.usuario_id == usuario_id,
                    Tentativa.finalizado_em.is_(None),
                ).order_by(Tentativa.id.desc()).first()
                if tentativa_erro:
                    tentativa_erro.resultado = "Repassou p/ admin"
                    tentativa_erro.finalizado_em = datetime.now()
                ind_erro.recebido_por_id = None
                ind_erro.pedido_token = None
                ind_erro.status = "Aguardando admin"
                db.commit()
        except Exception as erro_fila_admin:
            db.rollback()
            print(
                f"ERRO AO ENVIAR INDICAÇÃO {indicacao_id} PARA O ADMIN: "
                f"{type(erro_fila_admin).__name__}: {erro_fila_admin}",
                flush=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Não foi possível concluir o repasse. O administrador deve liberar esta indicação.",
            )
        return RedirectResponse(
            "/painel?ok=Você foi liberado. A indicação foi enviada ao administrador para decisão.",
            status_code=303,
        )
    if proximo and ind.pedido_token and whatsapp_valido(proximo.whatsapp):
        item = db.get(Item, ind.item_id)
        mensagem = _mensagem_nova_oportunidade(request, ind, proximo, item)
        return RedirectResponse(_url_whatsapp(proximo.whatsapp, mensagem), status_code=303)
    return RedirectResponse(
        "/painel?ok=" + quote_plus(
            "Repasse concluído. Você está livre. Como não havia outro participante disponível, nenhum WhatsApp foi aberto e a indicação foi enviada ao administrador."
        ),
        status_code=303,
    )


@app.post("/oportunidade/{token}/finalizar")
def oportunidade_finalizar(token: str, request: Request, acao: str = Form(...), motivo: str = Form(""), db: Session = Depends(get_db)):
    ind, _usuario = _usuario_da_oportunidade(token, request, db)
    if ind.status != "Em atendimento":
        raise HTTPException(status_code=404, detail="Oportunidade indisponível")
    tent = _tentativa_atual(db, ind)
    if not tent or not tent.aceite_em:
        raise HTTPException(status_code=403, detail="A oportunidade ainda não foi aceita")
    if acao == "fechei":
        tem_capacidade, motivo_capacidade = usuario_tem_capacidade_na_data(db, _usuario, ind)
        if not tem_capacidade:
            ind.recebido_por_id = None
            ind.pedido_token = None
            ind.status = "Aguardando admin"
            tent.resultado = "Sem equipamento disponível na data"
            tent.finalizado_em = datetime.now()
            db.commit()
            return RedirectResponse(
                f"/painel?erro={urllib.parse.quote(motivo_capacidade)}. A indicação foi enviada ao administrador.",
                status_code=303,
            )
        tent.resultado = "Fechou"
        ind.status = "Sucesso"
    elif acao == "cliente_nao_deseja":
        motivo = (motivo or "").strip()
        if not motivo:
            return RedirectResponse(f"/oportunidade/{token}?erro=Informe o motivo", status_code=303)
        tent.resultado = "Cliente não deseja: " + motivo[:180]
        ind.status = "Cliente não deseja"
    else:
        raise HTTPException(status_code=400, detail="Ação inválida")
    agora = datetime.now()
    tent.finalizado_em = agora
    ind.encerrado_em = agora
    db.commit()
    return RedirectResponse(f"/oportunidade/{token}?ok=Atendimento finalizado com sucesso", status_code=303)



@app.get("/admin/itens-pendentes", response_class=HTMLResponse)
def itens_pendentes(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    indicacoes = (
        db.query(Indicacao)
        .filter(Indicacao.status == "Aguardando item")
        .order_by(Indicacao.criado_em)
        .all()
    )
    categorias = db.query(Categoria).filter(Categoria.ativo == 1).order_by(Categoria.nome).all()
    catalogo_itens = db.query(CatalogoItem).filter(CatalogoItem.ativo == 1).order_by(CatalogoItem.nome).all()
    return templates.TemplateResponse("itens_pendentes.html", {
        "request": request,
        "usuario": usuario,
        "indicacoes": indicacoes,
        "categorias": categorias,
        "catalogo_itens": catalogo_itens,
    })


@app.post("/admin/indicacoes/{indicacao_id}/vincular-item")
def vincular_item_pendente(
    indicacao_id: int,
    catalogo_item_id: int = Form(0),
    categoria_id: int = Form(0),
    novo_item: str = Form(""),
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db)
):
    exigir_admin(usuario)
    ind = db.get(Indicacao, indicacao_id)
    if not ind or ind.status != "Aguardando item":
        return RedirectResponse("/admin/itens-pendentes?erro=Solicitação indisponível", status_code=303)

    catalogo_item = db.get(CatalogoItem, catalogo_item_id) if catalogo_item_id else None

    if not catalogo_item:
        nome = (novo_item or ind.item_solicitado_texto or "").strip()
        categoria = db.get(Categoria, categoria_id) if categoria_id else None
        if not nome or not categoria:
            return RedirectResponse("/admin/itens-pendentes?erro=Escolha um item existente ou crie um novo com categoria", status_code=303)

        catalogo_item = next(
            (x for x in db.query(CatalogoItem).filter(CatalogoItem.categoria_id == categoria.id).all()
             if _normalizar_texto(x.nome) == _normalizar_texto(nome)), None
        )
        if not catalogo_item:
            catalogo_item = CatalogoItem(categoria_id=categoria.id, nome=nome, ativo=1)
            db.add(catalogo_item)
            db.flush()

    ind.catalogo_item_id = catalogo_item.id
    ind.item_solicitado_texto = None

    area = area_da_localidade(db, ind.localidade_id) if ind.localidade_id else None
    if area:
        ind.area_id = area.id
        ind.zona = area.nome
        ind.status = "Aguardando sorteio"
    else:
        ind.status = "Aguardando classificação"

    db.commit()
    return RedirectResponse("/admin/itens-pendentes?ok=Item vinculado com sucesso", status_code=303)



@app.get("/admin/validacoes", response_class=HTMLResponse)
def admin_validacoes(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    regras = db.query(RegraValidacao).order_by(RegraValidacao.id.desc()).all()
    categorias = db.query(Categoria).filter(Categoria.ativo == 1).order_by(Categoria.nome).all()
    categorias_map = {c.id: c for c in categorias}
    return templates.TemplateResponse("validacoes.html", {
        "request": request,
        "usuario": usuario,
        "regras": regras,
        "categorias": categorias,
        "categorias_map": categorias_map,
    })


@app.post("/admin/validacoes")
def admin_validacoes_salvar(
    nome: str = Form(...),
    tipo: str = Form("catalogo_obrigatorio"),
    categoria_id: int = Form(...),
    valor_obrigatorio: str = Form(""),
    mensagem_bloqueio: str = Form(""),
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db)
):
    exigir_admin(usuario)
    tipo_limpo = tipo.strip()
    valor_limpo = valor_obrigatorio.strip()

    if tipo_limpo == "catalogo_obrigatorio" and not _chave_pacote_catalogo(valor_limpo):
        return RedirectResponse(
            "/admin/validacoes?erro=Informe o catálogo no formato AAAA.N, por exemplo 2025.2",
            status_code=303
        )

    # Mantém apenas uma regra ativa por categoria e tipo.
    db.query(RegraValidacao).filter(
        RegraValidacao.categoria_id == categoria_id,
        RegraValidacao.tipo == tipo_limpo,
        RegraValidacao.ativo == 1
    ).update({"ativo": 0}, synchronize_session=False)

    db.add(RegraValidacao(
        nome=nome.strip(),
        tipo=tipo_limpo,
        categoria_id=categoria_id,
        valor_obrigatorio=valor_limpo or None,
        mensagem_bloqueio=mensagem_bloqueio.strip() or None,
        ativo=1,
        somente_zona_propria=1 if form.get("somente_zona_propria") else 0
    ))
    db.commit()
    return RedirectResponse("/admin/validacoes?ok=Regra criada", status_code=303)


@app.get("/admin/validacoes/{regra_id}/editar", response_class=HTMLResponse)
def admin_validacoes_editar(
    regra_id: int,
    request: Request,
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db)
):
    exigir_admin(usuario)
    regra = db.get(RegraValidacao, regra_id)
    if not regra:
        return RedirectResponse("/admin/validacoes?erro=Regra não encontrada", status_code=303)

    regras = db.query(RegraValidacao).order_by(RegraValidacao.id.desc()).all()
    categorias = db.query(Categoria).filter(Categoria.ativo == 1).order_by(Categoria.nome).all()
    categorias_map = {c.id: c for c in categorias}
    return templates.TemplateResponse("validacoes.html", {
        "request": request,
        "usuario": usuario,
        "regras": regras,
        "categorias": categorias,
        "categorias_map": categorias_map,
        "regra_edicao": regra,
    })


@app.post("/admin/validacoes/{regra_id}/editar")
def admin_validacoes_atualizar(
    regra_id: int,
    nome: str = Form(...),
    tipo: str = Form("catalogo_obrigatorio"),
    categoria_id: int = Form(...),
    valor_obrigatorio: str = Form(""),
    mensagem_bloqueio: str = Form(""),
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db)
):
    exigir_admin(usuario)
    regra = db.get(RegraValidacao, regra_id)
    if not regra:
        return RedirectResponse("/admin/validacoes?erro=Regra não encontrada", status_code=303)

    tipo_limpo = tipo.strip()
    valor_limpo = valor_obrigatorio.strip()
    if tipo_limpo == "catalogo_obrigatorio" and not _chave_pacote_catalogo(valor_limpo):
        return RedirectResponse(
            f"/admin/validacoes/{regra_id}/editar?erro=Informe o catálogo no formato AAAA.N, por exemplo 2025.2",
            status_code=303
        )

    db.query(RegraValidacao).filter(
        RegraValidacao.id != regra_id,
        RegraValidacao.categoria_id == categoria_id,
        RegraValidacao.tipo == tipo_limpo,
        RegraValidacao.ativo == 1
    ).update({"ativo": 0}, synchronize_session=False)

    regra.nome = nome.strip()
    regra.tipo = tipo_limpo
    regra.categoria_id = categoria_id
    regra.valor_obrigatorio = valor_limpo or None
    regra.mensagem_bloqueio = mensagem_bloqueio.strip() or None
    regra.ativo = 1
    db.commit()
    return RedirectResponse("/admin/validacoes?ok=Regra atualizada", status_code=303)


@app.post("/admin/validacoes/{regra_id}/toggle")
def admin_validacoes_toggle(
    regra_id: int,
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db)
):
    exigir_admin(usuario)
    regra = db.get(RegraValidacao, regra_id)
    if regra:
        regra.ativo = 0 if regra.ativo else 1
        db.commit()
    return RedirectResponse("/admin/validacoes", status_code=303)


@app.get("/admin/locais-pendentes", response_class=HTMLResponse)
def locais_pendentes(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    indicacoes = db.query(Indicacao).filter(Indicacao.status == "Aguardando classificação").order_by(Indicacao.criado_em).all()
    localidades = {l.id: l for l in db.query(Localidade).all()}
    municipios = {m.id: m for m in db.query(Municipio).all()}
    estados = {e.id: e for e in db.query(Estado).all()}
    areas = db.query(Zona).filter(Zona.ativo == 1).order_by(Zona.nome).all()
    return templates.TemplateResponse("locais_pendentes.html", {
        "request": request, "usuario": usuario, "indicacoes": indicacoes,
        "localidades": localidades, "municipios": municipios, "estados": estados, "areas": areas
    })


@app.post("/admin/localidades/{localidade_id}/classificar")
def classificar_localidade(localidade_id: int, area_id: int = Form(...), usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    localidade = db.get(Localidade, localidade_id)
    area = db.get(Zona, area_id)
    if not localidade or not area or not area.ativo:
        return RedirectResponse("/admin/locais-pendentes?erro=Local ou área inválidos", status_code=303)

    vinculo = db.query(AreaLocalidade).filter(AreaLocalidade.localidade_id == localidade.id).first()
    if vinculo:
        vinculo.area_id = area.id
    else:
        db.add(AreaLocalidade(area_id=area.id, localidade_id=localidade.id))

    relacionadas = db.query(Indicacao).filter(
        Indicacao.localidade_id == localidade.id,
        Indicacao.status.in_(["Aguardando classificação", "Aguardando sorteio"])
    ).all()
    for ind in relacionadas:
        ind.area_id = area.id
        ind.zona = area.nome
        if ind.status == "Aguardando classificação":
            ind.status = "Aguardando sorteio"
    db.commit()
    return RedirectResponse("/admin/locais-pendentes?ok=Local classificado; indicações liberadas para sorteio", status_code=303)


@app.get("/admin/sorteio", response_class=HTMLResponse)
def admin_sorteio(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    reprocessar_sorteios_pendentes(db)

    tentativas = db.query(Tentativa).order_by(Tentativa.sorteado_em.desc(), Tentativa.id.desc()).all()
    indicacoes = db.query(Indicacao).order_by(Indicacao.criado_em.desc(), Indicacao.id.desc()).all()
    indicacoes_map = {i.id: i for i in indicacoes}
    usuarios_map = {u.id: u for u in db.query(Usuario).all()}
    itens = {i.id: i for i in db.query(Item).all()}

    aguardando = db.query(Indicacao).filter(Indicacao.status == "Aguardando sorteio").count()
    aguardando_admin = db.query(Indicacao).filter(Indicacao.status == "Aguardando admin").count()
    total_sorteios = len(tentativas)
    vencedores_ids = {t.usuario_id for t in tentativas}

    karaoke_cat = next(
        (c for c in db.query(Categoria).filter(Categoria.ativo == 1).all()
         if _normalizar_texto(c.nome) == "karaoke"), None
    )
    vinculados = set()
    if karaoke_cat:
        vinculados = {
            x.usuario_id for x in db.query(UsuarioCategoria).filter(
                UsuarioCategoria.categoria_id == karaoke_cat.id
            ).all()
        }

    aptos = []
    nao_aptos = []
    for u in db.query(Usuario).filter(Usuario.ativo == 1, Usuario.aprovado == 1).all():
        if u.is_admin:
            continue

        apto_karaoke = False
        motivo_karaoke = "Não está vinculado à categoria Karaokê"
        if u.id in vinculados:
            if not u.krj_validado or not u.krj_cliente_id:
                motivo_karaoke = "Cadastro do Organiza ainda não validado para Karaokê"
            elif karaoke_cat:
                validacao = validar_usuario_regras(db, u, karaoke_cat.id)
                apto_karaoke = bool(validacao.get("apto"))
                if not apto_karaoke:
                    motivo_karaoke = (validacao.get("mensagens") or ["Não atende à regra vigente de Karaokê"])[0]

        apto_fliperama = bool(
            u.krj_validado
            and u.krj_cliente_id
            and int(u.krj_fliperama_qtd or 0) > 0
        )

        if apto_karaoke or apto_fliperama:
            aptos.append(u)
        else:
            motivo_flip = "Não possui Fliperama ativo no Organiza"
            nao_aptos.append({"usuario": u, "motivo": f"Karaokê: {motivo_karaoke} · Fliperama: {motivo_flip}"})
    aptos.sort(key=lambda u: (_normalizar_texto(u.zona or ""), _normalizar_texto(u.nome or "")))
    nao_aptos.sort(key=lambda r: (_normalizar_texto(r["usuario"].zona or ""), _normalizar_texto(r["usuario"].nome or "")))
    ainda_nao_receberam = [u for u in aptos if u.id not in vencedores_ids]

    contagem = {}
    for t in tentativas:
        contagem[t.usuario_id] = contagem.get(t.usuario_id, 0) + 1
    distribuicao = sorted(
        [(usuarios_map.get(uid), qtd) for uid, qtd in contagem.items() if usuarios_map.get(uid)],
        key=lambda x: (_normalizar_texto(x[0].zona or ""), _normalizar_texto(x[0].nome or ""))
    )

    # Uma linha por indicação. As tentativas anteriores ficam na tela "Ver histórico".
    tentativas_por_indicacao = {}
    for t in tentativas:
        tentativas_por_indicacao.setdefault(t.indicacao_id, []).append(t)

    indicacoes_resumo = []
    for ind in indicacoes:
        historico = tentativas_por_indicacao.get(ind.id, [])
        ultima = historico[0] if historico else None
        ganhador = usuarios_map.get(ultima.usuario_id) if ultima else None
        indicador = usuarios_map.get(ind.indicado_por_id) if ind.indicado_por_id else None
        indicacoes_resumo.append({
            "indicacao": ind,
            "indicador": indicador,
            "ultima_tentativa": ultima,
            "ganhador": ganhador,
            "item": itens.get(ind.item_id),
            "total_tentativas": len(historico),
        })

    # Filtros da listagem de indicações (mantém os indicadores gerais sem filtro).
    filtro_busca = (request.query_params.get("busca") or "").strip()
    filtro_status = (request.query_params.get("status") or "").strip()
    filtro_zona = (request.query_params.get("zona") or "").strip()
    filtro_item = (request.query_params.get("item") or "").strip()
    filtro_situacao = (request.query_params.get("situacao") or "").strip()

    def texto_filtro(row):
        ind = row["indicacao"]
        partes = [
            str(ind.id), ind.status, ind.zona, getattr(ind, "local_texto", None),
            row["indicador"].nome if row["indicador"] else None,
            row["ganhador"].nome if row["ganhador"] else None,
            row["item"].nome if row["item"] else None,
        ]
        return _normalizar_texto(" ".join(str(x) for x in partes if x))

    if filtro_busca:
        termo = _normalizar_texto(filtro_busca.lstrip("#"))
        indicacoes_resumo = [r for r in indicacoes_resumo if termo in texto_filtro(r)]
    if filtro_status:
        indicacoes_resumo = [r for r in indicacoes_resumo if r["indicacao"].status == filtro_status]
    if filtro_zona:
        indicacoes_resumo = [r for r in indicacoes_resumo if (r["indicacao"].zona or "") == filtro_zona]
    if filtro_item:
        indicacoes_resumo = [r for r in indicacoes_resumo if r["item"] and str(r["item"].id) == filtro_item]
    if filtro_situacao == "abertas":
        indicacoes_resumo = [r for r in indicacoes_resumo if not r["indicacao"].encerrado_em]
    elif filtro_situacao == "finalizadas":
        indicacoes_resumo = [r for r in indicacoes_resumo if r["indicacao"].encerrado_em]
    elif filtro_situacao == "admin":
        indicacoes_resumo = [r for r in indicacoes_resumo if r["indicacao"].status == "Aguardando admin"]
    elif filtro_situacao == "atendimento":
        indicacoes_resumo = [r for r in indicacoes_resumo if r["indicacao"].status == "Em atendimento"]

    status_opcoes = sorted({i.status for i in indicacoes if i.status}, key=_normalizar_texto)
    zonas_opcoes = sorted({i.zona for i in indicacoes if i.zona}, key=_normalizar_texto)
    itens_opcoes = sorted(itens.values(), key=lambda x: _normalizar_texto(x.nome or ""))

    return templates.TemplateResponse("sorteio.html", {
        "request": request, "usuario": usuario,
        "tentativas": tentativas,
        "indicacoes_map": indicacoes_map,
        "usuarios": usuarios_map,
        "itens": itens,
        "aguardando": aguardando,
        "aguardando_admin": aguardando_admin,
        "total_sorteios": total_sorteios,
        "total_vencedores": len(vencedores_ids),
        "aptos": aptos,
        "ainda_nao_receberam": ainda_nao_receberam,
        "distribuicao": distribuicao,
        "indicacoes_resumo": indicacoes_resumo,
        "nao_aptos": nao_aptos,
        "status_opcoes": status_opcoes,
        "zonas_opcoes": zonas_opcoes,
        "itens_opcoes": itens_opcoes,
        "retorno_filtros": str(request.url.path) + (("?" + request.url.query) if request.url.query else ""),
        "filtros": {
            "busca": filtro_busca,
            "status": filtro_status,
            "zona": filtro_zona,
            "item": filtro_item,
            "situacao": filtro_situacao,
        },
    })


@app.get("/admin/sorteio/indicacoes/{indicacao_id}/historico", response_class=HTMLResponse)
def historico_indicacao(indicacao_id: int, request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    ind = db.get(Indicacao, indicacao_id)
    if not ind:
        return RedirectResponse("/admin/sorteio?erro=Indicação não encontrada", status_code=303)

    tentativas = (db.query(Tentativa)
        .filter(Tentativa.indicacao_id == indicacao_id)
        .order_by(Tentativa.rodada, Tentativa.sorteado_em, Tentativa.id)
        .all())
    usuarios = {u.id: u for u in db.query(Usuario).all()}
    auditoria = (db.query(SorteioAuditoria)
        .filter(SorteioAuditoria.indicacao_id == indicacao_id)
        .order_by(SorteioAuditoria.rodada, SorteioAuditoria.selecionado.desc(), SorteioAuditoria.elegivel.desc(), SorteioAuditoria.id)
        .all())
    auditoria_por_rodada = {}
    for registro in auditoria:
        auditoria_por_rodada.setdefault(registro.rodada, []).append(registro)
    return templates.TemplateResponse("sorteio_historico.html", {
        "request": request,
        "usuario": usuario,
        "indicacao": ind,
        "indicador": usuarios.get(ind.indicado_por_id),
        "item": db.get(Item, ind.item_id),
        "tentativas": tentativas,
        "usuarios": usuarios,
        "auditoria_por_rodada": auditoria_por_rodada,
    })


@app.post("/admin/sorteio/indicacoes/{indicacao_id}/reabrir")
async def reabrir_indicacao_admin(indicacao_id: int, request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    """Tenta novamente somente com participantes ainda não usados na rodada atual."""
    exigir_admin(usuario)
    form = await request.form()
    retorno = form.get("retorno") or "/admin/sorteio"
    ind = db.get(Indicacao, indicacao_id)
    if not ind:
        return RedirectResponse(_retorno_admin_sorteio(retorno, "erro", "Indicação não encontrada"), status_code=303)
    if ind.encerrado_em:
        return RedirectResponse(_retorno_admin_sorteio(retorno, "erro", "Indicação já encerrada"), status_code=303)
    ind.status = "Aguardando sorteio"
    ind.recebido_por_id = None
    ind.pedido_token = None
    escolhido = executar_sorteio_automatico(db, ind)
    db.commit()
    mensagem = (
        "Novo participante ainda não utilizado foi selecionado"
        if escolhido else
        "Nenhum participante novo está elegível; a indicação continua aguardando o administrador"
    )
    return RedirectResponse(_retorno_admin_sorteio(retorno, "ok", mensagem), status_code=303)


@app.post("/admin/sorteio/indicacoes/{indicacao_id}/reiniciar")
async def reiniciar_sorteio_admin(indicacao_id: int, request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    """Inicia uma rodada nova e permite reconsiderar participantes das rodadas anteriores."""
    exigir_admin(usuario)
    form = await request.form()
    retorno = form.get("retorno") or "/admin/sorteio"
    ind = db.get(Indicacao, indicacao_id)
    if not ind:
        return RedirectResponse(_retorno_admin_sorteio(retorno, "erro", "Indicação não encontrada"), status_code=303)
    if ind.encerrado_em:
        return RedirectResponse(_retorno_admin_sorteio(retorno, "erro", "Indicação já encerrada"), status_code=303)
    tentativa_aberta = db.query(Tentativa).filter(
        Tentativa.indicacao_id == indicacao_id, Tentativa.finalizado_em.is_(None)
    ).order_by(Tentativa.id.desc()).first()
    if tentativa_aberta:
        tentativa_aberta.resultado = "Reiniciada pelo admin"
        tentativa_aberta.finalizado_em = datetime.now()
    ind.sorteio_rodada = max(1, int(ind.sorteio_rodada or 1)) + 1
    ind.status = "Aguardando sorteio"
    ind.recebido_por_id = None
    ind.pedido_token = None
    escolhido = executar_sorteio_automatico(db, ind)
    db.commit()
    mensagem = (
        f"Rodada {ind.sorteio_rodada} iniciada e participante selecionado"
        if escolhido else
        f"Rodada {ind.sorteio_rodada} iniciada, mas não há participante elegível"
    )
    return RedirectResponse(_retorno_admin_sorteio(retorno, "ok", mensagem), status_code=303)


@app.get("/admin/sorteio/indicacoes/{indicacao_id}/reenviar-whatsapp")
def reenviar_oportunidade_whatsapp_admin(indicacao_id: int, request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    """Reabre no WhatsApp do administrador a mensagem destinada ao participante atual."""
    exigir_admin(usuario)
    ind = db.get(Indicacao, indicacao_id)
    if not ind or ind.status != "Em atendimento" or not ind.recebido_por_id or not ind.pedido_token:
        return RedirectResponse("/admin/sorteio?erro=Não existe participante atual para reenviar a mensagem", status_code=303)
    participante = db.get(Usuario, ind.recebido_por_id)
    if not participante or not whatsapp_valido(participante.whatsapp):
        return RedirectResponse("/admin/sorteio?erro=O participante atual não possui WhatsApp válido", status_code=303)
    if normalizar_whatsapp(participante.whatsapp) == normalizar_whatsapp(ind.whatsapp):
        return RedirectResponse(
            "/admin/sorteio?erro=O WhatsApp do participante é o mesmo número informado na indicação; o envio foi bloqueado",
            status_code=303,
        )
    item = db.get(Item, ind.item_id)
    mensagem = _mensagem_nova_oportunidade(request, ind, participante, item)
    ind.whatsapp_encaminhado_em = datetime.now()
    db.commit()
    return RedirectResponse(_url_whatsapp(participante.whatsapp, mensagem), status_code=302)


@app.post("/admin/sorteio/indicacoes/{indicacao_id}/finalizar")
async def finalizar_indicacao_admin(indicacao_id: int, request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    ind = db.get(Indicacao, indicacao_id)
    if not ind:
        return RedirectResponse("/admin/sorteio?erro=Indicação não encontrada", status_code=303)
    if ind.encerrado_em or ind.status in {"Sucesso", "Cliente não deseja", "Finalizada pelo administrador"}:
        return RedirectResponse("/admin/sorteio?erro=Esta indicação já está finalizada", status_code=303)

    form = await request.form()
    retorno = form.get("retorno") or "/admin/sorteio"
    motivo = (form.get("motivo") or "Sem participante disponível").strip()[:180]
    agora = datetime.now()
    tentativa = (db.query(Tentativa)
        .filter(Tentativa.indicacao_id == indicacao_id, Tentativa.finalizado_em.is_(None))
        .order_by(Tentativa.id.desc()).first())
    if tentativa:
        tentativa.resultado = "Finalizada pelo administrador"
        tentativa.finalizado_em = agora

    ind.status = "Finalizada pelo administrador"
    ind.encerrado_em = agora
    ind.recebido_por_id = None
    ind.pedido_token = None
    db.commit()
    return RedirectResponse(
        _retorno_admin_sorteio(retorno, "ok", f"Indicação #{ind.id} finalizada: {motivo}"),
        status_code=303
    )


@app.post("/admin/sorteio/indicacoes/{indicacao_id}/excluir-teste")
async def excluir_indicacao_teste(indicacao_id: int, request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    """Exclui uma indicação administrativa e desfaz o crédito concedido ao indicador."""
    exigir_admin(usuario)
    form = await request.form()
    retorno = form.get("retorno") or "/admin/sorteio"
    ind = db.get(Indicacao, indicacao_id)
    if not ind:
        return RedirectResponse(_retorno_admin_sorteio(retorno, "erro", "Indicação não encontrada"), status_code=303)

    indicador = db.get(Usuario, ind.indicado_por_id) if ind.indicado_por_id else None
    credito_retirado = False
    if indicador and int(indicador.prioridade_creditos or 0) > 0:
        indicador.prioridade_creditos = int(indicador.prioridade_creditos or 0) - 1
        credito_retirado = True

    db.query(Tentativa).filter(
        Tentativa.indicacao_id == indicacao_id
    ).delete(synchronize_session=False)
    db.delete(ind)
    db.commit()

    mensagem = f"Indicação #{indicacao_id} e histórico excluídos"
    if credito_retirado:
        mensagem += "; 1 crédito foi retirado do indicador"
    elif indicador:
        mensagem += "; o indicador já não possuía crédito disponível"
    return RedirectResponse(_retorno_admin_sorteio(retorno, "ok", mensagem), status_code=303)


def extrair_zonas_bloqueadas_form(form, zonas: list[str]) -> tuple[list[str], list[str]]:
    """Lê a escolha simples Atende/Não atende de cada zona."""
    atendidas: list[str] = []
    bloqueadas: list[str] = []
    for indice, zona in enumerate(zonas):
        status = (form.get(f"zona_status_{indice}") or "nao_atende").strip().lower()
        if status == "atende":
            atendidas.append(zona)
        else:
            bloqueadas.append(zona)
    return atendidas, bloqueadas


@app.get("/meu-cadastro", response_class=HTMLResponse)
def meu_cadastro(
    request: Request,
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db)
):
    vinculo = db.query(UsuarioCategoria).filter(UsuarioCategoria.usuario_id == usuario.id).first()
    categoria = db.get(Categoria, vinculo.categoria_id) if vinculo else None
    try:
        equipamentos = json.loads(usuario.krj_equipamentos_json or "[]")
    except Exception:
        equipamentos = []

    zonas = [z.nome for z in db.query(Zona).filter(Zona.ativo == 1).order_by(Zona.nome).all()]
    try:
        configuracao = json.loads(usuario.zonas_bloqueadas_json or "[]")
        configurado = isinstance(configuracao, list) and "__CONFIGURADO__" in configuracao
        zonas_bloqueadas = {z for z in configuracao if z != "__CONFIGURADO__"} if configurado else set(zonas)
    except (TypeError, ValueError, json.JSONDecodeError):
        configurado = False
        zonas_bloqueadas = set(zonas)
    # A zona principal é sempre atendida por padrão e corrige automaticamente
    # cadastros antigos que tenham sido salvos com tudo como “Não atende”.
    zonas_bloqueadas.discard(usuario.zona)

    agora = datetime.now()
    ultima_atualizacao = usuario.zonas_bloqueadas_atualizadas_em
    pode_editar_zonas = (
        ultima_atualizacao is None
        or ultima_atualizacao.year != agora.year
        or ultima_atualizacao.month != agora.month
    )

    return templates.TemplateResponse("meu_cadastro.html", {
        "request": request,
        "usuario": usuario,
        "categoria": categoria,
        "equipamentos": equipamentos,
        "zonas": zonas,
        "zonas_bloqueadas": zonas_bloqueadas,
        "pode_editar_zonas": pode_editar_zonas,
        "zonas_configuradas": configurado,
        "ultima_atualizacao_zonas": ultima_atualizacao,
    })


@app.post("/meu-cadastro")
async def meu_cadastro_salvar(
    request: Request,
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db)
):
    form = await request.form()

    nome = normalizar_nome_exibicao(form.get("nome") or "")
    whatsapp = (form.get("whatsapp") or "").strip()
    cpf = normalizar_cpf(form.get("cpf") or "")
    senha_atual = form.get("senha_atual") or ""
    nova_senha = form.get("nova_senha") or ""
    confirmar_senha = form.get("confirmar_senha") or ""

    if not nome_completo_valido(nome):
        return RedirectResponse("/meu-cadastro?erro=Favor informar um nome completo correto. Essa informação será exibida ao cliente final.", status_code=303)
    if not cpf_valido(cpf):
        return RedirectResponse("/meu-cadastro?erro=Informe um CPF válido", status_code=303)
    if not whatsapp_valido(whatsapp):
        return RedirectResponse("/meu-cadastro?erro=Informe um WhatsApp válido com DDD", status_code=303)

    telefone_normalizado = normalizar_whatsapp(whatsapp)
    for outro in db.query(Usuario).filter(Usuario.id != usuario.id).all():
        if normalizar_cpf(outro.cpf or "") == cpf:
            return RedirectResponse("/meu-cadastro?erro=Este CPF já está cadastrado", status_code=303)
        if normalizar_whatsapp(outro.whatsapp or "") == telefone_normalizado:
            return RedirectResponse("/meu-cadastro?erro=Este WhatsApp já está cadastrado", status_code=303)
    usuario.nome = nome
    usuario.whatsapp = telefone_normalizado
    usuario.cpf = cpf

    # As zonas não atendidas são administradas pelo próprio usuário, no máximo
    # uma vez por mês. Na primeira configuração, todas começam marcadas.
    if form.get("salvar_zonas") == "1":
        agora = datetime.now()
        ultima = usuario.zonas_bloqueadas_atualizadas_em
        pode_editar = ultima is None or ultima.year != agora.year or ultima.month != agora.month
        if not pode_editar:
            return RedirectResponse(
                "/meu-cadastro?erro=As zonas de atendimento já foram atualizadas neste mês",
                status_code=303,
            )
        zonas_ativas = [z.nome for z in db.query(Zona).filter(Zona.ativo == 1).order_by(Zona.nome).all()]
        zonas_atendidas, zonas_bloqueadas = extrair_zonas_bloqueadas_form(form, zonas_ativas)
        if usuario.zona in zonas_bloqueadas:
            zonas_bloqueadas.remove(usuario.zona)
        if usuario.zona and usuario.zona not in zonas_atendidas:
            zonas_atendidas.append(usuario.zona)
        if not zonas_atendidas:
            return RedirectResponse(
                "/meu-cadastro?erro=Marque Atende em pelo menos uma zona",
                status_code=303,
            )
        usuario.somente_zona_propria = 0
        usuario.zonas_bloqueadas_json = json.dumps(
            ["__CONFIGURADO__", *zonas_bloqueadas], ensure_ascii=False
        )
        usuario.zonas_bloqueadas_atualizadas_em = agora
        # Pré-cadastro criado pelo Humiat: ao concluir a primeira configuração
        # das áreas e já possuir categoria principal, passa a ficar liberado.
        vinculo_categoria = db.query(UsuarioCategoria.id).filter(UsuarioCategoria.usuario_id == usuario.id).first()
        if vinculo_categoria:
            usuario.aprovado = 1

    if nova_senha or confirmar_senha:
        if not senha_atual or not verificar_senha(senha_atual, usuario.senha_hash):
            return RedirectResponse("/meu-cadastro?erro=Senha atual incorreta", status_code=303)
        if len(nova_senha) < 6:
            return RedirectResponse("/meu-cadastro?erro=A nova senha deve ter pelo menos 6 caracteres", status_code=303)
        if nova_senha != confirmar_senha:
            return RedirectResponse("/meu-cadastro?erro=A confirmação da nova senha não confere", status_code=303)
        usuario.senha_hash = gerar_hash_senha(nova_senha)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(
            "/meu-cadastro?erro=CPF ou WhatsApp já cadastrado. Cada CPF e telefone podem pertencer a apenas uma conta.",
            status_code=303
        )
    return RedirectResponse("/meu-cadastro?ok=Cadastro atualizado com sucesso", status_code=303)




@app.get("/admin/novidades", response_class=HTMLResponse)
def admin_novidades(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    novidades = db.query(Novidade).order_by(Novidade.id.desc()).all()
    for item in novidades:
        item.itens = _novidade_itens(item)
    return templates.TemplateResponse("novidades.html", {"request": request, "usuario": usuario, "novidades": novidades})


@app.get("/admin/novidades/nova", response_class=HTMLResponse)
def admin_novidade_nova(request: Request, usuario: Usuario = Depends(usuario_logado)):
    exigir_admin(usuario)
    return templates.TemplateResponse("novidade_form.html", {"request": request, "usuario": usuario, "novidade": None, "itens_texto": ""})


@app.post("/admin/novidades/nova")
async def admin_novidade_criar(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    form = await request.form()
    titulo = (form.get("titulo") or "").strip()
    chamada = (form.get("chamada") or "").strip()
    itens_texto = (form.get("itens") or "").strip()
    if not titulo:
        return RedirectResponse("/admin/novidades/nova?erro=Informe o título da novidade", status_code=303)
    itens = []
    for linha in itens_texto.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        partes = [p.strip() for p in linha.split("|", 1)]
        itens.append({"titulo": partes[0], "descricao": partes[1] if len(partes) > 1 else ""})
    if not itens:
        return RedirectResponse("/admin/novidades/nova?erro=Inclua ao menos um item da novidade", status_code=303)
    publicar = 1 if form.get("ativo") else 0
    if publicar:
        db.query(Novidade).update({Novidade.ativo: 0}, synchronize_session=False)
    db.add(Novidade(titulo=titulo, chamada=chamada, itens_json=json.dumps(itens, ensure_ascii=False), ativo=publicar))
    db.commit()
    return RedirectResponse("/admin/novidades?ok=Novidade cadastrada com sucesso", status_code=303)


@app.get("/admin/novidades/{novidade_id}/editar", response_class=HTMLResponse)
def admin_novidade_editar(novidade_id: int, request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    novidade = db.get(Novidade, novidade_id)
    if not novidade:
        raise HTTPException(status_code=404, detail="Novidade não encontrada")
    itens = _novidade_itens(novidade)
    itens_texto = "\n".join(f"{i.get('titulo','')} | {i.get('descricao','')}" for i in itens)
    return templates.TemplateResponse("novidade_form.html", {"request": request, "usuario": usuario, "novidade": novidade, "itens_texto": itens_texto})


@app.post("/admin/novidades/{novidade_id}/editar")
async def admin_novidade_salvar(novidade_id: int, request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    novidade = db.get(Novidade, novidade_id)
    if not novidade:
        raise HTTPException(status_code=404, detail="Novidade não encontrada")
    form = await request.form()
    titulo = (form.get("titulo") or "").strip()
    chamada = (form.get("chamada") or "").strip()
    itens = []
    for linha in (form.get("itens") or "").splitlines():
        linha = linha.strip()
        if linha:
            partes = [p.strip() for p in linha.split("|", 1)]
            itens.append({"titulo": partes[0], "descricao": partes[1] if len(partes) > 1 else ""})
    if not titulo or not itens:
        return RedirectResponse(f"/admin/novidades/{novidade_id}/editar?erro=Informe o título e ao menos um item", status_code=303)
    publicar = 1 if form.get("ativo") else 0
    if publicar:
        db.query(Novidade).filter(Novidade.id != novidade_id).update({Novidade.ativo: 0}, synchronize_session=False)
    novidade.titulo = titulo
    novidade.chamada = chamada
    novidade.itens_json = json.dumps(itens, ensure_ascii=False)
    novidade.ativo = publicar
    novidade.atualizado_em = datetime.now()
    db.commit()
    return RedirectResponse("/admin/novidades?ok=Novidade atualizada com sucesso", status_code=303)


@app.post("/admin/novidades/{novidade_id}/ativar")
def admin_novidade_ativar(novidade_id: int, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    novidade = db.get(Novidade, novidade_id)
    if not novidade:
        raise HTTPException(status_code=404, detail="Novidade não encontrada")
    db.query(Novidade).update({Novidade.ativo: 0}, synchronize_session=False)
    novidade.ativo = 1
    novidade.atualizado_em = datetime.now()
    db.commit()
    return RedirectResponse("/admin/novidades?ok=Novidade publicada. Todos os usuários voltarão a vê-la.", status_code=303)


@app.post("/admin/novidades/{novidade_id}/desativar")
def admin_novidade_desativar(novidade_id: int, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    novidade = db.get(Novidade, novidade_id)
    if novidade:
        novidade.ativo = 0
        db.commit()
    return RedirectResponse("/admin/novidades?ok=Novidade desativada", status_code=303)


@app.get("/admin/usuarios", response_class=HTMLResponse)
def usuarios(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    todos = db.query(Usuario).order_by(Usuario.zona, Usuario.nome).all()
    karaoke_id = _categoria_karaoke_id(db)
    linhas = []
    for u in todos:
        validacao = validar_usuario_regras(db, u, karaoke_id) if karaoke_id and u.krj_validado else None
        linhas.append({
            "usuario": u,
            "apto": bool(validacao and validacao.get("apto")),
            "apto_fliperama": int(u.krj_fliperama_qtd or 0) > 0,
            "qtd_fliperama": int(u.krj_fliperama_qtd or 0),
            "minimo": validacao.get("catalogo_obrigatorio") if validacao else None,
            "ultima": validacao.get("ultima_atualizacao") if validacao else None,
            "atualizacao_pendente": bool(validacao and validacao.get("atualizacao_pendente")),
        })
    return templates.TemplateResponse("usuarios.html", {"request": request, "usuario": usuario, "usuarios": todos, "linhas": linhas})


@app.post("/admin/usuarios/{usuario_id}/atualizar-organiza")
def usuario_atualizar_organiza(
    usuario_id: int,
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db),
):
    """Atualização manual do cache Organiza para um usuário da lista administrativa."""
    exigir_admin(usuario)
    alvo = db.get(Usuario, usuario_id)
    if not alvo:
        return JSONResponse({"ok": False, "mensagem": "Usuário não encontrado."}, status_code=404)

    resultado = consultar_organiza_cliente(
        alvo.cpf or "",
        alvo.whatsapp or "",
        cliente_id=str(alvo.krj_cliente_id or ""),
    )

    if not resultado.get("ok"):
        return JSONResponse(
            {"ok": False, "mensagem": resultado.get("mensagem") or "Falha ao consultar o Organiza."},
            status_code=503,
        )

    if not resultado.get("encontrado"):
        # Aqui a consulta respondeu corretamente e confirmou que não há vínculo atual.
        # Isso é diferente de falha de rede: nesse caso o cache antigo deve ser removido.
        limpar_cache_organiza_usuario(alvo)
        sincronizar_categorias_por_equipamentos(db, alvo)
        db.commit()
        return {
            "ok": True,
            "encontrado": False,
            "usuario_id": alvo.id,
            "nome": alvo.nome,
            "mensagem": "Cliente não encontrado no Organiza; cache anterior removido.",
        }

    aplicar_cache_krj(alvo, resultado)
    sincronizar_categorias_por_equipamentos(db, alvo)
    db.commit()
    return {
        "ok": True,
        "encontrado": True,
        "usuario_id": alvo.id,
        "nome": alvo.nome,
        "jukebox": int(alvo.krj_jukebox_qtd or 0),
        "portatil": int(alvo.krj_portatil_qtd or 0),
        "iphone": int(alvo.krj_iphone_qtd or 0),
        "fliperama": int(alvo.krj_fliperama_qtd or 0),
    }


@app.get("/admin/usuarios/novo", response_class=HTMLResponse)
def usuario_novo(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    zonas = [z.nome for z in db.query(Zona).filter(Zona.ativo == 1).order_by(Zona.nome).all()]
    categorias = db.query(Categoria).filter(Categoria.ativo == 1).order_by(Categoria.nome).all()
    catalogo_itens = db.query(CatalogoItem).filter(CatalogoItem.ativo == 1).order_by(CatalogoItem.nome).all()
    itens_por_categoria = {}
    for ci in catalogo_itens:
        itens_por_categoria.setdefault(ci.categoria_id, []).append(ci)
    return templates.TemplateResponse("usuario_form.html", {
        "request": request, "usuario": usuario, "editado": None, "zonas": zonas,
        "categorias": categorias, "itens_por_categoria": itens_por_categoria,
        "categorias_selecionadas": set(), "catalogo_itens_selecionados": set(),
        "zonas_bloqueadas_selecionadas": set(zonas)
    })


@app.post("/admin/usuarios/novo")
async def usuario_criar(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    form = await request.form()
    senha = form.get("senha") or ""
    nome = normalizar_nome_exibicao(form.get("nome") or "")
    whatsapp = (form.get("whatsapp") or "").strip()
    cpf = normalizar_cpf(form.get("cpf") or "")

    if not nome_completo_valido(nome):
        return RedirectResponse("/admin/usuarios/novo?erro=Favor informar um nome completo correto. Essa informação será exibida ao cliente final.", status_code=303)
    if not whatsapp_valido(whatsapp):
        return RedirectResponse("/admin/usuarios/novo?erro=Informe um WhatsApp válido com DDD; ele é obrigatório para gerar o token", status_code=303)
    if not cpf_valido(cpf):
        return RedirectResponse("/admin/usuarios/novo?erro=Informe um CPF válido", status_code=303)
    if not senha:
        return RedirectResponse("/admin/usuarios/novo?erro=Informe uma senha", status_code=303)
    telefone_normalizado = normalizar_whatsapp(whatsapp)
    for existente in db.query(Usuario).all():
        if normalizar_cpf(existente.cpf or "") == cpf:
            return RedirectResponse("/admin/usuarios/novo?erro=Este CPF já está cadastrado", status_code=303)
        if normalizar_whatsapp(existente.whatsapp or "") == telefone_normalizado:
            return RedirectResponse("/admin/usuarios/novo?erro=Este WhatsApp já está cadastrado", status_code=303)

    zona_nome = (form.get("zona") or "").strip()
    zona_obj = db.query(Zona).filter(Zona.nome == zona_nome, Zona.ativo == 1).first()
    if not zona_obj:
        return RedirectResponse("/admin/usuarios/novo?erro=Selecione uma zona ativa", status_code=303)

    zonas_ativas = [z.nome for z in db.query(Zona).filter(Zona.ativo == 1).order_by(Zona.nome).all()]
    zonas_atendidas, zonas_bloqueadas = extrair_zonas_bloqueadas_form(form, zonas_ativas)
    if not zonas_atendidas:
        return RedirectResponse("/admin/usuarios/novo?erro=Marque Atende em pelo menos uma zona", status_code=303)

    novo = Usuario(
        nome=nome,
        usuario=gerar_login_interno(db),
        whatsapp=telefone_normalizado,
        cpf=cpf,
        senha_hash=gerar_hash_senha(senha),
        zona=zona_obj.nome,
        is_admin=0,
        ativo=1,
        somente_zona_propria=0,
        zonas_bloqueadas_json=json.dumps(["__CONFIGURADO__", *zonas_bloqueadas], ensure_ascii=False),
        zonas_bloqueadas_atualizadas_em=datetime.now(),
        grupo_locadores=1 if form.get("grupo_locadores") == "1" else 0
    )
    db.add(novo)
    db.flush()
    definir_zona_gratuita(db, novo, zona_obj.nome)

    categoria_ids = []
    for valor in form.getlist("categoria_principal"):
        if str(valor).isdigit() and int(valor) not in categoria_ids:
            categoria_ids.append(int(valor))
    if not categoria_ids:
        db.rollback()
        return RedirectResponse("/admin/usuarios/novo?erro=Escolha pelo menos uma categoria", status_code=303)
    if len(categoria_ids) > 2:
        db.rollback()
        return RedirectResponse("/admin/usuarios/novo?erro=O usuário pode oferecer no máximo 2 categorias", status_code=303)

    karaoke_id = _categoria_karaoke_id(db)
    fliperama_id = _categoria_fliperama_id(db)

    if (form.get("krj_validado") or "") == "1":
        try:
            detalhes_org = json.loads(form.get("krj_equipamentos_json") or "[]")
        except Exception:
            detalhes_org = []
        resultado_org = {
            "encontrado": True,
            "cliente_id": form.get("krj_cliente_id") or "",
            "cpf": cpf,
            "atualizacao": form.get("krj_atualizacao") or "",
            "jukebox": int(form.get("krj_jukebox_qtd") or 0),
            "portatil": int(form.get("krj_portatil_qtd") or 0),
            "iphone": int(form.get("krj_iphone_qtd") or 0),
            "fliperama": int(form.get("krj_fliperama_qtd") or 0),
            "detalhes": detalhes_org,
        }
        aplicar_cache_krj(novo, resultado_org)

    if karaoke_id and karaoke_id in categoria_ids:
        if not novo.krj_validado or not novo.krj_cliente_id or (
            int(novo.krj_jukebox_qtd or 0) + int(novo.krj_portatil_qtd or 0) + int(novo.krj_iphone_qtd or 0) <= 0
        ):
            db.rollback()
            return RedirectResponse("/admin/usuarios/novo?erro=Para Karaokê, carregue os dados do Organiza e confirme pelo menos um equipamento válido", status_code=303)

    if fliperama_id and fliperama_id in categoria_ids:
        if not novo.krj_validado or not novo.krj_cliente_id or int(novo.krj_fliperama_qtd or 0) <= 0:
            db.rollback()
            return RedirectResponse("/admin/usuarios/novo?erro=Para Fliperama, carregue os dados do Organiza e confirme pelo menos 1 Fliperama ativo", status_code=303)

    catalogo_ids = [x for x in form.getlist("catalogo_itens") if str(x).isdigit()]
    if not definir_categorias_limitadas(db, novo, categoria_ids, catalogo_ids, maximo=2):
        db.rollback()
        return RedirectResponse("/admin/usuarios/novo?erro=Categorias inválidas", status_code=303)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(
            "/admin/usuarios/novo?erro=CPF ou WhatsApp já cadastrado. Cada CPF e telefone podem pertencer a apenas uma conta.",
            status_code=303
        )
    return RedirectResponse("/admin/usuarios", status_code=303)


@app.post("/admin/usuarios/{usuario_id}/aprovar")
def usuario_aprovar(usuario_id: int, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    editado = db.get(Usuario, usuario_id)
    if not editado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    editado.aprovado = 1
    editado.ativo = 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(
            "/admin/usuarios?erro=Não foi possível aprovar: CPF ou WhatsApp já pertence a outra conta ativa. Corrija o cadastro duplicado primeiro.",
            status_code=303
        )
    return RedirectResponse("/admin/usuarios?ok=Usuário aprovado com sucesso", status_code=303)


@app.get("/admin/usuarios/{usuario_id}/aprovar")
def usuario_aprovar_get(usuario_id: int, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    editado = db.get(Usuario, usuario_id)
    if not editado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return RedirectResponse("/admin/usuarios", status_code=303)


@app.post("/admin/usuarios/{usuario_id}/gerar-token")
def usuario_gerar_token(usuario_id: int, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    editado = db.get(Usuario, usuario_id)
    if not editado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    ja_existia = bool((editado.indicacao_token or "").strip())
    token = garantir_token_indicacao_usuario(db, editado)
    mensagem = "Token já existente" if ja_existia else "Token criado com sucesso"
    return RedirectResponse(
        f"/admin/usuarios/{usuario_id}/editar?ok={mensagem}: {token}",
        status_code=303,
    )


@app.get("/admin/usuarios/{usuario_id}/editar", response_class=HTMLResponse)
def usuario_editar_form(usuario_id: int, request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    editado = db.get(Usuario, usuario_id)
    if not editado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    zonas = [z.nome for z in db.query(Zona).filter(Zona.ativo == 1).order_by(Zona.nome).all()]
    categorias = db.query(Categoria).filter(Categoria.ativo == 1).order_by(Categoria.nome).all()
    catalogo_itens = db.query(CatalogoItem).filter(CatalogoItem.ativo == 1).order_by(CatalogoItem.nome).all()
    itens_por_categoria = {}
    for ci in catalogo_itens:
        itens_por_categoria.setdefault(ci.categoria_id, []).append(ci)
    categorias_selecionadas = {x.categoria_id for x in db.query(UsuarioCategoria).filter(UsuarioCategoria.usuario_id == editado.id).all()}
    catalogo_itens_selecionados = {x.catalogo_item_id for x in db.query(UsuarioCatalogoItem).filter(UsuarioCatalogoItem.usuario_id == editado.id).all()}

    # Diagnóstico somente visual: mantém exatamente os dados já armazenados
    # da última validação do HUMIAT, sem classificar ou alterar equipamentos.
    krj_equipamentos_resumo = []
    try:
        dados_equipamentos = json.loads(editado.krj_equipamentos_json or "[]")
        if isinstance(dados_equipamentos, list):
            krj_equipamentos_resumo = [item for item in dados_equipamentos if isinstance(item, dict)]
    except (TypeError, ValueError, json.JSONDecodeError):
        krj_equipamentos_resumo = []

    try:
        configuracao_zonas = json.loads(editado.zonas_bloqueadas_json or "[]")
        zonas_bloqueadas_selecionadas = {z for z in configuracao_zonas if z != "__CONFIGURADO__"}
        if "__CONFIGURADO__" not in configuracao_zonas:
            zonas_bloqueadas_selecionadas = set(zonas)
    except (TypeError, ValueError, json.JSONDecodeError):
        zonas_bloqueadas_selecionadas = set(zonas)
    zonas_bloqueadas_selecionadas.discard(editado.zona)

    return templates.TemplateResponse("usuario_form.html", {
        "request": request, "usuario": usuario, "editado": editado, "zonas": zonas,
        "categorias": categorias, "itens_por_categoria": itens_por_categoria,
        "categorias_selecionadas": categorias_selecionadas,
        "catalogo_itens_selecionados": catalogo_itens_selecionados,
        "krj_equipamentos_resumo": krj_equipamentos_resumo,
        "zonas_bloqueadas_selecionadas": zonas_bloqueadas_selecionadas,
    })


@app.post("/admin/usuarios/{usuario_id}/editar")
async def usuario_editar(usuario_id: int, request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    editado = db.get(Usuario, usuario_id)
    if not editado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    form = await request.form()

    zona_nome = (form.get("zona") or "").strip()
    zona_obj = db.query(Zona).filter(Zona.nome == zona_nome, Zona.ativo == 1).first()
    if not zona_obj:
        return RedirectResponse(f"/admin/usuarios/{usuario_id}/editar?erro=Selecione uma zona ativa", status_code=303)

    nome_editado = normalizar_nome_exibicao(form.get("nome") or "")
    whatsapp_editado = (form.get("whatsapp") or "").strip()
    cpf_editado = normalizar_cpf(form.get("cpf") or "")
    if not nome_completo_valido(nome_editado):
        return RedirectResponse(f"/admin/usuarios/{usuario_id}/editar?erro=Favor informar um nome completo correto. Essa informação será exibida ao cliente final.", status_code=303)
    if not cpf_valido(cpf_editado):
        return RedirectResponse(f"/admin/usuarios/{usuario_id}/editar?erro=Informe um CPF válido", status_code=303)
    if not whatsapp_valido(whatsapp_editado):
        return RedirectResponse(
            f"/admin/usuarios/{usuario_id}/editar?erro=Informe um WhatsApp válido com DDD; ele é obrigatório para gerar o token",
            status_code=303
        )

    telefone_normalizado = normalizar_whatsapp(whatsapp_editado)
    for outro in db.query(Usuario).filter(Usuario.id != editado.id).all():
        if normalizar_cpf(outro.cpf or "") == cpf_editado:
            return RedirectResponse(f"/admin/usuarios/{usuario_id}/editar?erro=Este CPF já está cadastrado", status_code=303)
        if normalizar_whatsapp(outro.whatsapp or "") == telefone_normalizado:
            return RedirectResponse(f"/admin/usuarios/{usuario_id}/editar?erro=Este WhatsApp já está cadastrado", status_code=303)
    editado.nome = nome_editado
    editado.whatsapp = telefone_normalizado
    editado.cpf = cpf_editado
    editado.grupo_locadores = 1 if form.get("grupo_locadores") == "1" else 0
    definir_zona_gratuita(db, editado, zona_obj.nome)

    # O administrador pode corrigir as zonas de qualquer usuário a qualquer momento.
    zonas_ativas = [z.nome for z in db.query(Zona).filter(Zona.ativo == 1).order_by(Zona.nome).all()]
    zonas_atendidas, zonas_bloqueadas = extrair_zonas_bloqueadas_form(form, zonas_ativas)
    if zona_obj.nome in zonas_bloqueadas:
        zonas_bloqueadas.remove(zona_obj.nome)
    if zona_obj.nome not in zonas_atendidas:
        zonas_atendidas.append(zona_obj.nome)
    if not zonas_atendidas:
        return RedirectResponse(
            f"/admin/usuarios/{usuario_id}/editar?erro=Marque Atende em pelo menos uma zona",
            status_code=303,
        )
    editado.somente_zona_propria = 0
    editado.zonas_bloqueadas_json = json.dumps(["__CONFIGURADO__", *zonas_bloqueadas], ensure_ascii=False)
    editado.zonas_bloqueadas_atualizadas_em = datetime.now()

    # Perfil administrativo não é alterado por esta tela pública/comercial.
    senha = form.get("senha") or ""
    if senha:
        editado.senha_hash = gerar_hash_senha(senha)

    categoria_ids = []
    for valor in form.getlist("categoria_principal"):
        if str(valor).isdigit() and int(valor) not in categoria_ids:
            categoria_ids.append(int(valor))
    if not categoria_ids:
        return RedirectResponse(f"/admin/usuarios/{usuario_id}/editar?erro=Escolha pelo menos uma categoria", status_code=303)
    if len(categoria_ids) > 2:
        return RedirectResponse(f"/admin/usuarios/{usuario_id}/editar?erro=O usuário pode oferecer no máximo 2 categorias", status_code=303)

    karaoke_id = _categoria_karaoke_id(db)

    if karaoke_id and karaoke_id in categoria_ids:
        # Se houve uma nova consulta nesta edição, atualiza o cache.
        if (form.get("krj_validado") or "") == "1":
            try:
                detalhes_krj = json.loads(form.get("krj_equipamentos_json") or "[]")
            except Exception:
                detalhes_krj = []

            resultado_krj = {
                "encontrado": True,
                "cliente_id": form.get("krj_cliente_id") or editado.krj_cliente_id or "",
                "cpf": form.get("cpf") or editado.cpf or "",
                "atualizacao": form.get("krj_atualizacao") or editado.krj_atualizacao or "",
                "jukebox": int(form.get("krj_jukebox_qtd") or editado.krj_jukebox_qtd or 0),
                "portatil": int(form.get("krj_portatil_qtd") or editado.krj_portatil_qtd or 0),
                "iphone": int(form.get("krj_iphone_qtd") or editado.krj_iphone_qtd or 0),
                "fliperama": int(form.get("krj_fliperama_qtd") or editado.krj_fliperama_qtd or 0),
                "detalhes": detalhes_krj,
            }
            aplicar_cache_krj(editado, resultado_krj)

        # Se já estava validado anteriormente, mantém os dados salvos.
        if not editado.krj_validado or not editado.krj_cliente_id:
            return RedirectResponse(
                f"/admin/usuarios/{usuario_id}/editar?erro=Para Karaokê, carregue e valide os dados da Karaoke RJ antes de salvar",
                status_code=303
            )

    fliperama_id = _categoria_fliperama_id(db)
    if fliperama_id and fliperama_id in categoria_ids:
        # Se houve nova consulta, o cache já contém a quantidade de fliperamas.
        if (form.get("krj_validado") or "") == "1":
            try:
                detalhes_flip = json.loads(form.get("krj_equipamentos_json") or "[]")
            except Exception:
                detalhes_flip = []
            resultado_flip = {
                "encontrado": True,
                "cliente_id": form.get("krj_cliente_id") or editado.krj_cliente_id or "",
                "cpf": form.get("cpf") or editado.cpf or "",
                "atualizacao": form.get("krj_atualizacao") or editado.krj_atualizacao or "",
                "jukebox": int(form.get("krj_jukebox_qtd") or editado.krj_jukebox_qtd or 0),
                "portatil": int(form.get("krj_portatil_qtd") or editado.krj_portatil_qtd or 0),
                "iphone": int(form.get("krj_iphone_qtd") or editado.krj_iphone_qtd or 0),
                "fliperama": int(form.get("krj_fliperama_qtd") or editado.krj_fliperama_qtd or 0),
                "detalhes": detalhes_flip,
            }
            aplicar_cache_krj(editado, resultado_flip)
        if int(editado.krj_fliperama_qtd or 0) <= 0:
            return RedirectResponse(
                f"/admin/usuarios/{usuario_id}/editar?erro=Para Fliperama, carregue os dados do Organiza e confirme pelo menos 1 Fliperama ativo",
                status_code=303
            )

    catalogo_ids = [x for x in form.getlist("catalogo_itens") if str(x).isdigit()]
    if not definir_categorias_limitadas(db, editado, categoria_ids, catalogo_ids, maximo=2):
        return RedirectResponse(f"/admin/usuarios/{usuario_id}/editar?erro=Categorias inválidas", status_code=303)

    # Cadastros antigos podem estar sem token. Ao salvar a edição, garante o link pessoal.
    if not (editado.indicacao_token or "").strip():
        garantir_token_indicacao_usuario(db, editado)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(
            f"/admin/usuarios/{usuario_id}/editar?erro=CPF ou WhatsApp já cadastrado. Cada CPF e telefone podem pertencer a apenas uma conta.",
            status_code=303
        )
    return RedirectResponse(f"/admin/usuarios/{usuario_id}/editar?ok=Usuário atualizado", status_code=303)


@app.get("/admin/produtos", response_class=HTMLResponse)
def produtos(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    itens = db.query(Item).order_by(Item.tipo, Item.nome).all()
    return templates.TemplateResponse("produtos.html", {"request": request, "usuario": usuario, "itens": itens})


@app.post("/admin/produtos")
def produto_criar(nome: str = Form(...), tipo: str = Form(...), usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    tipo = tipo if tipo in {"Produto", "Serviço"} else "Produto"
    nome = nome.strip()
    if not nome:
        return RedirectResponse("/admin/produtos?erro=Informe o nome", status_code=303)
    if db.query(Item).filter(func.lower(Item.nome) == nome.lower()).first():
        return RedirectResponse("/admin/produtos?erro=Já existe um produto ou serviço com esse nome", status_code=303)
    db.add(Item(nome=nome, tipo=tipo, ativo=1))
    db.commit()
    return RedirectResponse("/admin/produtos?ok=Cadastrado com sucesso", status_code=303)


@app.post("/admin/produtos/{item_id}/editar")
def produto_editar(item_id: int, nome: str = Form(...), tipo: str = Form(...), usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    nome = nome.strip()
    tipo = tipo if tipo in {"Produto", "Serviço"} else "Produto"
    duplicado = db.query(Item).filter(func.lower(Item.nome) == nome.lower(), Item.id != item_id).first()
    if not nome or duplicado:
        return RedirectResponse("/admin/produtos?erro=Nome inválido ou já cadastrado", status_code=303)
    item.nome = nome
    item.tipo = tipo
    db.commit()
    return RedirectResponse("/admin/produtos?ok=Cadastro atualizado", status_code=303)


@app.post("/admin/produtos/{item_id}/status")
def produto_status(item_id: int, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    item.ativo = 0 if item.ativo else 1
    db.commit()
    return RedirectResponse("/admin/produtos", status_code=303)


@app.get("/admin/zonas", response_class=HTMLResponse)
def zonas_lista(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    zonas = db.query(Zona).order_by(Zona.nome).all()
    municipios = {m.id: m for m in db.query(Municipio).all()}
    localidades = {l.id: l for l in db.query(Localidade).all()}
    bairros_por_zona = {z.id: [] for z in zonas}
    for vinculo in db.query(AreaLocalidade).all():
        loc = localidades.get(vinculo.localidade_id)
        if not loc: continue
        mun = municipios.get(loc.municipio_id)
        bairros_por_zona.setdefault(vinculo.area_id, []).append({"id": loc.id, "nome": loc.nome, "municipio": mun.nome if mun else ""})
    for itens in bairros_por_zona.values():
        itens.sort(key=lambda x: (_normalizar_texto(x["municipio"]), _normalizar_texto(x["nome"])))
    return templates.TemplateResponse("zonas.html", {"request": request, "usuario": usuario, "zonas": zonas, "bairros_por_zona": bairros_por_zona})

@app.post("/admin/zonas/localidades/{localidade_id}/mover")
def mover_localidade_zona(localidade_id: int, zona_id: int = Form(...), usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    localidade = db.get(Localidade, localidade_id); zona = db.get(Zona, zona_id)
    if not localidade or not zona or not zona.ativo:
        return RedirectResponse("/admin/zonas?erro=Bairro ou zona inválidos", status_code=303)
    vinculo = db.query(AreaLocalidade).filter(AreaLocalidade.localidade_id == localidade_id).first()
    if vinculo: vinculo.area_id = zona_id
    else: db.add(AreaLocalidade(area_id=zona_id, localidade_id=localidade_id))
    db.query(Indicacao).filter(Indicacao.localidade_id == localidade_id).update({Indicacao.area_id: zona_id, Indicacao.zona: zona.nome}, synchronize_session=False)
    db.commit()
    return RedirectResponse("/admin/zonas?ok=Bairro movido para a zona correta", status_code=303)


@app.post("/admin/zonas")
def zona_criar(nome: str = Form(...), usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    nome = nome.strip()
    if not nome:
        return RedirectResponse("/admin/zonas?erro=Informe o nome da zona", status_code=303)
    if db.query(Zona).filter(func.lower(Zona.nome) == nome.lower()).first():
        return RedirectResponse("/admin/zonas?erro=Essa zona já está cadastrada", status_code=303)
    db.add(Zona(nome=nome, ativo=1))
    db.commit()
    return RedirectResponse("/admin/zonas?ok=Zona cadastrada", status_code=303)


@app.post("/admin/zonas/{zona_id}/editar")
def zona_editar(zona_id: int, nome: str = Form(...), usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    zona = db.get(Zona, zona_id)
    if not zona:
        raise HTTPException(status_code=404, detail="Zona não encontrada")
    nome_novo = nome.strip()
    duplicada = db.query(Zona).filter(func.lower(Zona.nome) == nome_novo.lower(), Zona.id != zona_id).first()
    if not nome_novo or duplicada:
        return RedirectResponse("/admin/zonas?erro=Nome inválido ou já cadastrado", status_code=303)
    nome_antigo = zona.nome
    zona.nome = nome_novo
    # Mantém usuários e indicações históricas coerentes quando o nome da zona é alterado.
    db.query(Usuario).filter(Usuario.zona == nome_antigo).update({Usuario.zona: nome_novo}, synchronize_session=False)
    db.query(Indicacao).filter(Indicacao.zona == nome_antigo).update({Indicacao.zona: nome_novo}, synchronize_session=False)
    db.commit()
    return RedirectResponse("/admin/zonas?ok=Zona atualizada", status_code=303)


@app.post("/admin/zonas/{zona_id}/status")
def zona_status(zona_id: int, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    zona = db.get(Zona, zona_id)
    if not zona:
        raise HTTPException(status_code=404, detail="Zona não encontrada")
    if zona.ativo and db.query(Zona).filter(Zona.ativo == 1).count() <= 1:
        return RedirectResponse("/admin/zonas?erro=É necessário manter pelo menos uma zona ativa", status_code=303)
    zona.ativo = 0 if zona.ativo else 1
    db.commit()
    return RedirectResponse("/admin/zonas", status_code=303)



@app.get("/admin/catalogo", response_class=HTMLResponse)
def admin_catalogo(request: Request, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    categorias = db.query(Categoria).order_by(Categoria.nome).all()
    itens = db.query(CatalogoItem).order_by(CatalogoItem.nome).all()
    por_categoria = {}
    for i in itens:
        por_categoria.setdefault(i.categoria_id, []).append(i)
    return templates.TemplateResponse("catalogo.html", {"request":request,"usuario":usuario,"categorias":categorias,"por_categoria":por_categoria})

@app.post("/admin/catalogo/categoria")
def criar_categoria(nome: str = Form(...), usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario); nome=nome.strip()
    if nome and not db.query(Categoria).filter(func.lower(Categoria.nome)==nome.lower()).first():
        db.add(Categoria(nome=nome,ativo=1)); db.commit()
    return RedirectResponse("/admin/catalogo",303)

@app.post("/admin/catalogo/categoria/{categoria_id}/toggle")
def toggle_categoria(categoria_id: int, usuario: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    exigir_admin(usuario)
    categoria = db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    categoria.ativo = 0 if categoria.ativo else 1
    db.commit()
    estado = "ativada" if categoria.ativo else "desativada"
    return RedirectResponse(f"/admin/catalogo?ok=Categoria {quote_plus(categoria.nome)} {estado}", status_code=303)

@app.post("/admin/catalogo/item")
def criar_catalogo_item(categoria_id:int=Form(...), nome:str=Form(...), usuario:Usuario=Depends(usuario_logado), db:Session=Depends(get_db)):
    exigir_admin(usuario); nome=nome.strip()
    if db.get(Categoria,categoria_id) and nome:
        existe=db.query(CatalogoItem).filter(CatalogoItem.categoria_id==categoria_id,func.lower(CatalogoItem.nome)==nome.lower()).first()
        if not existe: db.add(CatalogoItem(categoria_id=categoria_id,nome=nome,ativo=1)); db.commit()
    return RedirectResponse("/admin/catalogo",303)

@app.get("/catalogo/solicitar", response_class=HTMLResponse)
def solicitar_catalogo_form(request:Request, usuario:Usuario=Depends(usuario_logado), db:Session=Depends(get_db)):
    categorias=db.query(Categoria).filter(Categoria.ativo==1).order_by(Categoria.nome).all()
    return templates.TemplateResponse("solicitar_catalogo.html",{"request":request,"usuario":usuario,"categorias":categorias})

@app.post("/catalogo/solicitar")
def solicitar_catalogo(categoria_sugerida:str=Form(...), item_sugerido:str=Form(...), observacao:str=Form(""), usuario:Usuario=Depends(usuario_logado), db:Session=Depends(get_db)):
    db.add(SolicitacaoCatalogo(usuario_id=usuario.id,categoria_sugerida=categoria_sugerida.strip(),item_sugerido=item_sugerido.strip(),observacao=observacao.strip(),status="Pendente"))
    db.commit()
    return RedirectResponse("/catalogo/solicitar?ok=1",303)

@app.get("/admin/solicitacoes-catalogo", response_class=HTMLResponse)
def solicitacoes_catalogo(request:Request, usuario:Usuario=Depends(usuario_logado), db:Session=Depends(get_db)):
    exigir_admin(usuario)
    sols=db.query(SolicitacaoCatalogo).order_by(SolicitacaoCatalogo.id.desc()).all()
    usuarios={u.id:u for u in db.query(Usuario).all()}
    categorias=db.query(Categoria).order_by(Categoria.nome).all()
    return templates.TemplateResponse("solicitacoes_catalogo.html",{"request":request,"usuario":usuario,"solicitacoes":sols,"usuarios":usuarios,"categorias":categorias})

@app.post("/admin/solicitacoes-catalogo/{sid}/aprovar")
def aprovar_solicitacao(sid:int,categoria_id:int=Form(0),nome_item:str=Form(""),usuario:Usuario=Depends(usuario_logado),db:Session=Depends(get_db)):
    exigir_admin(usuario); s=db.get(SolicitacaoCatalogo,sid)
    if not s: raise HTTPException(404)
    cat=db.get(Categoria,categoria_id) if categoria_id else None
    if not cat:
        cat=db.query(Categoria).filter(func.lower(Categoria.nome)==s.categoria_sugerida.lower()).first()
        if not cat:
            cat=Categoria(nome=s.categoria_sugerida,ativo=1);db.add(cat);db.flush()
    nome=(nome_item or s.item_sugerido).strip()
    existe=db.query(CatalogoItem).filter(CatalogoItem.categoria_id==cat.id,func.lower(CatalogoItem.nome)==nome.lower()).first()
    if not existe: db.add(CatalogoItem(categoria_id=cat.id,nome=nome,ativo=1))
    s.status="Aprovada";db.commit()
    return RedirectResponse("/admin/solicitacoes-catalogo",303)

@app.post("/admin/solicitacoes-catalogo/{sid}/recusar")
def recusar_solicitacao(sid:int,usuario:Usuario=Depends(usuario_logado),db:Session=Depends(get_db)):
    exigir_admin(usuario);s=db.get(SolicitacaoCatalogo,sid)
    if s: s.status="Recusada";db.commit()
    return RedirectResponse("/admin/solicitacoes-catalogo",303)

@app.get("/saude")
def saude():
    return {"status": "ok", "sistema": "LokaFest", "versao": APP_VERSION}
