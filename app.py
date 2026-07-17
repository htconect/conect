from datetime import datetime, date, time, timedelta, timezone
from typing import Optional
from pathlib import Path
from io import BytesIO, StringIO
import shutil
import csv
import uuid
import hashlib
import re
import zipfile
from xml.sax.saxutils import escape as xml_escape
from difflib import SequenceMatcher
from urllib.parse import quote, urlparse, parse_qsl, urlencode, urlunparse

from fastapi import FastAPI, Depends, Form, Request, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, text, inspect, or_

from config import APP_NOME, SECRET_KEY, ADMIN_NOME, ADMIN_SENHA
from database import Base, engine, get_db, SessionLocal
from models import Agenda, CampoEmpresa, CampoGlobal, Cliente, EnderecoCliente, Contrato, Empresa, EquipamentoCliente, Pagamento, \
    ProdutoServico, ReservaItem, Solicitacao, UsuarioEmpresa, ContaFinanceira, LancamentoBanco, \
    LancamentoManualFinanceiro
from seed import inicializar_dados
from utils import limpar_identificador, somar_horas, somar_minutos, hora_meia_em_meia_valida, texto_para_float, \
    cpf_valido, cnpj_valido, aplicar_variaveis_mensagem

from fastapi.templating import Jinja2Templates

class ControleAcessoMiddleware:
    """Bloqueia a entrada nos módulos sem esconder cards, alertas ou pendências."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "")
            session = scope.get("session") or {}
            if session.get("empresa_id") and not session.get("acesso_total"):
                area = self.area_da_rota(path)
                acessos = session.get("acessos") or {}
                if area and not acessos.get(area, False):
                    response = RedirectResponse(f"/painel/acesso-negado?area={area}", status_code=303)
                    await response(scope, receive, send)
                    return
        await self.app(scope, receive, send)

    @staticmethod
    def area_da_rota(path: str):
        # A permissão protege o módulo de destino. Pendências e dados exibidos no painel continuam visíveis.
        if path == "/painel/agenda" or path.startswith("/painel/agenda/"):
            return "agenda"
        if path == "/painel/reservas" or path.startswith("/painel/reservas/"):
            return "operacao"
        if path == "/painel/clientes" or path.startswith("/painel/cliente/"):
            return "buscar_cliente"
        if path == "/painel/financeiro" or path.startswith("/painel/financeiro/"):
            return "financeiro"
        if path == "/painel/relatorios" or path.startswith("/painel/relatorios/"):
            return "relatorios"
        prefixos_cadastro = (
            "/painel/configuracoes", "/painel/produtos", "/painel/produto/",
            "/painel/contratos", "/painel/contrato/", "/painel/disponibilidade"
        )
        if any(path == p or path.startswith(p) for p in prefixos_cadastro):
            return "cadastros"
        return None


app = FastAPI(title=APP_NOME)
app.add_middleware(ControleAcessoMiddleware)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
Path("static/uploads/logos").mkdir(parents=True, exist_ok=True)

FUSO_EMPRESA = timezone(timedelta(hours=-3))


def agora_utc() -> datetime:
    """Salva horários em UTC para não depender do fuso do servidor."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def redirect_preservando_filtros(request: Request, fallback: str = "/painel/financeiro",
                                 extras: dict | None = None) -> RedirectResponse:
    url = request.headers.get("referer") or fallback
    if extras:
        partes = urlparse(url)
        qs = dict(parse_qsl(partes.query, keep_blank_values=True))
        qs.update({k: str(v) for k, v in extras.items()})
        url = urlunparse((partes.scheme, partes.netloc, partes.path, partes.params, urlencode(qs), partes.fragment))
    return RedirectResponse(url, status_code=303)


def datahora_local(valor):
    """Mostra horários no fuso do Brasil/RJ."""
    if not valor:
        return "-"
    try:
        return valor.replace(tzinfo=timezone.utc).astimezone(FUSO_EMPRESA).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "-"


templates.env.filters["datahora_local"] = datahora_local


def valor_falta(item) -> float:
    return max(float(getattr(item, "valor", 0) or 0) - float(getattr(item, "valor_pago", 0) or 0), 0)


def resumo_financeiro(itens):
    total = sum(float(getattr(i, "valor", 0) or 0) for i in itens)
    recebido = sum(float(getattr(i, "valor_pago", 0) or 0) for i in itens)
    falta = sum(valor_falta(i) for i in itens)
    return {"qtd": len(itens), "total": total, "recebido": recebido, "falta": falta}


def pagamento_sem_conciliar(item) -> bool:
    return any(not getattr(p, "conciliado_em", None) for p in getattr(item, "pagamentos", []) or [])


def somente_lancamentos_financeiros(itens):
    # Financeiro recebe os contratos que já possuem pelo menos uma linha de pagamento.
    # Cada pagamento fica listado dentro do card para conciliação com banco/cartão/dinheiro.
    return [i for i in itens if getattr(i, "pagamentos", None)]


def pagamentos_pendentes_conciliacao(itens):
    return [p for i in itens for p in (getattr(i, "pagamentos", []) or []) if not getattr(p, "conciliado_em", None)]


def recalcular_pagamento_solicitacao(db: Session, item: Solicitacao):
    # Fonte da verdade do financeiro: tabela de pagamentos.
    # O campo Solicitacao.valor_pago é apenas um resumo/cache usado nos cards.
    # Antes havia casos em que o card mostrava falta receber mesmo com todos
    # os pagamentos lançados/conciliados, porque esse resumo ficou desatualizado.
    db.flush()
    total_pago = sum(
        (p.valor or 0) for p in db.query(Pagamento).filter_by(empresa_id=item.empresa_id, solicitacao_id=item.id).all())
    item.valor_pago = total_pago
    item.sinal_recebido = total_pago > 0
    if total_pago <= 0:
        item.pagamento_confirmado_em = None
    elif not item.pagamento_confirmado_em:
        item.pagamento_confirmado_em = agora_utc()
    return total_pago


def sincronizar_pagamentos_solicitacoes(db: Session, solicitacoes):
    """Recalcula o resumo financeiro exibido nas telas operacionais/detalhe."""
    alterou = False
    vistos = set()
    for item in solicitacoes or []:
        if not item or item.id in vistos:
            continue
        vistos.add(item.id)
        total_pago = sum((p.valor or 0) for p in
                         db.query(Pagamento).filter_by(empresa_id=item.empresa_id, solicitacao_id=item.id).all())
        if round(float(item.valor_pago or 0), 2) != round(float(total_pago or 0), 2):
            item.valor_pago = total_pago
            item.sinal_recebido = total_pago > 0
            if total_pago <= 0:
                item.pagamento_confirmado_em = None
            elif not item.pagamento_confirmado_em:
                item.pagamento_confirmado_em = agora_utc()
            alterou = True
    if alterou:
        db.commit()
    return alterou


def existe_pagamento_conciliado(item: Solicitacao) -> bool:
    return any(getattr(p, "conciliado_em", None) for p in (getattr(item, "pagamentos", None) or []))


def classe_alerta_contrato(status: str) -> str:
    if status in {"pre_reserva"}:
        return "card-rascunho"
    if status in {"aguardando_aceite", "contrato_enviado"}:
        return "card-nao-aceito"
    return ""


templates.env.globals["classe_alerta_contrato"] = classe_alerta_contrato


def validar_total_pagamentos(item: Solicitacao, total_pago: float):
    if item.valor and total_pago > float(item.valor or 0) + 0.009:
        raise HTTPException(400, "A soma dos pagamentos não pode ser maior que o total do contrato.")


def status_reserva_confirmada(status: str) -> bool:
    return status in {"aceito", "aguardando_pagamento", "reserva_confirmada"}


def status_em_contrato(status: str) -> bool:
    return status in {"pre_reserva", "aguardando_aceite", "contrato_enviado"}


def reserva_tem_itens(item) -> bool:
    return bool(getattr(item, "itens", None))


def reserva_pode_aprovar(item) -> bool:
    """Contrato só pode ser aprovado quando já existe pelo menos um item."""
    return reserva_tem_itens(item)


def corrigir_reservas_aprovadas_sem_itens(db: Session):
    """
    Corrige reservas que ficaram em status aprovado/confirmado sem itens.
    Esse estado não é permitido: a próxima ação correta é adicionar itens.
    """
    alterou = False
    reservas = db.query(Solicitacao).filter(
        Solicitacao.status.in_(["reserva_confirmada", "aguardando_pagamento"])).all()
    for item in reservas:
        qtd_itens = db.query(ReservaItem).filter_by(empresa_id=item.empresa_id, solicitacao_id=item.id).count()
        if qtd_itens == 0:
            item.status = "pre_reserva"
            item.aprovado_em = None
            item.sinal_recebido = False
            item.valor_pago = 0
            item.pagamento_confirmado_em = None
            db.query(Pagamento).filter_by(empresa_id=item.empresa_id, solicitacao_id=item.id).delete()
            alterou = True
    if alterou:
        db.commit()


def corrigir_valores_teste(db: Session):
    """
    Corrige valores inflados em bases de teste geradas por máscara monetária antiga.
    Ex.: 310.000,00 salvo como 310000.00 volta para 310.00.
    Regra conservadora para este projeto: valores operacionais acima de 50 mil,
    quando múltiplos de 1000, são reduzidos em 1000.
    """

    def ajustar(valor):
        try:
            numero = float(valor or 0)
        except Exception:
            return valor
        if numero >= 50000 and numero % 1000 == 0:
            return numero / 1000
        return numero

    alterou = False
    for item in db.query(Solicitacao).all():
        novo_valor = ajustar(item.valor)
        novo_sinal = ajustar(item.sinal)
        novo_pago = ajustar(item.valor_pago)
        if (novo_valor, novo_sinal, novo_pago) != (item.valor, item.sinal, item.valor_pago):
            item.valor, item.sinal, item.valor_pago = novo_valor, novo_sinal, novo_pago
            alterou = True

    for linha in db.query(ReservaItem).all():
        novo_unitario = ajustar(linha.valor_unitario)
        novo_total = ajustar(linha.valor_total)
        if (novo_unitario, novo_total) != (linha.valor_unitario, linha.valor_total):
            linha.valor_unitario, linha.valor_total = novo_unitario, novo_total
            alterou = True

    for produto in db.query(ProdutoServico).all():
        novo_base = ajustar(produto.valor_base)
        if novo_base != produto.valor_base:
            produto.valor_base = novo_base
            alterou = True

    for pagamento in db.query(Pagamento).all():
        novo_pagamento = ajustar(pagamento.valor)
        if novo_pagamento != pagamento.valor:
            pagamento.valor = novo_pagamento
            alterou = True

    if alterou:
        db.commit()


def recalcular_valores_reservas(db: Session):
    """Mantém o valor da reserva igual à soma dos itens e corrige bases antigas."""
    alterou = False
    for item in db.query(Solicitacao).all():
        total_itens = sum((linha.valor_total or 0) for linha in item.itens)
        if total_itens > 0 and round(float(item.valor or 0), 2) != round(float(total_itens), 2):
            item.valor = total_itens
            # Valor pago não pode ficar maior que o total da reserva.
            if item.valor_pago and item.valor_pago > item.valor:
                item.valor_pago = item.valor
            alterou = True
    if alterou:
        db.commit()


def limpar_agenda_operacional(db: Session):
    """
    Remove duplicidade operacional.
    Regra atual: a reserva nasce com ENTREGA.
    A RETIRADA nasce ao concluir a entrega, exceto quando o cliente exigiu retirada obrigatória.
    """
    alterou = False
    reservas = db.query(Solicitacao).all()
    for reserva in reservas:
        eventos = (
            db.query(Agenda)
            .filter_by(empresa_id=reserva.empresa_id, solicitacao_id=reserva.id)
            .order_by(Agenda.id)
            .all()
        )
        entregas = [e for e in eventos if (e.tipo_evento or "entrega") == "entrega"]
        retiradas = [e for e in eventos if e.tipo_evento == "retirada"]

        if not entregas and eventos:
            eventos[0].tipo_evento = "entrega"
            entregas = [eventos[0]]
            alterou = True

        if entregas:
            principal = entregas[0]
            principal.tipo_evento = "entrega"
            principal.data = reserva.data_evento
            principal.hora_inicio = reserva.hora_inicio
            principal.hora_fim = reserva.hora_fim
            principal.titulo = f"{nome_item_reserva(reserva)} - {reserva.cliente.nome if reserva.cliente else 'Cliente'}"
            principal.bairro = reserva.bairro
            for duplicado in entregas[1:]:
                db.delete(duplicado)
                alterou = True

        if retirada_obrigatoria_ativa(reserva):
            criar_ou_atualizar_retirada_obrigatoria(db, reserva)
            alterou = True
            if len(retiradas) > 1:
                for duplicada in retiradas[1:]:
                    db.delete(duplicada)
                    alterou = True
            continue

        # Retiradas comuns só devem existir depois que a entrega foi concluída.
        entrega_concluida = bool(entregas and entregas[0].status_operacional == "concluido")
        if not entrega_concluida:
            for retirada in retiradas:
                db.delete(retirada)
                alterou = True
        elif len(retiradas) > 1:
            for duplicada in retiradas[1:]:
                db.delete(duplicada)
                alterou = True

    if alterou:
        db.commit()

def janela_uma_hora(hora) -> str:
    if not hora:
        return "-"
    fim = somar_horas(hora, 1)
    if not fim:
        return hora.strftime("%H:%M")
    return f"{hora.strftime('%H:%M')} às {fim.strftime('%H:%M')}"


def ajustar_hora_texto(hora_texto, horas: int) -> str:
    """Recebe HH:MM e devolve HH:MM somando/subtraindo horas."""
    try:
        if not hora_texto or hora_texto == "--":
            return "-"
        base = datetime.strptime(str(hora_texto), "%H:%M")
        return (base + timedelta(hours=int(horas))).strftime("%H:%M")
    except Exception:
        return "-"


def periodo_semana_atual():
    hoje = date.today()
    inicio = hoje - timedelta(days=hoje.weekday())
    fim = inicio + timedelta(days=6)
    return inicio, fim


def moeda_br(valor) -> str:
    try:
        numero = float(valor or 0)
    except Exception:
        numero = 0.0
    texto = f"{numero:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


templates.env.filters["moeda_br"] = moeda_br
templates.env.globals["status_reserva_confirmada"] = status_reserva_confirmada
templates.env.globals["status_em_contrato"] = status_em_contrato
templates.env.globals["janela_uma_hora"] = janela_uma_hora
templates.env.globals["ajustar_hora_texto"] = ajustar_hora_texto


def _limpar_tel_whatsapp(valor: str) -> str:
    tel = "".join(ch for ch in str(valor or "") if ch.isdigit())
    if not tel:
        return ""
    if tel.startswith("55"):
        return tel
    return "55" + tel


def _link_absoluto(request: Request, nome_rota: str, **params) -> str:
    return str(request.url_for(nome_rota, **params))


def linhas_endereco_reserva(item: Solicitacao) -> list[str]:
    """Monta o endereço completo usando dados da reserva e do cadastro do cliente."""
    cliente = item.cliente
    local_nome = (item.local_nome or "").strip()
    endereco = (item.local or cliente.endereco or "").strip()
    numero = (cliente.numero or "").strip()
    complemento = (cliente.complemento or "").strip()
    bairro = (item.bairro or cliente.bairro or "").strip()
    cidade = (cliente.cidade or "").strip()
    estado = (cliente.estado or "").strip()
    cep = (cliente.cep or "").strip()
    referencia = (item.observacoes or cliente.observacoes or "").strip()

    linhas = []
    if local_nome:
        linhas.append(f"*Local:* {local_nome}")

    endereco_partes = []
    if endereco:
        endereco_partes.append(endereco)
    if numero:
        endereco_partes.append(f"nº {numero}")
    if complemento:
        endereco_partes.append(complemento)
    if endereco_partes:
        linhas.append(f"*Endereço:* {', '.join(endereco_partes)}")

    if bairro:
        linhas.append(f"*Bairro:* {bairro}")

    cidade_uf = " / ".join([p for p in [cidade, estado] if p])
    if cidade_uf:
        linhas.append(f"*Cidade:* {cidade_uf}")

    if cep:
        linhas.append(f"*CEP:* {cep}")

    if referencia:
        linhas.append(f"*Observação:* {referencia}")

    if not linhas:
        linhas.append("*Endereço:* -")

    return linhas


def linhas_informacoes_preenchidas_contrato(item: Solicitacao, formato: str = "texto") -> list[str]:
    """Lista todas as informações preenchidas do contrato/reserva para PDF e WhatsApp.
    formato='whatsapp' usa negrito com *campo*.
    """
    cliente = item.cliente

    def fmt_data(v):
        return v.strftime("%d/%m/%Y") if v else ""

    def fmt_hora(v):
        return v.strftime("%H:%M") if v else ""

    def add(linhas, rotulo, valor):
        if valor is None:
            return
        valor_txt = str(valor).strip()
        if not valor_txt:
            return
        if formato == "whatsapp":
            linhas.append(f"*{rotulo}:* {valor_txt}")
        else:
            linhas.append(f"{rotulo}: {valor_txt}")

    linhas = []

    add(linhas, "Cliente", getattr(cliente, "nome", ""))
    add(linhas, "Telefone", (getattr(cliente, "telefone", "") or getattr(cliente, "identificador", "")))
    add(linhas, "CPF", getattr(cliente, "cpf", ""))
    add(linhas, "CNPJ", getattr(cliente, "cnpj", ""))
    add(linhas, "E-mail", getattr(cliente, "email", ""))
    add(linhas, "Nascimento", fmt_data(getattr(cliente, "data_nascimento", None)))

    add(linhas, "Data do evento", fmt_data(item.data_evento))
    add(linhas, "Hora de início", fmt_hora(item.hora_inicio))
    add(linhas, "Hora de fim", fmt_hora(item.hora_fim))

    add(linhas, "Nome do local", item.local_nome)
    add(linhas, "Endereço do evento", item.local)
    add(linhas, "Bairro do evento", item.bairro)
    add(linhas, "Acesso ao local", item.acesso_local)
    add(linhas, "Responsável no local", item.local_responsavel_nome)
    add(linhas, "Telefone do responsável", item.local_responsavel_telefone)

    add(linhas, "Endereço do evento", item.local or getattr(cliente, "endereco", ""))
    add(linhas, "Número", getattr(cliente, "numero", ""))
    add(linhas, "Complemento", getattr(cliente, "complemento", ""))
    add(linhas, "Bairro do cliente", getattr(cliente, "bairro", ""))
    cidade_uf = " - ".join([p for p in [getattr(cliente, "cidade", ""), getattr(cliente, "estado", "")] if p])
    add(linhas, "Cidade/UF", cidade_uf)
    add(linhas, "CEP", getattr(cliente, "cep", ""))
    add(linhas, "Observações do cliente", getattr(cliente, "observacoes", ""))
    add(linhas, "Observações da reserva", item.observacoes)

    add(linhas, "Valor total", f"R$ {moeda_br(item.valor or 0)}")
    add(linhas, "Valor recebido", f"R$ {moeda_br(item.valor_pago or 0)}")
    add(linhas, "Sinal previsto", f"R$ {moeda_br(item.sinal or 0)}")
    add(linhas, "Falta", f"R$ {moeda_br(max((item.valor or 0) - (item.valor_pago or 0), 0))}")

    return linhas


def _resumo_reserva_whatsapp(empresa: Empresa, item: Solicitacao, itens_reserva) -> list[str]:
    """Monta o resumo principal da reserva para mensagens de WhatsApp."""
    total = float(item.valor or 0)
    pago = float(item.valor_pago or 0)
    falta = max(total - pago, 0)
    data_txt = item.data_evento.strftime("%d/%m/%Y") if item.data_evento else "-"
    hora_txt = item.hora_inicio.strftime("%H:%M") if item.hora_inicio else "-"

    equipamentos = []
    if itens_reserva:
        for ri in itens_reserva:
            prefixo = f"{ri.quantidade or 1}x " if (ri.quantidade or 1) > 1 else ""
            equipamentos.append(f"• {prefixo}{ri.nome}")
    elif item.produto:
        equipamentos.append(f"• {item.produto.nome}")
    else:
        equipamentos.append("• Itens da reserva")

    endereco_linhas = linhas_endereco_reserva(item)
    endereco_texto = "\n".join(
        l.replace("*Endereço:* ", "").replace("*Local:* ", "").replace("*Bairro:* ", "Bairro: ")
        for l in endereco_linhas
    )

    return [
        f"*{empresa.nome or 'Karaokê RJ'}*",
        "",
        f"Cliente: {item.cliente.nome if item.cliente else '-'}",
        "",
        "📅 Entrega",
        f"{data_txt} às {hora_txt}",
        "",
        "📍 Local",
        endereco_texto or "-",
        "",
        "🎤 Equipamentos",
        *equipamentos,
        "",
        "💰 Financeiro",
        f"Total: R$ {moeda_br(total)}",
        f"Pago: R$ {moeda_br(pago)}",
        f"Saldo: R$ {moeda_br(falta)}",
    ]


def montar_mensagem_whatsapp_aceite(request: Request, empresa: Empresa, item: Solicitacao, db: Session) -> str:
    """Mensagem para o cliente aceitar a reserva. Usa o texto do cadastro da empresa e complementos do sistema."""
    link_aceite = _link_absoluto(request, "contrato_cliente", slug=empresa.slug, solicitacao_id=item.id)
    cliente_nome = item.cliente.nome if item.cliente else "cliente"

    texto_base = aplicar_variaveis_mensagem(
        mensagens_empresa(empresa).get("aceite", ""),
        link=link_aceite,
        empresa=empresa.nome,
        cliente=cliente_nome,
        valor_sinal=moeda_br(item.sinal or 0),
        pix=empresa.pix_copia_cola or "",
    ).strip()

    linhas = [texto_base] if texto_base else []

    if getattr(empresa, "exige_sinal", False):
        linhas.extend([
            "",
            "Para concluir a confirmação, realize o PIX do sinal para a chave abaixo e envie o comprovante.",
            "",
            f"PIX: {empresa.pix_copia_cola or '-'}",
            "",
            "Assim que o aceite do pré-contrato e a confirmação do pagamento do sinal forem concluídos, sua reserva será efetivada.",
        ])
    else:
        linhas.extend([
            "",
            "Assim que o aceite do pré-contrato for concluído, sua reserva será efetivada.",
        ])

    linhas.extend([
        "",
        "Em seguida, você receberá:",
        "• O resumo da reserva;",
        "• O contrato em PDF;",
        "• As cláusulas do contrato para sua consulta.",
    ])

    return "\n".join(linhas).strip()


def montar_mensagem_whatsapp_contrato(request: Request, empresa: Empresa, item: Solicitacao, db: Session) -> str:
    """Mensagem enviada somente depois do aceite, com o link do contrato final."""
    itens_reserva = db.query(ReservaItem).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).all()
    link_contrato = _link_absoluto(request, "contrato_cliente_pdf", slug=empresa.slug, solicitacao_id=item.id)
    link_clausulas = _link_absoluto(request, "contrato_cliente_clausulas", slug=empresa.slug, solicitacao_id=item.id)

    linhas = _resumo_reserva_whatsapp(empresa, item, itens_reserva)
    linhas.extend([
        "",
        "📄 Contrato final:",
        link_contrato,
        "",
        "📄 Cláusulas do contrato:",
        link_clausulas,
        "",
    ])

    mensagem_final = mensagens_empresa(empresa).get("confirmacao", "").strip()
    if mensagem_final:
        linhas.append(mensagem_final)

    return "\n".join(linhas).strip()



MENSAGEM_OPERACAO_PREPARACAO_APROVADA = (
    "Olá, {{cliente}}.\n\n"
    "Estamos nos preparando para sair e, em breve, iniciaremos o deslocamento até você.\n\n"
    "Nossa previsão de chegada é entre {{hora_previsao_inicio}} e {{hora_previsao_fim}}.\n\n"
    "Caso esse horário não seja adequado ou aconteça algum imprevisto, por favor nos avise.\n\n"
    "Se houver qualquer alteração em nossa programação, entraremos em contato imediatamente.\n\n"
    "Equipe {{empresa}}"
)

MENSAGEM_OPERACAO_A_CAMINHO_APROVADA = (
    "Olá, {{cliente}}.\n\n"
    "Nossa equipe já está a caminho.\n\n"
    "Em breve estaremos no local informado.\n\n"
    "Caso precise falar conosco, basta responder esta mensagem.\n\n"
    "Equipe {{empresa}}"
)

def garantir_colunas_novas():
    """Migração simples para bases locais/teste já existentes."""
    insp = inspect(engine)
    try:
        tabelas = insp.get_table_names()
    except Exception:
        return
    if "empresas" not in tabelas:
        return

    def colunas(tabela):
        return {c["name"] for c in insp.get_columns(tabela)}

    comandos = []

    if "usuarios_empresa" not in tabelas:
        comandos.append("""
        CREATE TABLE usuarios_empresa (
            id INTEGER PRIMARY KEY,
            empresa_id INTEGER NOT NULL,
            nome VARCHAR(120) NOT NULL,
            usuario VARCHAR(80) NOT NULL,
            senha VARCHAR(120) NOT NULL,
            ativo BOOLEAN DEFAULT true,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(empresa_id) REFERENCES empresas (id)
        )
        """)
        comandos.append("CREATE INDEX IF NOT EXISTS ix_usuarios_empresa_usuario ON usuarios_empresa (usuario)")
    cols_emp = colunas("empresas")
    if "pix_copia_cola" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN pix_copia_cola TEXT")
    if "exige_sinal" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN exige_sinal BOOLEAN DEFAULT false")
    if "suporte_inicio" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN suporte_inicio VARCHAR(5)")
    if "suporte_fim" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN suporte_fim VARCHAR(5)")
    if "mostrar_suporte_contrato" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN mostrar_suporte_contrato BOOLEAN DEFAULT false")
    if "logo_url" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN logo_url VARCHAR(300)")
    if "tema" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN tema VARCHAR(30) DEFAULT 'azul'")
    if "mensagem_reserva" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN mensagem_reserva TEXT")
    if "mensagem_preparacao" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN mensagem_preparacao TEXT")
    if "mensagem_a_caminho" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN mensagem_a_caminho TEXT")
    if "mensagem_localizacao" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN mensagem_localizacao TEXT")
    if "logo_idb_url" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN logo_idb_url VARCHAR(300)")
    if "mensagem_hora_fim" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN mensagem_hora_fim TEXT")
    if "mostrar_mensagem_hora_fim" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN mostrar_mensagem_hora_fim BOOLEAN DEFAULT true")
    if "mensagem_aceite" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN mensagem_aceite TEXT")
    if "mensagem_pagamento" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN mensagem_pagamento TEXT")
    if "mensagem_confirmacao" not in cols_emp:
        comandos.append("ALTER TABLE empresas ADD COLUMN mensagem_confirmacao TEXT")

    if "clientes" in tabelas:
        cols_cli = colunas("clientes")
        if "data_nascimento" not in cols_cli:
            comandos.append("ALTER TABLE clientes ADD COLUMN data_nascimento DATE")

    if "produtos_servicos" in tabelas:
        cols_prod = colunas("produtos_servicos")
        if "duracao_minutos" not in cols_prod:
            comandos.append("ALTER TABLE produtos_servicos ADD COLUMN duracao_minutos INTEGER DEFAULT 240")
        if "prazo_retirada_dias" not in cols_prod:
            comandos.append("ALTER TABLE produtos_servicos ADD COLUMN prazo_retirada_dias INTEGER DEFAULT 1")

    if "solicitacoes" in tabelas:
        cols_sol = colunas("solicitacoes")
        if "valor_pago" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN valor_pago FLOAT DEFAULT 0")
        if "sinal_recebido" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN sinal_recebido BOOLEAN DEFAULT false")
        if "pagamento_confirmado_em" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN pagamento_confirmado_em DATETIME")
        if "aprovado_em" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN aprovado_em DATETIME")
        if "cancelado_em" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN cancelado_em DATETIME")
        if "retirada_obrigatoria" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN retirada_obrigatoria BOOLEAN DEFAULT false")
        if "retirada_data" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN retirada_data DATE")
        if "retirada_hora" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN retirada_hora TIME")
        if "local_nome" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN local_nome VARCHAR(160)")
        if "local_responsavel_nome" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN local_responsavel_nome VARCHAR(160)")
        if "local_responsavel_telefone" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN local_responsavel_telefone VARCHAR(40)")
        if "retirada_responsavel_nome" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN retirada_responsavel_nome VARCHAR(160)")
        if "retirada_responsavel_telefone" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN retirada_responsavel_telefone VARCHAR(40)")

        if "acesso_local" not in cols_sol:
            comandos.append("ALTER TABLE solicitacoes ADD COLUMN acesso_local VARCHAR(40)")

    if "pagamentos" in tabelas:
        cols_pag = colunas("pagamentos")
        if "usuario_registro" not in cols_pag:
            comandos.append("ALTER TABLE pagamentos ADD COLUMN usuario_registro VARCHAR(120)")
        if "conciliado_por" not in cols_pag:
            comandos.append("ALTER TABLE pagamentos ADD COLUMN conciliado_por VARCHAR(120)")
        if "conciliado_em" not in cols_pag:
            comandos.append("ALTER TABLE pagamentos ADD COLUMN conciliado_em DATETIME")

    if "usuarios_empresa" in tabelas:
        cols_usu = colunas("usuarios_empresa")
        novas_permissoes = {
            "acesso_agenda": "BOOLEAN DEFAULT false",
            "acesso_operacao": "BOOLEAN DEFAULT false",
            "acesso_buscar_cliente": "BOOLEAN DEFAULT false",
            "acesso_financeiro": "BOOLEAN DEFAULT false",
            "acesso_cadastros": "BOOLEAN DEFAULT false",
            "acesso_relatorios": "BOOLEAN DEFAULT false",
            "acesso_equipe_1": "BOOLEAN DEFAULT true",
            "acesso_equipe_2": "BOOLEAN DEFAULT false",
        }
        for coluna, tipo in novas_permissoes.items():
            if coluna not in cols_usu:
                comandos.append(f"ALTER TABLE usuarios_empresa ADD COLUMN {coluna} {tipo}")

    if "contas_financeiras" not in tabelas:
        comandos.append("""
        CREATE TABLE contas_financeiras (
            id INTEGER PRIMARY KEY,
            empresa_id INTEGER NOT NULL,
            nome VARCHAR(80) NOT NULL,
            tipo VARCHAR(20) DEFAULT 'banco',
            saldo_inicial FLOAT DEFAULT 0,
            ativa BOOLEAN DEFAULT true,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(empresa_id) REFERENCES empresas (id)
        )
        """)

    if "lancamentos_banco" not in tabelas:
        comandos.append("""
        CREATE TABLE lancamentos_banco (
            id INTEGER PRIMARY KEY,
            empresa_id INTEGER NOT NULL,
            conta_id INTEGER NOT NULL,
            data DATE NOT NULL,
            historico TEXT NOT NULL,
            documento VARCHAR(80),
            valor FLOAT DEFAULT 0,
            saldo FLOAT DEFAULT 0,
            categoria VARCHAR(20) DEFAULT 'aluguel',
            categoria_confirmada BOOLEAN DEFAULT false,
            pagamento_id INTEGER,
            hash_importacao VARCHAR(64),
            origem_importacao VARCHAR(120),
            ordem INTEGER DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(empresa_id) REFERENCES empresas (id),
            FOREIGN KEY(conta_id) REFERENCES contas_financeiras (id),
            FOREIGN KEY(pagamento_id) REFERENCES pagamentos (id)
        )
        """)

    if "lancamentos_banco" in tabelas:
        cols_lb = colunas("lancamentos_banco")
        if "hash_importacao" not in cols_lb:
            comandos.append("ALTER TABLE lancamentos_banco ADD COLUMN hash_importacao VARCHAR(64)")
        if "categoria_confirmada" not in cols_lb:
            comandos.append("ALTER TABLE lancamentos_banco ADD COLUMN categoria_confirmada BOOLEAN DEFAULT false")
        if "ordem" not in cols_lb:
            comandos.append("ALTER TABLE lancamentos_banco ADD COLUMN ordem INTEGER DEFAULT 0")

    if "lancamentos_manuais_financeiros" not in tabelas:
        comandos.append("""
        CREATE TABLE lancamentos_manuais_financeiros (
            id INTEGER PRIMARY KEY,
            empresa_id INTEGER NOT NULL,
            conta_id INTEGER NOT NULL,
            data DATE NOT NULL,
            descricao TEXT NOT NULL,
            valor FLOAT DEFAULT 0,
            categoria VARCHAR(20) DEFAULT 'empresa',
            tipo VARCHAR(20) DEFAULT 'real',
            recebido BOOLEAN DEFAULT false,
            pagamento_id INTEGER,
            ordem INTEGER DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(empresa_id) REFERENCES empresas (id),
            FOREIGN KEY(conta_id) REFERENCES contas_financeiras (id),
            FOREIGN KEY(pagamento_id) REFERENCES pagamentos (id)
        )
        """)

    if "lancamentos_manuais_financeiros" in tabelas:
        cols_lmf = colunas("lancamentos_manuais_financeiros")
        if "pagamento_id" not in cols_lmf:
            comandos.append("ALTER TABLE lancamentos_manuais_financeiros ADD COLUMN pagamento_id INTEGER")
        if "ordem" not in cols_lmf:
            comandos.append("ALTER TABLE lancamentos_manuais_financeiros ADD COLUMN ordem INTEGER DEFAULT 0")

    if "app_migrations" not in tabelas:
        comandos.append("""
        CREATE TABLE app_migrations (
            chave VARCHAR(120) PRIMARY KEY,
            executado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

    if "agenda" in tabelas:
        cols_ag = colunas("agenda")
        if "ordem_rota" not in cols_ag:
            comandos.append("ALTER TABLE agenda ADD COLUMN ordem_rota INTEGER DEFAULT 0")
        if "previsao_entrega" not in cols_ag:
            comandos.append("ALTER TABLE agenda ADD COLUMN previsao_entrega VARCHAR(5)")
        if "link_localizacao" not in cols_ag:
            comandos.append("ALTER TABLE agenda ADD COLUMN link_localizacao TEXT")
        if "tipo_evento" not in cols_ag:
            comandos.append("ALTER TABLE agenda ADD COLUMN tipo_evento VARCHAR(20) DEFAULT 'entrega'")
        if "status_operacional" not in cols_ag:
            comandos.append("ALTER TABLE agenda ADD COLUMN status_operacional VARCHAR(20) DEFAULT 'pendente'")
        if "observacoes_operacionais" not in cols_ag:
            comandos.append("ALTER TABLE agenda ADD COLUMN observacoes_operacionais TEXT")

    if comandos:
        with engine.begin() as conn:
            for comando in comandos:
                conn.execute(text(comando))


def atualizar_mensagem_previsao_padrao():
    """Copia uma única vez para o cadastro as mensagens aprovadas que estavam fixas nos botões da operação.

    Depois dessa migração, os botões Previsão e A caminho passam a usar o texto cadastrado
    na empresa. O controle por chave evita sobrescrever edições futuras feitas em Configurações.
    """
    chave_migracao = "20260706_mensagens_operacao_aprovadas"
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS app_migrations (
                    chave VARCHAR(120) PRIMARY KEY,
                    executado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            ja_executou = conn.execute(
                text("SELECT chave FROM app_migrations WHERE chave = :chave"),
                {"chave": chave_migracao},
            ).first()
            if ja_executou:
                return

            conn.execute(
                text("""
                    UPDATE empresas
                       SET mensagem_preparacao = :preparacao,
                           mensagem_a_caminho = :a_caminho
                """),
                {
                    "preparacao": MENSAGEM_OPERACAO_PREPARACAO_APROVADA,
                    "a_caminho": MENSAGEM_OPERACAO_A_CAMINHO_APROVADA,
                },
            )
            conn.execute(
                text("INSERT INTO app_migrations (chave) VALUES (:chave)"),
                {"chave": chave_migracao},
            )
    except Exception:
        pass

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    garantir_colunas_novas()
    atualizar_mensagem_previsao_padrao()
    db = SessionLocal()
    try:
        inicializar_dados(db)
        for emp in db.query(Empresa).all():
            configurar_campos_empresa(db, emp.id)
            criar_modelos_iniciais_empresa(db, emp)
            corrigir_valores_teste(db)
            recalcular_valores_reservas(db)
            corrigir_reservas_aprovadas_sem_itens(db)
            limpar_agenda_operacional(db)
            garantir_agenda_reservas(db, emp.id)
    finally:
        db.close()


def nome_item_reserva(item: Solicitacao) -> str:
    if item.produto:
        return item.produto.nome
    if item.itens:
        return item.itens[0].nome
    return "Reserva"


def retirada_obrigatoria_ativa(item: Solicitacao) -> bool:
    return bool(getattr(item, "retirada_obrigatoria", False))


def criar_ou_atualizar_retirada_obrigatoria(db: Session, item: Solicitacao):
    """
    Cria o card de BUSCA antes da entrega ser concluída quando o cliente exigiu retirada.
    Esse card fica com data/hora do contrato, não deve ser duplicado depois da entrega.
    """
    if not item or not item.id:
        return

    retirada = (
        db.query(Agenda)
        .filter_by(empresa_id=item.empresa_id, solicitacao_id=item.id, tipo_evento="retirada")
        .first()
    )

    if not retirada_obrigatoria_ativa(item):
        # Se a busca obrigatória foi removida e a busca ainda não foi executada, remove o card especial.
        if retirada and retirada.status_operacional != "concluido":
            db.delete(retirada)
        return

    data_retirada = item.retirada_data or item.data_evento
    hora_retirada = item.retirada_hora or item.hora_fim or item.hora_inicio
    titulo_base = f"{nome_item_reserva(item)} - {item.cliente.nome if item.cliente else 'Cliente'}"

    if not retirada:
        retirada = Agenda(
            empresa_id=item.empresa_id,
            solicitacao_id=item.id,
            tipo_evento="retirada",
            status_operacional="pendente",
        )
        db.add(retirada)

    retirada.data = data_retirada
    retirada.hora_inicio = hora_retirada
    retirada.hora_fim = None
    retirada.titulo = titulo_base
    retirada.bairro = item.bairro
    retirada.previsao_entrega = hora_retirada.strftime("%H:%M") if hora_retirada else ""


def criar_eventos_operacionais(db: Session, item: Solicitacao):
    """Garante a entrega e, se existir retirada obrigatória, garante também a busca do cliente."""
    if not item or not item.id:
        return

    titulo_base = f"{nome_item_reserva(item)} - {item.cliente.nome if item.cliente else 'Cliente'}"
    entrega = (
        db.query(Agenda)
        .filter_by(empresa_id=item.empresa_id, solicitacao_id=item.id, tipo_evento="entrega")
        .first()
    )
    if not entrega:
        entrega = Agenda(
            empresa_id=item.empresa_id,
            solicitacao_id=item.id,
            tipo_evento="entrega",
            status_operacional="pendente",
            data=item.data_evento,
            hora_inicio=item.hora_inicio,
            hora_fim=item.hora_fim,
            titulo=titulo_base,
            bairro=item.bairro,
        )
        db.add(entrega)
    else:
        # Não sobrescreve data/hora operacional já roteirizada.
        # A data/hora do contrato continua em Solicitacao; a operação usa Agenda.
        ja_roteirizado = bool(
            (entrega.previsao_entrega or "").strip()
            or (entrega.ordem_rota or 0)
            or (entrega.observacoes_operacionais and "Roteirização salva" in entrega.observacoes_operacionais)
            or (entrega.data and item.data_evento and entrega.data != item.data_evento)
            or (entrega.hora_inicio and item.hora_inicio and entrega.hora_inicio != item.hora_inicio)
        )
        if not ja_roteirizado:
            entrega.data = item.data_evento
            entrega.hora_inicio = item.hora_inicio
            entrega.hora_fim = item.hora_fim
        entrega.titulo = titulo_base
        entrega.bairro = item.bairro

    criar_ou_atualizar_retirada_obrigatoria(db, item)

def garantir_agenda_reservas(db: Session, empresa_id: int | None = None):
    """
    Garante que toda reserva válida apareça na Agenda.
    Isso corrige bases locais onde a reserva foi criada, mas o item da agenda não nasceu.
    """
    status_ignorados = {"rejeitada", "cancelada", "cancelado"}
    q = db.query(Solicitacao)
    if empresa_id:
        q = q.filter(Solicitacao.empresa_id == empresa_id)

    alterou = False
    for reserva in q.all():
        if reserva.status in status_ignorados:
            continue
        existe = (
            db.query(Agenda)
            .filter_by(empresa_id=reserva.empresa_id, solicitacao_id=reserva.id, tipo_evento="entrega")
            .first()
        )
        if not existe or retirada_obrigatoria_ativa(reserva):
            criar_eventos_operacionais(db, reserva)
            alterou = True

    if alterou:
        db.commit()


def criar_retirada_apos_entrega(db: Session, entrega: Agenda):
    """Ao concluir uma entrega, cria a retirada sugerida uma única vez."""
    reserva = entrega.solicitacao
    if not reserva:
        return

    # Se o cliente já exigiu retirada obrigatória, o card de busca já existe
    # e a entrega concluída não deve criar outro card vermelho de busca.
    if retirada_obrigatoria_ativa(reserva):
        criar_ou_atualizar_retirada_obrigatoria(db, reserva)
        return

    retirada_existente = (
        db.query(Agenda)
        .filter_by(empresa_id=entrega.empresa_id, solicitacao_id=entrega.solicitacao_id, tipo_evento="retirada")
        .first()
    )
    if retirada_existente:
        return

    prazo_dias = 1
    if reserva.produto and reserva.produto.prazo_retirada_dias is not None:
        prazo_dias = reserva.produto.prazo_retirada_dias

    db.add(Agenda(
        empresa_id=entrega.empresa_id,
        solicitacao_id=entrega.solicitacao_id,
        tipo_evento="retirada",
        status_operacional="pendente",
        data=(entrega.data or reserva.data_evento) + timedelta(days=prazo_dias),
        hora_inicio=entrega.hora_fim or entrega.hora_inicio,
        hora_fim=None,
        titulo=entrega.titulo,
        bairro=entrega.bairro,
    ))


def mensagens_empresa(empresa: Empresa) -> dict:
    """Mensagens prontas. A empresa pode editar sem precisar entender o sistema."""
    return {
        "reserva": empresa.mensagem_reserva or (
            "Olá!\n\n"
            "Para agilizar sua reserva, preencha este formulário:\n"
            "{{link}}\n\n"
            "Após o envio, nossa equipe irá preparar os equipamentos, valores e o pré-contrato.\n\n"
            "Assim que estiver tudo pronto, você receberá o contrato para análise e aceite."
        ),
        "aceite": empresa.mensagem_aceite or (
            "Olá, {{cliente}}!\n\n"
            "Seu pré-contrato está pronto.\n\n"
            "Confira atentamente as informações e, se estiver tudo correto, efetue o aceite pelo link abaixo:\n"
            "{{link}}"
        ),
        # Mantido apenas por compatibilidade com bancos antigos. Não é mais exibido nem utilizado no fluxo.
        "pagamento": "",
        "confirmacao": empresa.mensagem_confirmacao or (
            "Sua reserva foi efetivada com sucesso.\n\n"
            "Obrigado pela confiança!"
        ),
        "hora_fim": empresa.mensagem_hora_fim or (
            "Seu fim de contrato é calculado automaticamente. Leia o contrato quando receber."
        ),
        "preparacao": empresa.mensagem_preparacao or MENSAGEM_OPERACAO_PREPARACAO_APROVADA,
        "a_caminho": empresa.mensagem_a_caminho or MENSAGEM_OPERACAO_A_CAMINHO_APROVADA,
    }


def url_publica(request: Request, caminho: str) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}{caminho}"


def empresa_logada(request: Request, db: Session = Depends(get_db)) -> Empresa:
    empresa_id = request.session.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=303, headers={"Location": "/empresa/login"})
    empresa = db.get(Empresa, empresa_id)
    if not empresa:
        request.session.clear()
        raise HTTPException(status_code=303, headers={"Location": "/empresa/login"})
    return empresa


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if request.session.get("empresa_id"):
        return RedirectResponse("/painel", status_code=303)
    if request.session.get("admin_geral"):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("home.html", {"request": request})


def admin_geral_logado(request: Request):
    if not request.session.get("admin_geral"):
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    return True


@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_form(request: Request):
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "erro": request.query_params.get("erro"),
        "titulo_login": "Administrador Geral",
        "action_login": "/admin/login"
    })


@app.post("/admin/login")
def admin_login(request: Request, usuario: str = Form(...), senha: str = Form(...)):
    if usuario.strip() == ADMIN_NOME and senha.strip() == ADMIN_SENHA:
        request.session.clear()
        request.session["admin_geral"] = True
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse("/admin/login?erro=Usuário ou senha inválidos", status_code=303)


@app.get("/admin/sair")
def admin_sair(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin_geral(request: Request, db: Session = Depends(get_db), ok: bool = Depends(admin_geral_logado)):
    empresas = db.query(Empresa).order_by(Empresa.nome).all()
    return templates.TemplateResponse("admin/empresas.html",
                                      {"request": request, "empresas": empresas, "empresa": None})


@app.post("/admin/empresas")
def admin_criar_empresa(
        nome: str = Form(...),
        slug: str = Form(...),
        usuario_admin: str = Form(...),
        senha_admin: str = Form(...),
        identificador_principal: str = Form("telefone"),
        pix_copia_cola: str = Form(""),
        exige_sinal: Optional[str] = Form(None),
        suporte_inicio: str = Form(""),
        suporte_fim: str = Form(""),
        mostrar_suporte_contrato: Optional[str] = Form(None),
        logo_url: str = Form(""),
        logo_idb_url: str = Form(""),
        logo_arquivo: UploadFile | None = File(None),
        tema: str = Form("azul"),
        mensagem_reserva: str = Form(""),
        mensagem_aceite: str = Form(""),
        mensagem_pagamento: str = Form(""),
        mensagem_confirmacao: str = Form(""),
        mensagem_hora_fim: str = Form(""),
        mostrar_mensagem_hora_fim: Optional[str] = Form(None),
        mensagem_preparacao: str = Form(""),
        mensagem_a_caminho: str = Form(""),
        mensagem_localizacao: str = Form(""),
        db: Session = Depends(get_db),
        ok: bool = Depends(admin_geral_logado)
):
    empresa = Empresa(
        nome=nome.strip(),
        slug=slug.strip().lower().replace(" ", "-"),
        identificador_principal=identificador_principal,
        usuario_admin=usuario_admin.strip(),
        senha_admin=senha_admin.strip(),
        pix_copia_cola=pix_copia_cola.strip(),
        exige_sinal=bool(exige_sinal),
        suporte_inicio=suporte_inicio.strip(),
        suporte_fim=suporte_fim.strip(),
        mostrar_suporte_contrato=bool(mostrar_suporte_contrato),
        logo_url="",
        logo_idb_url="",
        tema=tema,
        mensagem_reserva=mensagem_reserva.strip(),
        mensagem_aceite=mensagem_aceite.strip(),
        mensagem_pagamento=mensagem_pagamento.strip(),
        mensagem_confirmacao=mensagem_confirmacao.strip(),
        mensagem_preparacao=mensagem_preparacao.strip(),
        mensagem_a_caminho=mensagem_a_caminho.strip(),
        mensagem_localizacao=mensagem_localizacao.strip(),
        ativa=True
    )
    db.add(empresa)
    db.commit()
    db.refresh(empresa)

    # Logo no cadastro inicial da empresa.
    if logo_arquivo and logo_arquivo.filename:
        extensao = Path(logo_arquivo.filename).suffix.lower()
        if extensao not in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]:
            raise HTTPException(400, "Formato de logo inválido. Use PNG, JPG, WEBP, GIF ou SVG.")
        nome_arquivo = f"empresa_{empresa.id}_{uuid.uuid4().hex}{extensao}"
        destino = Path("static/uploads/logos") / nome_arquivo
        with destino.open("wb") as buffer:
            shutil.copyfileobj(logo_arquivo.file, buffer)
        empresa.logo_url = f"/static/uploads/logos/{nome_arquivo}"
        empresa.logo_idb_url = ""
    elif logo_url.strip():
        empresa.logo_url = logo_url.strip()
        empresa.logo_idb_url = ""
    elif logo_idb_url.strip():
        empresa.logo_idb_url = logo_idb_url.strip()
        empresa.logo_url = ""
    db.commit()
    db.refresh(empresa)
    configurar_campos_empresa(db, empresa.id)
    criar_modelos_iniciais_empresa(db, empresa)
    return RedirectResponse("/admin", status_code=303)


@app.get("/admin/empresa/{empresa_id}", response_class=HTMLResponse)
def admin_editar_empresa(empresa_id: int, request: Request, db: Session = Depends(get_db),
                         ok: bool = Depends(admin_geral_logado)):
    empresa = db.get(Empresa, empresa_id)
    if not empresa:
        raise HTTPException(404)
    empresas = db.query(Empresa).order_by(Empresa.nome).all()
    usuarios_empresa = db.query(UsuarioEmpresa).filter_by(empresa_id=empresa.id).order_by(UsuarioEmpresa.nome).all()
    return templates.TemplateResponse("admin/empresas.html",
                                      {"request": request, "empresas": empresas, "empresa": empresa,
                                       "usuarios_empresa": usuarios_empresa})


@app.post("/admin/empresa/{empresa_id}")
def admin_salvar_empresa(
        empresa_id: int,
        nome: str = Form(...),
        slug: str = Form(...),
        usuario_admin: str = Form(...),
        senha_admin: str = Form(...),
        identificador_principal: str = Form("telefone"),
        pix_copia_cola: str = Form(""),
        exige_sinal: Optional[str] = Form(None),
        suporte_inicio: str = Form(""),
        suporte_fim: str = Form(""),
        mostrar_suporte_contrato: Optional[str] = Form(None),
        logo_url: str = Form(""),
        logo_idb_url: str = Form(""),
        logo_arquivo: UploadFile | None = File(None),
        tema: str = Form("azul"),
        ativa: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        ok: bool = Depends(admin_geral_logado)
):
    empresa = db.get(Empresa, empresa_id)
    if not empresa:
        raise HTTPException(404)
    empresa.nome = nome.strip()
    empresa.slug = slug.strip().lower().replace(" ", "-")
    empresa.identificador_principal = identificador_principal
    empresa.usuario_admin = usuario_admin.strip()
    empresa.senha_admin = senha_admin.strip()
    empresa.pix_copia_cola = pix_copia_cola.strip()
    empresa.exige_sinal = bool(exige_sinal)
    empresa.suporte_inicio = suporte_inicio.strip()
    empresa.suporte_fim = suporte_fim.strip()
    empresa.mostrar_suporte_contrato = bool(mostrar_suporte_contrato)
    # Logo: o caminho mais simples para o locador é enviar do próprio PC/celular.
    # Mantemos URL apenas como alternativa técnica.
    if logo_arquivo and logo_arquivo.filename:
        extensao = Path(logo_arquivo.filename).suffix.lower()
        if extensao not in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]:
            raise HTTPException(400, "Formato de logo inválido. Use PNG, JPG, WEBP, GIF ou SVG.")
        nome_arquivo = f"empresa_{empresa.id}_{uuid.uuid4().hex}{extensao}"
        destino = Path("static/uploads/logos") / nome_arquivo
        with destino.open("wb") as buffer:
            shutil.copyfileobj(logo_arquivo.file, buffer)
        empresa.logo_url = f"/static/uploads/logos/{nome_arquivo}"
        empresa.logo_idb_url = ""
    elif logo_url.strip():
        empresa.logo_url = logo_url.strip()
        empresa.logo_idb_url = ""
    elif logo_idb_url.strip():
        empresa.logo_idb_url = logo_idb_url.strip()
        empresa.logo_url = ""
    empresa.tema = tema
    empresa.ativa = bool(ativa)
    db.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/empresa/{empresa_id}/usuarios")
def admin_criar_usuario_empresa(
        empresa_id: int,
        nome: str = Form(...),
        usuario: str = Form(...),
        senha: Optional[str] = Form(None),
        usuario_id: Optional[int] = Form(None),
        ativo: Optional[str] = Form("1"),
        acesso_agenda: Optional[str] = Form(None),
        acesso_operacao: Optional[str] = Form(None),
        acesso_buscar_cliente: Optional[str] = Form(None),
        acesso_financeiro: Optional[str] = Form(None),
        acesso_cadastros: Optional[str] = Form(None),
        acesso_relatorios: Optional[str] = Form(None),
        acesso_equipe_1: Optional[str] = Form(None),
        acesso_equipe_2: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        ok: bool = Depends(admin_geral_logado)
):
    empresa = db.get(Empresa, empresa_id)
    if not empresa:
        raise HTTPException(404)

    usuario_limpo = usuario.strip()
    if not usuario_limpo:
        raise HTTPException(400, "Informe o usuário.")

    existente = None
    if usuario_id:
        existente = db.get(UsuarioEmpresa, usuario_id)
        if not existente or existente.empresa_id != empresa.id:
            raise HTTPException(404, "Usuário não encontrado.")

    conflito = (
        db.query(UsuarioEmpresa)
        .filter(
            UsuarioEmpresa.empresa_id == empresa.id,
            UsuarioEmpresa.usuario == usuario_limpo
        )
        .first()
    )
    if conflito and (not existente or conflito.id != existente.id):
        raise HTTPException(400, "Já existe um usuário com este login nesta empresa.")

    dados = {
        "nome": nome.strip(),
        "usuario": usuario_limpo,
        "ativo": bool(ativo),
        "acesso_agenda": bool(acesso_agenda),
        "acesso_operacao": bool(acesso_operacao),
        "acesso_buscar_cliente": bool(acesso_buscar_cliente),
        "acesso_financeiro": bool(acesso_financeiro),
        "acesso_cadastros": bool(acesso_cadastros),
        "acesso_relatorios": bool(acesso_relatorios),
        "acesso_equipe_1": bool(acesso_equipe_1),
        "acesso_equipe_2": bool(acesso_equipe_2),
    }

    if existente:
        for campo, valor in dados.items():
            setattr(existente, campo, valor)
        if senha and senha.strip():
            existente.senha = senha.strip()
    else:
        if not senha or not senha.strip():
            raise HTTPException(400, "Informe a senha para criar o usuário.")
        db.add(UsuarioEmpresa(
            empresa_id=empresa.id,
            senha=senha.strip(),
            **dados
        ))

    db.commit()
    return RedirectResponse(f"/admin/empresa/{empresa_id}", status_code=303)


@app.get("/admin/empresa/{empresa_id}/usuario/{usuario_id}/excluir")
def admin_excluir_usuario_empresa(
        empresa_id: int,
        usuario_id: int,
        db: Session = Depends(get_db),
        ok: bool = Depends(admin_geral_logado)
):
    usuario = db.get(UsuarioEmpresa, usuario_id)
    if usuario and usuario.empresa_id == empresa_id:
        db.delete(usuario)
        db.commit()
    return RedirectResponse(f"/admin/empresa/{empresa_id}", status_code=303)


@app.get("/empresa/login", response_class=HTMLResponse)
def empresa_login_form(request: Request, db: Session = Depends(get_db)):
    if request.session.get("empresa_id"):
        return RedirectResponse("/painel", status_code=303)
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "erro": request.query_params.get("erro"),
        "titulo_login": "Acesso da Empresa",
        "action_login": "/empresa/login"
    })


@app.post("/empresa/login")
def empresa_login(request: Request, usuario: str = Form(...), senha: str = Form(...), db: Session = Depends(get_db)):
    if request.session.get("empresa_id"):
        return RedirectResponse("/painel", status_code=303)
    usuario_limpo = usuario.strip()
    usuario_busca = usuario_limpo.lower()
    senha_limpa = senha.strip()

    empresa = db.query(Empresa).filter(
        func.lower(Empresa.usuario_admin) == usuario_busca,
        Empresa.senha_admin == senha_limpa,
        Empresa.ativa == True
    ).first()
    if empresa:
        request.session.clear()
        request.session["empresa_id"] = empresa.id
        request.session["usuario_sistema"] = usuario_limpo
        request.session["usuario_nome"] = empresa.usuario_admin or usuario_limpo
        request.session["acesso_total"] = True
        request.session["acessos"] = {}
        return RedirectResponse("/painel", status_code=303)

    usuario_empresa = (
        db.query(UsuarioEmpresa)
        .join(Empresa, Empresa.id == UsuarioEmpresa.empresa_id)
        .filter(func.lower(UsuarioEmpresa.usuario) == usuario_busca, UsuarioEmpresa.senha == senha_limpa,
                UsuarioEmpresa.ativo == True, Empresa.ativa == True)
        .first()
    )
    if usuario_empresa:
        request.session.clear()
        request.session["empresa_id"] = usuario_empresa.empresa_id
        request.session["usuario_sistema"] = usuario_empresa.usuario
        request.session["usuario_nome"] = usuario_empresa.nome
        request.session["usuario_empresa_id"] = usuario_empresa.id
        request.session["acesso_total"] = False
        request.session["acessos"] = {
            "agenda": bool(usuario_empresa.acesso_agenda),
            "operacao": bool(usuario_empresa.acesso_operacao),
            "buscar_cliente": bool(usuario_empresa.acesso_buscar_cliente),
            "financeiro": bool(usuario_empresa.acesso_financeiro),
            "cadastros": bool(usuario_empresa.acesso_cadastros),
            "relatorios": bool(usuario_empresa.acesso_relatorios),
        }
        return RedirectResponse("/painel", status_code=303)

    return RedirectResponse(
        "/empresa/login?erro=Usuário ou senha não encontrado. Confira o usuário, a senha e se o celular está acessando o endereço correto da rede local.",
        status_code=303)


@app.get("/empresa/sair")
def empresa_sair(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/admin/setup")
def setup_antigo():
    return RedirectResponse("/admin/login", status_code=303)


def configurar_campos_empresa(db: Session, empresa_id: int):
    campos = db.query(CampoGlobal).all()
    obrigatorios = {"telefone", "nome", "bairro", "endereco", "numero", "data_evento", "hora_inicio"}
    for ordem, campo in enumerate(campos, start=1):
        existe = db.query(CampoEmpresa).filter_by(empresa_id=empresa_id, campo_id=campo.id).first()
        if not existe:
            visivel = campo.chave not in ["hora_fim"]
            db.add(CampoEmpresa(empresa_id=empresa_id, campo_id=campo.id, ordem=ordem, visivel=visivel,
                                obrigatorio=campo.chave in obrigatorios))
    db.commit()


def criar_modelos_iniciais_empresa(db: Session, empresa: Empresa):
    """Cria produto, contrato e mensagens padrão para a empresa não começar vazia."""
    contrato = db.query(Contrato).filter_by(empresa_id=empresa.id).first()
    if not contrato:
        contrato = Contrato(
            empresa_id=empresa.id,
            nome="Contrato padrão de locação",
            descricao="Modelo inicial pronto para editar.",
            clausulas="""CONTRATO DE LOCAÇÃO DE EQUIPAMENTOS

A LOCADORA disponibilizará ao CLIENTE os equipamentos e serviços combinados para a data do evento.

O CLIENTE declara que recebeu a proposta com descrição dos itens, endereço, horário, valor total e condições de pagamento antes do aceite.

A reserva somente será considerada confirmada após o aceite digital e, quando exigido, após a confirmação do pagamento do sinal.

O CLIENTE se compromete a informar corretamente endereço, acesso ao local, responsável pelo recebimento e qualquer restrição de entrega, como escadas, elevador, horário de carga e descarga ou necessidade de autorização.

A LOCADORA poderá cancelar ou reagendar a reserva caso as informações do local impeçam a entrega segura dos equipamentos.

Este é um contrato fictício inicial. Edite este texto conforme a política da empresa."""
        )
        db.add(contrato)
        db.commit()
        db.refresh(contrato)

    produto = db.query(ProdutoServico).filter_by(empresa_id=empresa.id).first()
    if not produto:
        db.add(ProdutoServico(
            empresa_id=empresa.id,
            contrato_id=None,
            nome="Jukebox Básico - exemplo",
            descricao="1 jukebox, 2 caixas, 2 microfones e cabos. Edite ou exclua este exemplo.",
            quantidade_disponivel=1,
            valor_base=0,
            duracao_minutos=240,
            ativo=True
        ))
        db.commit()

    mensagens = mensagens_empresa(empresa)
    empresa.mensagem_reserva = empresa.mensagem_reserva or mensagens["reserva"]
    empresa.mensagem_aceite = empresa.mensagem_aceite or mensagens["aceite"]
    empresa.mensagem_confirmacao = empresa.mensagem_confirmacao or mensagens["confirmacao"]
    empresa.mensagem_hora_fim = empresa.mensagem_hora_fim or mensagens["hora_fim"]
    if empresa.mostrar_mensagem_hora_fim is None:
        empresa.mostrar_mensagem_hora_fim = True
    db.commit()


@app.get("/painel/acesso-negado", response_class=HTMLResponse)
def acesso_negado(request: Request, area: str = "", empresa: Empresa = Depends(empresa_logada)):
    nomes = {
        "agenda": "Agenda", "operacao": "Operação", "buscar_cliente": "Buscar cliente",
        "financeiro": "Financeiro", "cadastros": "Cadastros", "relatorios": "Relatórios"
    }
    return templates.TemplateResponse("admin/acesso_negado.html", {
        "request": request, "empresa": empresa, "area": nomes.get(area, area)
    }, status_code=403)


@app.get("/painel/relatorios", response_class=HTMLResponse)
def relatorios(request: Request, empresa: Empresa = Depends(empresa_logada)):
    return templates.TemplateResponse("admin/relatorios.html", {"request": request, "empresa": empresa})


@app.get("/painel", response_class=HTMLResponse)
def painel(request: Request, db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)):
    garantir_agenda_reservas(db, empresa.id)

    solicitacoes = (
        db.query(Solicitacao)
        .filter(
            Solicitacao.empresa_id == empresa.id,
            Solicitacao.status.in_(["reserva", "pre_reserva", "contrato_enviado", "aguardando_aceite"])
        )
        .order_by(Solicitacao.data_evento.asc(), Solicitacao.hora_inicio.asc())
        .limit(8)
        .all()
    )

    total_clientes = db.query(Cliente).filter_by(empresa_id=empresa.id).count()
    total_produtos = db.query(ProdutoServico).filter_by(empresa_id=empresa.id).count()

    pendentes = db.query(Solicitacao).filter(
        Solicitacao.empresa_id == empresa.id,
        Solicitacao.status.in_(["reserva", "pre_reserva", "contrato_enviado", "aguardando_aceite"])
    ).count()

    inicio_semana, fim_semana = periodo_semana_atual()
    status_agenda_inativos = {"aguardando_nova_data", "cancelada", "cancelado_cliente", "rejeitada"}

    agenda_periodo_qtd = db.query(Solicitacao).filter(
        Solicitacao.empresa_id == empresa.id,
        Solicitacao.data_evento >= inicio_semana,
        Solicitacao.data_evento <= fim_semana,
        ~Solicitacao.status.in_(status_agenda_inativos)
    ).count()

    operacao_base = db.query(Agenda).filter(
        Agenda.empresa_id == empresa.id,
        Agenda.data >= inicio_semana,
        Agenda.data <= fim_semana,
        Agenda.status_operacional != "concluido"
    )
    operacao_entregar_qtd = operacao_base.filter(Agenda.tipo_evento == "entrega").count()
    operacao_buscar_qtd = operacao_base.filter(Agenda.tipo_evento == "retirada").count()
    operacao_periodo_qtd = operacao_entregar_qtd + operacao_buscar_qtd

    pendencias_agenda = solicitacoes

    pendencias_sinal = []
    if empresa.exige_sinal:
        pendencias_sinal = (
            db.query(Solicitacao)
            .filter(
                Solicitacao.empresa_id == empresa.id,
                Solicitacao.status.in_(["aceito", "aguardando_pagamento", "reserva_confirmada"]),
                Solicitacao.valor_pago <= 0
            )
            .order_by(Solicitacao.data_evento.asc(), Solicitacao.hora_inicio.asc())
            .limit(12)
            .all()
        )

    hoje = date.today()
    pendencias_operacao = (
        db.query(Agenda)
        .join(Solicitacao)
        .filter(
            Agenda.empresa_id == empresa.id,
            Agenda.data < hoje,
            Agenda.status_operacional != "concluido",
            ~Solicitacao.status.in_(status_agenda_inativos)
        )
        .order_by(Agenda.data.asc(), Agenda.hora_inicio.asc())
        .limit(12)
        .all()
    )

    pendencias_financeiras = (
        db.query(Pagamento)
        .join(Solicitacao)
        .join(Cliente)
        .filter(
            Pagamento.empresa_id == empresa.id,
            Pagamento.conciliado_em == None
        )
        .order_by(Pagamento.data_pagamento.asc(), Pagamento.id.asc())
        .limit(12)
        .all()
    )

    link_pre_contrato = f"{str(request.base_url).rstrip('/')}/e/{empresa.slug}/pre-contrato"
    mensagem_pre_contrato = aplicar_variaveis_mensagem(
        mensagens_empresa(empresa).get("reserva", ""),
        link=link_pre_contrato,
        empresa=empresa.nome,
        cliente="",
        valor_sinal="",
        pix=empresa.pix_copia_cola or "",
    )

    return templates.TemplateResponse("admin/painel.html", {
        "request": request,
        "empresa": empresa,
        "mensagem_pre_contrato": mensagem_pre_contrato,
        "solicitacoes": solicitacoes,
        "pendencias_agenda": pendencias_agenda,
        "pendencias_sinal": pendencias_sinal,
        "pendencias_operacao": pendencias_operacao,
        "pendencias_financeiras": pendencias_financeiras,
        "total_clientes": total_clientes,
        "total_produtos": total_produtos,
        "pendentes": pendentes,
        "agenda_periodo_qtd": agenda_periodo_qtd,
        "operacao_periodo_qtd": operacao_periodo_qtd,
        "operacao_entregar_qtd": operacao_entregar_qtd,
        "operacao_buscar_qtd": operacao_buscar_qtd,
        "inicio_semana": inicio_semana,
        "fim_semana": fim_semana,
        "usuario_online": request.session.get("usuario_nome") or request.session.get("usuario") or "Usuário"
    })



def usuario_empresa_atual(db: Session, empresa: Empresa, request: Request):
    usuario_sessao = (request.session.get("usuario_sistema") or request.session.get("usuario") or "").strip()
    usuario_busca = usuario_sessao.lower()
    usuario = None
    if usuario_busca:
        usuario = (
            db.query(UsuarioEmpresa)
            .filter(
                UsuarioEmpresa.empresa_id == empresa.id,
                func.lower(UsuarioEmpresa.usuario) == usuario_busca,
                UsuarioEmpresa.ativo == True,
            )
            .first()
        )
    if usuario:
        return "usuario", usuario
    return "admin", empresa


@app.get("/painel/perfil", response_class=HTMLResponse)
def perfil_usuario(request: Request, db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)):
    tipo, usuario = usuario_empresa_atual(db, empresa, request)
    perfil_nome = usuario.nome if tipo == "usuario" else (request.session.get("usuario_nome") or empresa.usuario_admin or "Administrador")
    perfil_usuario_valor = usuario.usuario if tipo == "usuario" else (empresa.usuario_admin or request.session.get("usuario_sistema") or "")
    return templates.TemplateResponse("admin/perfil.html", {
        "request": request,
        "empresa": empresa,
        "perfil_nome": perfil_nome,
        "perfil_usuario": perfil_usuario_valor,
        "erro": request.query_params.get("erro"),
        "sucesso": request.query_params.get("sucesso"),
    })


@app.post("/painel/perfil")
def salvar_perfil_usuario(
        request: Request,
        nome: str = Form(...),
        usuario: str = Form(...),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)):
    nome_limpo = nome.strip()
    usuario_limpo = usuario.strip()
    if not nome_limpo or not usuario_limpo:
        return RedirectResponse("/painel/perfil?erro=Informe nome e usuário.", status_code=303)

    tipo, registro = usuario_empresa_atual(db, empresa, request)
    usuario_busca = usuario_limpo.lower()

    empresa_com_usuario = (
        db.query(Empresa)
        .filter(func.lower(Empresa.usuario_admin) == usuario_busca, Empresa.id != empresa.id)
        .first()
    )
    usuario_com_usuario = (
        db.query(UsuarioEmpresa)
        .filter(func.lower(UsuarioEmpresa.usuario) == usuario_busca)
        .first()
    )
    if empresa_com_usuario or (usuario_com_usuario and (tipo != "usuario" or usuario_com_usuario.id != registro.id)):
        return RedirectResponse("/painel/perfil?erro=Este usuário já está em uso.", status_code=303)

    if tipo == "usuario":
        registro.nome = nome_limpo
        registro.usuario = usuario_limpo
        request.session["usuario_nome"] = nome_limpo
        request.session["usuario_sistema"] = usuario_limpo
    else:
        empresa.usuario_admin = usuario_limpo
        request.session["usuario_nome"] = nome_limpo
        request.session["usuario_sistema"] = usuario_limpo

    db.commit()
    return RedirectResponse("/painel/perfil?sucesso=Perfil atualizado com sucesso.", status_code=303)


@app.get("/painel/alterar-senha", response_class=HTMLResponse)
def alterar_senha_form(request: Request, db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)):
    return templates.TemplateResponse("admin/alterar_senha.html", {
        "request": request,
        "empresa": empresa,
        "erro": request.query_params.get("erro"),
        "sucesso": request.query_params.get("sucesso"),
    })


@app.post("/painel/alterar-senha")
def alterar_senha_salvar(
        request: Request,
        senha_atual: str = Form(...),
        nova_senha: str = Form(...),
        confirmar_senha: str = Form(...),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)):
    senha_atual = senha_atual.strip()
    nova_senha = nova_senha.strip()
    confirmar_senha = confirmar_senha.strip()
    if len(nova_senha) < 6:
        return RedirectResponse("/painel/alterar-senha?erro=A nova senha precisa ter pelo menos 6 caracteres.", status_code=303)
    if nova_senha != confirmar_senha:
        return RedirectResponse("/painel/alterar-senha?erro=A confirmação da senha não confere.", status_code=303)

    tipo, registro = usuario_empresa_atual(db, empresa, request)
    senha_cadastrada = registro.senha if tipo == "usuario" else empresa.senha_admin
    if senha_atual != (senha_cadastrada or ""):
        return RedirectResponse("/painel/alterar-senha?erro=Senha atual incorreta.", status_code=303)

    if tipo == "usuario":
        registro.senha = nova_senha
    else:
        empresa.senha_admin = nova_senha
    db.commit()
    return RedirectResponse("/painel/alterar-senha?sucesso=Senha alterada com sucesso.", status_code=303)


@app.get("/painel/configuracoes", response_class=HTMLResponse)
def configuracoes_empresa(request: Request, db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)):
    mensagens_padrao = mensagens_empresa(empresa)
    campos = db.query(CampoEmpresa).join(CampoGlobal).filter(CampoEmpresa.empresa_id == empresa.id).order_by(
        CampoEmpresa.ordem).all()
    return templates.TemplateResponse("admin/configuracoes.html",
                                      {"request": request, "empresa": empresa, "mensagens_padrao": mensagens_padrao,
                                       "campos": campos})


@app.post("/painel/configuracoes")
async def salvar_configuracoes_empresa(
        request: Request,
        pix_copia_cola: str = Form(""),
        exige_sinal: Optional[str] = Form(None),
        suporte_inicio: str = Form(""),
        suporte_fim: str = Form(""),
        mostrar_suporte_contrato: Optional[str] = Form(None),
        logo_url: str = Form(""),
        logo_idb_url: str = Form(""),
        logo_arquivo: UploadFile | None = File(None),
        tema: str = Form("azul"),
        mensagem_reserva: str = Form(""),
        mensagem_aceite: str = Form(""),
        mensagem_pagamento: str = Form(""),
        mensagem_confirmacao: str = Form(""),
        mensagem_hora_fim: str = Form(""),
        mostrar_mensagem_hora_fim: Optional[str] = Form(None),
        mensagem_preparacao: str = Form(""),
        mensagem_a_caminho: str = Form(""),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    empresa.pix_copia_cola = pix_copia_cola.strip()
    empresa.exige_sinal = bool(exige_sinal)
    empresa.suporte_inicio = suporte_inicio.strip()
    empresa.suporte_fim = suporte_fim.strip()
    empresa.mostrar_suporte_contrato = bool(mostrar_suporte_contrato)
    # Logo: o caminho mais simples para o locador é enviar do próprio PC/celular.
    # Mantemos URL apenas como alternativa técnica.
    if logo_arquivo and logo_arquivo.filename:
        extensao = Path(logo_arquivo.filename).suffix.lower()
        if extensao not in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]:
            raise HTTPException(400, "Formato de logo inválido. Use PNG, JPG, WEBP, GIF ou SVG.")
        nome_arquivo = f"empresa_{empresa.id}_{uuid.uuid4().hex}{extensao}"
        destino = Path("static/uploads/logos") / nome_arquivo
        with destino.open("wb") as buffer:
            shutil.copyfileobj(logo_arquivo.file, buffer)
        empresa.logo_url = f"/static/uploads/logos/{nome_arquivo}"
        empresa.logo_idb_url = ""
    elif logo_url.strip():
        empresa.logo_url = logo_url.strip()
        empresa.logo_idb_url = ""
    elif logo_idb_url.strip():
        empresa.logo_idb_url = logo_idb_url.strip()
        empresa.logo_url = ""
    empresa.tema = tema
    empresa.mensagem_reserva = mensagem_reserva.strip()
    empresa.mensagem_aceite = mensagem_aceite.strip()
    empresa.mensagem_confirmacao = mensagem_confirmacao.strip()
    empresa.mensagem_hora_fim = mensagem_hora_fim.strip()
    empresa.mostrar_mensagem_hora_fim = bool(mostrar_mensagem_hora_fim)
    empresa.mensagem_preparacao = mensagem_preparacao.strip()
    empresa.mensagem_a_caminho = mensagem_a_caminho.strip()
    form = await request.form()
    campos = db.query(CampoEmpresa).filter_by(empresa_id=empresa.id).all()
    for ce in campos:
        ce.visivel = f"campo_visivel_{ce.id}" in form
        ce.obrigatorio = f"campo_obrigatorio_{ce.id}" in form
    db.commit()
    return RedirectResponse("/painel", status_code=303)


@app.get("/painel/produtos", response_class=HTMLResponse)
def produtos(request: Request, db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)):
    produtos = db.query(ProdutoServico).filter_by(empresa_id=empresa.id).order_by(ProdutoServico.nome).all()
    contratos = db.query(Contrato).filter_by(empresa_id=empresa.id, ativo=True).order_by(Contrato.nome).all()
    return templates.TemplateResponse("admin/produtos.html",
                                      {"request": request, "empresa": empresa, "produtos": produtos, "produto": None,
                                       "contratos": contratos})


@app.get("/painel/produto/{produto_id}", response_class=HTMLResponse)
def produto_editar(produto_id: int, request: Request, db: Session = Depends(get_db),
                   empresa: Empresa = Depends(empresa_logada)):
    produto = db.get(ProdutoServico, produto_id)
    if not produto or produto.empresa_id != empresa.id:
        raise HTTPException(404)
    produtos = db.query(ProdutoServico).filter_by(empresa_id=empresa.id).order_by(ProdutoServico.nome).all()
    contratos = db.query(Contrato).filter_by(empresa_id=empresa.id, ativo=True).order_by(Contrato.nome).all()
    return templates.TemplateResponse("admin/produtos.html",
                                      {"request": request, "empresa": empresa, "produtos": produtos,
                                       "produto": produto, "contratos": contratos})


@app.post("/painel/produto/{produto_id_url}")
def salvar_produto_url(produto_id_url: int, nome: str = Form(...), descricao: str = Form(""),
                       quantidade_disponivel: int = Form(1), valor_base: str = Form("0"),
                       duracao_minutos: int = Form(240), prazo_retirada_dias: int = Form(1),
                       contrato_id: str = Form(""),
                       db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)):
    return salvar_produto(str(produto_id_url), nome, descricao, quantidade_disponivel, valor_base, duracao_minutos,
                          prazo_retirada_dias, contrato_id, db, empresa)


@app.post("/painel/produtos")
def salvar_produto(
        produto_id: str = Form(""),
        nome: str = Form(...), descricao: str = Form(""),
        quantidade_disponivel: int = Form(1), valor_base: str = Form("0"), duracao_minutos: int = Form(240),
        prazo_retirada_dias: int = Form(1), contrato_id: str = Form(""),
        db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)
):
    produto_id_int = int(produto_id) if produto_id else None
    produto = db.get(ProdutoServico, produto_id_int) if produto_id_int else None
    if not produto:
        produto = ProdutoServico(empresa_id=empresa.id)
        db.add(produto)
    produto.nome = nome.strip()
    produto.descricao = descricao
    contrato_id_int = int(contrato_id) if contrato_id and str(contrato_id).isdigit() else None
    contrato = db.get(Contrato, contrato_id_int) if contrato_id_int else None
    produto.contrato_id = contrato.id if contrato and contrato.empresa_id == empresa.id else None
    produto.quantidade_disponivel = quantidade_disponivel
    produto.valor_base = texto_para_float(valor_base)
    produto.duracao_minutos = duracao_minutos
    produto.prazo_retirada_dias = prazo_retirada_dias
    produto.tipo_locacao = "horas_fixas"
    db.commit()
    return RedirectResponse("/painel/produtos", status_code=303)


@app.get("/painel/produto/{produto_id}/copiar")
def copiar_produto(produto_id: int, db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)):
    origem = db.get(ProdutoServico, produto_id)
    if not origem or origem.empresa_id != empresa.id:
        raise HTTPException(404)
    novo = ProdutoServico(empresa_id=empresa.id, contrato_id=origem.contrato_id, nome=f"{origem.nome} - cópia",
                          descricao=origem.descricao, quantidade_disponivel=origem.quantidade_disponivel,
                          valor_base=origem.valor_base, duracao_minutos=origem.duracao_minutos,
                          prazo_retirada_dias=origem.prazo_retirada_dias, ativo=True)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return RedirectResponse(f"/painel/produto/{novo.id}", status_code=303)


@app.get("/painel/contratos", response_class=HTMLResponse)
def contratos(request: Request, db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)):
    contratos = db.query(Contrato).filter_by(empresa_id=empresa.id).order_by(Contrato.nome).all()
    return templates.TemplateResponse("admin/contratos.html",
                                      {"request": request, "empresa": empresa, "contratos": contratos,
                                       "contrato": None})


@app.get("/painel/contrato/{contrato_id}", response_class=HTMLResponse)
def contrato_editar(contrato_id: int, request: Request, db: Session = Depends(get_db),
                    empresa: Empresa = Depends(empresa_logada)):
    contrato = db.get(Contrato, contrato_id)
    if not contrato or contrato.empresa_id != empresa.id:
        raise HTTPException(404)
    contratos = db.query(Contrato).filter_by(empresa_id=empresa.id).order_by(Contrato.nome).all()
    return templates.TemplateResponse("admin/contratos.html",
                                      {"request": request, "empresa": empresa, "contratos": contratos,
                                       "contrato": contrato})


@app.post("/painel/contrato/{contrato_id}")
@app.post("/painel/contratos")
def salvar_contrato(
        contrato_id: int | None = None,
        contrato_id_form: str = Form("", alias="contrato_id"),
        nome: str = Form(...), descricao: str = Form(""), clausulas: str = Form(...),
        db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)
):
    contrato_id_final = contrato_id or (int(contrato_id_form) if contrato_id_form else None)
    contrato = db.get(Contrato, contrato_id_final) if contrato_id_final else None
    if contrato and contrato.empresa_id != empresa.id:
        raise HTTPException(404)
    if not contrato:
        contrato = Contrato(empresa_id=empresa.id)
        db.add(contrato)
    contrato.nome = nome.strip()
    contrato.descricao = descricao
    contrato.clausulas = clausulas
    db.commit()
    return RedirectResponse("/painel/contratos", status_code=303)


@app.get("/painel/contrato/{contrato_id}/copiar")
def copiar_contrato(contrato_id: int, db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)):
    origem = db.get(Contrato, contrato_id)
    if not origem or origem.empresa_id != empresa.id:
        raise HTTPException(404)
    novo = Contrato(
        empresa_id=empresa.id,
        nome=f"{origem.nome} - cópia",
        descricao=origem.descricao,
        clausulas=origem.clausulas,
        ativo=True
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return RedirectResponse(f"/painel/contrato/{novo.id}", status_code=303)


def equipes_permitidas_usuario(request: Request, db: Session) -> list[int]:
    if request.session.get("acesso_total"):
        return [1, 2]
    usuario_id = request.session.get("usuario_empresa_id")
    usuario = db.get(UsuarioEmpresa, usuario_id) if usuario_id else None
    equipes = []
    if usuario and getattr(usuario, "acesso_equipe_1", True):
        equipes.append(1)
    if usuario and getattr(usuario, "acesso_equipe_2", False):
        equipes.append(2)
    return equipes or [1]


def agenda_roteirizada(item: Agenda) -> bool:
    return bool((item.previsao_entrega or "").strip() and (item.ordem_rota or 0) in (1, 2))


@app.get("/painel/reservas", response_class=HTMLResponse)
def preparar_reservas(
        request: Request,
        data_inicial: str = "",
        data_final: str = "",
        mostrar_entregas: str = "",
        mostrar_retiradas: str = "",
        mostrar_concluidas: str = "",
        equipe: str = "",
        situacao_rota: str = "roteirizado",
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    inicio, fim = periodo_semana_atual()
    data_inicial = data_inicial or inicio.isoformat()
    data_final = data_final or fim.isoformat()
    equipes_permitidas = equipes_permitidas_usuario(request, db)
    equipe_salva = request.session.get("operacao_equipe")
    equipe_num = int(equipe) if equipe in {"1", "2"} else (equipe_salva if equipe_salva in equipes_permitidas else equipes_permitidas[0])
    if equipe_num not in equipes_permitidas:
        equipe_num = equipes_permitidas[0]
    request.session["operacao_equipe"] = equipe_num

    # Checkbox desmarcado não vem no GET. Se for o primeiro acesso da tela,
    # começa com Entregar e Retirar ligados. Depois disso, respeita exatamente
    # o que o usuário marcou/desmarcou.
    query = request.query_params
    if not query:
        mostrar_entregas = "1"
        mostrar_retiradas = "1"
        mostrar_concluidas = ""
    else:
        mostrar_entregas = "1" if "mostrar_entregas" in query else ""
        mostrar_retiradas = "1" if "mostrar_retiradas" in query else ""
        mostrar_concluidas = "1" if "mostrar_concluidas" in query else ""

    q = db.query(Agenda).filter_by(empresa_id=empresa.id)
    if situacao_rota == "nao_roteirizado":
        q = q.filter((Agenda.previsao_entrega == None) | (Agenda.previsao_entrega == "") | (~Agenda.ordem_rota.in_([1, 2])))
    else:
        situacao_rota = "roteirizado"
        q = q.filter(Agenda.previsao_entrega.isnot(None), Agenda.previsao_entrega != "", Agenda.ordem_rota == equipe_num)
    if data_inicial:
        q = q.filter(Agenda.data >= datetime.strptime(data_inicial, "%Y-%m-%d").date())
    if data_final:
        q = q.filter(Agenda.data <= datetime.strptime(data_final, "%Y-%m-%d").date())

    tipos = []
    if mostrar_entregas:
        tipos.append("entrega")
    if mostrar_retiradas:
        tipos.append("retirada")
    if tipos:
        q = q.filter(Agenda.tipo_evento.in_(tipos))
    else:
        q = q.filter(text("1=0"))

    if not mostrar_concluidas:
        q = q.filter(Agenda.status_operacional != "concluido")

    itens = q.join(Solicitacao, Agenda.solicitacao_id == Solicitacao.id).join(Cliente,
                                                                              Solicitacao.cliente_id == Cliente.id).all()
    sincronizar_pagamentos_solicitacoes(db, [a.solicitacao for a in itens])

    def chave_operacao(a: Agenda):
        sol = a.solicitacao
        data_base = a.data if agenda_roteirizada(a) else (sol.data_evento if sol else a.data)
        hora_base = a.hora_inicio if agenda_roteirizada(a) else (sol.hora_inicio if sol else a.hora_inicio)
        nome = (sol.cliente.nome if sol and sol.cliente else "").lower()
        return (data_base or date.max, hora_base or time.max, nome, a.id)

    itens = sorted(itens, key=chave_operacao)
    return templates.TemplateResponse("admin/preparar.html", {
        "request": request,
        "empresa": empresa,
        "itens": itens,
        "total_itens": len(itens),
        "data_inicial": data_inicial,
        "data_final": data_final,
        "mostrar_entregas": mostrar_entregas,
        "mostrar_retiradas": mostrar_retiradas,
        "mostrar_concluidas": mostrar_concluidas,
        "equipe_selecionada": equipe_num,
        "equipes_permitidas": equipes_permitidas,
        "situacao_rota": situacao_rota,
        "mensagens": mensagens_empresa(empresa),
    })


@app.get("/painel/solicitacoes", response_class=HTMLResponse)
def solicitacoes(request: Request, busca: str = "", db: Session = Depends(get_db),
                 empresa: Empresa = Depends(empresa_logada)):
    q = db.query(Solicitacao).filter_by(empresa_id=empresa.id)
    termo = limpar_identificador(busca)
    if termo:
        q = q.join(Cliente).filter((Cliente.cpf.contains(termo)) | (Cliente.telefone.contains(termo)) | (
            Cliente.identificador.contains(termo)))
    itens = q.join(Cliente, Solicitacao.cliente_id == Cliente.id).order_by(Solicitacao.data_evento, Cliente.nome,
                                                                           Solicitacao.hora_inicio,
                                                                           Solicitacao.id).all()
    return templates.TemplateResponse("admin/solicitacoes.html",
                                      {"request": request, "empresa": empresa, "itens": itens, "busca": busca})


@app.get("/painel/solicitacao/{solicitacao_id}", response_class=HTMLResponse)
def detalhe_solicitacao(solicitacao_id: int, request: Request, db: Session = Depends(get_db),
                        empresa: Empresa = Depends(empresa_logada)):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)
    sincronizar_pagamentos_solicitacoes(db, [item])
    produtos = db.query(ProdutoServico).filter_by(empresa_id=empresa.id, ativo=True).order_by(ProdutoServico.nome).all()
    contratos = db.query(Contrato).filter_by(empresa_id=empresa.id, ativo=True).order_by(Contrato.nome).all()
    mensagens = mensagens_empresa(empresa)
    return templates.TemplateResponse("admin/solicitacao_detalhe.html",
                                      {"request": request, "item": item, "empresa": empresa, "produtos": produtos,
                                       "contratos": contratos, "mensagens": mensagens})


@app.get("/painel/solicitacao/{solicitacao_id}/whatsapp")
def compartilhar_aceite_whatsapp(
    solicitacao_id: int,
    request: Request,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(empresa_logada),
):
    """Envia o link de aceite ao cliente. Não envia o contrato final."""
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)

    telefone = _limpar_tel_whatsapp(item.cliente.telefone or item.cliente.identificador)
    if not telefone:
        raise HTTPException(400, "Cliente sem telefone para WhatsApp")

    if item.status == "pre_reserva" and item.contrato_id and len(item.itens) > 0:
        item.status = "contrato_enviado"
        db.commit()

    texto = montar_mensagem_whatsapp_aceite(request, empresa, item, db)

    return RedirectResponse(
        f"https://wa.me/{telefone}?text={quote(texto)}",
        status_code=303,
    )


@app.get("/painel/solicitacao/{solicitacao_id}/whatsapp-contrato")
def compartilhar_contrato_whatsapp(
    solicitacao_id: int,
    request: Request,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(empresa_logada),
):
    """Envia o contrato final somente após aceite do cliente ou aceite manual."""
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)

    if not status_reserva_confirmada(item.status):
        return RedirectResponse(
            f"/painel/solicitacao/{solicitacao_id}?erro=O contrato final só pode ser enviado depois do aceite do cliente ou aceite manual.",
            status_code=303,
        )

    telefone = _limpar_tel_whatsapp(item.cliente.telefone or item.cliente.identificador)
    if not telefone:
        raise HTTPException(400, "Cliente sem telefone para WhatsApp")

    texto = montar_mensagem_whatsapp_contrato(request, empresa, item, db)

    return RedirectResponse(
        f"https://wa.me/{telefone}?text={quote(texto)}",
        status_code=303,
    )

@app.get("/painel/solicitacao/{solicitacao_id}/cliente", response_class=HTMLResponse)
def editar_cliente_da_solicitacao(solicitacao_id: int, request: Request, db: Session = Depends(get_db),
                                  empresa: Empresa = Depends(empresa_logada)):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id or not item.cliente:
        raise HTTPException(404)
    return templates.TemplateResponse(
        "admin/solicitacao_cliente_editar.html",
        {"request": request, "item": item, "cliente": item.cliente, "empresa": empresa},
    )


@app.post("/painel/solicitacao/{solicitacao_id}/cliente")
def salvar_cliente_da_solicitacao(
        solicitacao_id: int,
        nome: str = Form(""),
        telefone: str = Form(""),
        cpf: str = Form(""),
        cnpj: str = Form(""),
        data_nascimento: str = Form(""),
        email: str = Form(""),
        endereco: str = Form(""),
        numero: str = Form(""),
        complemento: str = Form(""),
        bairro: str = Form(""),
        cidade: str = Form(""),
        estado: str = Form(""),
        cep: str = Form(""),
        observacoes: str = Form(""),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id or not item.cliente:
        raise HTTPException(404)

    cliente = item.cliente
    cliente.nome = nome.strip() or cliente.nome
    cliente.telefone = limpar_identificador(telefone)
    cliente.cpf = limpar_identificador(cpf)
    cliente.cnpj = limpar_identificador(cnpj)
    cliente.email = email.strip()
    cliente.endereco = endereco.strip()
    cliente.numero = numero.strip()
    cliente.complemento = complemento.strip()
    cliente.bairro = bairro.strip()
    cliente.cidade = cidade.strip()
    cliente.estado = estado.strip().upper()
    cliente.cep = limpar_identificador(cep)
    cliente.observacoes = observacoes.strip()

    if data_nascimento:
        try:
            cliente.data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
        except ValueError:
            pass

    if empresa.identificador_principal == "cpf" and cliente.cpf:
        cliente.identificador = cliente.cpf
    elif empresa.identificador_principal == "cnpj" and cliente.cnpj:
        cliente.identificador = cliente.cnpj
    elif cliente.telefone:
        cliente.identificador = cliente.telefone

    db.commit()
    return RedirectResponse(f"/painel/solicitacao/{solicitacao_id}", status_code=303)


@app.get("/painel/solicitacao/{solicitacao_id}/editar", response_class=HTMLResponse)
def editar_solicitacao(solicitacao_id: int, request: Request, db: Session = Depends(get_db),
                       empresa: Empresa = Depends(empresa_logada)):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)
    produtos = db.query(ProdutoServico).filter_by(empresa_id=empresa.id, ativo=True).order_by(ProdutoServico.nome).all()
    contratos = db.query(Contrato).filter_by(empresa_id=empresa.id, ativo=True).order_by(Contrato.nome).all()
    return templates.TemplateResponse("admin/solicitacao_editar.html",
                                      {"request": request, "item": item, "empresa": empresa, "produtos": produtos,
                                       "contratos": contratos})


@app.post("/painel/solicitacao/{solicitacao_id}/editar")
def salvar_edicao_solicitacao(
        solicitacao_id: int,
        data_evento: str = Form(""),
        hora_inicio: str = Form(""),
        hora_fim: str = Form(""),
        bairro: str = Form(""),
        local: str = Form(""),
        acesso_local: str = Form(""),
        valor: str = Form("0"),
        sinal: str = Form("0"),
        status: str = Form(""),
        observacoes: str = Form(""),
        aprovacao_manual: str = Form(""),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)

    if status in ["aguardando_nova_data", "cancelada", "cancelado_cliente", "rejeitada"]:
        item.status = status
        # Crédito ou cancelamento sai da operação e da roteirização,
        # mas permanece no financeiro e pode ser visto pelo filtro da agenda.
        db.query(Agenda).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).delete()
    else:
        if data_evento:
            item.data_evento = datetime.strptime(data_evento, "%Y-%m-%d").date()
        if hora_inicio:
            item.hora_inicio = datetime.strptime(hora_inicio, "%H:%M").time()
        if hora_fim:
            item.hora_fim = datetime.strptime(hora_fim, "%H:%M").time()
        item.status = status or item.status
        criar_eventos_operacionais(db, item)

    item.bairro = bairro
    item.local = local
    item.acesso_local = acesso_local
    item.valor = texto_para_float(valor)
    item.sinal = texto_para_float(sinal)
    item.observacoes = observacoes

    tem_itens = db.query(ReservaItem).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).count() > 0

    if item.status in ["reserva_confirmada", "aguardando_pagamento"] and not tem_itens:
        # Não deixa salvar uma reserva como aprovada/confirmada sem itens.
        item.status = "pre_reserva"
        item.aprovado_em = None
        item.sinal_recebido = False
        item.valor_pago = 0
        item.pagamento_confirmado_em = None

    if aprovacao_manual and tem_itens:
        item.status = "reserva_confirmada"
        item.aprovado_em = agora_utc()

    db.commit()
    return RedirectResponse(f"/painel/solicitacao/{solicitacao_id}", status_code=303)


@app.post("/painel/solicitacao/{solicitacao_id}/status")
def atualizar_status_solicitacao(
        solicitacao_id: int,
        status: str = Form(""),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)

    status_permitidos = ["reserva_confirmada", "aguardando_pagamento", "aguardando_nova_data", "cancelada"]
    if status in status_permitidos:
        tem_itens = db.query(ReservaItem).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).count() > 0
        if status in ["reserva_confirmada", "aguardando_pagamento"] and not tem_itens:
            item.status = "pre_reserva"
            item.aprovado_em = None
            item.sinal_recebido = False
            item.valor_pago = 0
            item.pagamento_confirmado_em = None
        else:
            item.status = status
            if status == "reserva_confirmada" and not item.aprovado_em:
                item.aprovado_em = agora_utc()
            if status in ["aguardando_nova_data", "cancelada", "cancelado_cliente", "rejeitada"]:
                db.query(Agenda).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).delete()
            else:
                criar_eventos_operacionais(db, item)

    db.commit()
    return RedirectResponse(f"/painel/solicitacao/{solicitacao_id}", status_code=303)


@app.post("/painel/solicitacao/{solicitacao_id}/cliente-local")
def salvar_cliente_local_solicitacao(
        solicitacao_id: int,
        nome: str = Form(""),
        telefone: str = Form(""),
        cpf: str = Form(""),
        email: str = Form(""),
        data_evento: str = Form(""),
        hora_inicio: str = Form(""),
        hora_fim: str = Form(""),
        local: str = Form(""),
        numero: str = Form(""),
        bairro: str = Form(""),
        acesso_local: str = Form(""),
        local_nome: str = Form(""),
        local_responsavel_nome: str = Form(""),
        local_responsavel_telefone: str = Form(""),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)

    cliente = item.cliente
    cliente.nome = nome.strip() or cliente.nome
    cliente.telefone = limpar_identificador(telefone) or telefone.strip()
    cliente.cpf = limpar_identificador(cpf)
    cliente.email = email.strip()
    cliente.endereco = local.strip()
    cliente.numero = numero.strip()
    cliente.bairro = bairro.strip()

    if data_evento:
        item.data_evento = datetime.strptime(data_evento, "%Y-%m-%d").date()
    if hora_inicio:
        item.hora_inicio = datetime.strptime(hora_inicio, "%H:%M").time()
    item.hora_fim = datetime.strptime(hora_fim, "%H:%M").time() if hora_fim else None
    item.local = local.strip()
    item.bairro = bairro.strip()
    item.acesso_local = acesso_local.strip()
    item.local_nome = local_nome.strip()
    item.local_responsavel_nome = local_responsavel_nome.strip()
    item.local_responsavel_telefone = limpar_identificador(
        local_responsavel_telefone) or local_responsavel_telefone.strip()

    if item.status not in ["cancelada", "cancelado_cliente", "aguardando_nova_data"]:
        criar_eventos_operacionais(db, item)

    db.commit()
    return RedirectResponse(f"/painel/solicitacao/{solicitacao_id}", status_code=303)


@app.post("/painel/solicitacao/{solicitacao_id}/preparar")
async def preparar_contrato(
        solicitacao_id: int,
        request: Request,
        contrato_id: str = Form(""),
        data_evento: str = Form(""),
        hora_inicio: str = Form(""),
        hora_fim: str = Form(""),
        bairro: str = Form(""),
        local: str = Form(""),
        acesso_local: str = Form(""),
        valor: str = Form("0"),
        sinal: str = Form("0"),
        observacoes: str = Form(""),
        acao: str = Form("salvar"),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)
    if item.status in ["cancelada", "cancelado_cliente"]:
        return RedirectResponse(f"/painel/solicitacao/{solicitacao_id}", status_code=303)

    if data_evento:
        item.data_evento = datetime.strptime(data_evento, "%Y-%m-%d").date()
    if hora_inicio:
        item.hora_inicio = datetime.strptime(hora_inicio, "%H:%M").time()
    item.hora_fim = datetime.strptime(hora_fim, "%H:%M").time() if hora_fim else None
    item.bairro = bairro
    item.local = local
    item.acesso_local = acesso_local

    form = await request.form()
    produto_ids = form.getlist("produto_id")
    quantidades = form.getlist("quantidade")
    valores_unitarios = form.getlist("valor_unitario")

    # Regrava os itens da reserva para permitir vários produtos/serviços.
    db.query(ReservaItem).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).delete()
    primeiro_produto = None
    for idx, produto_id in enumerate(produto_ids):
        if not produto_id:
            continue
        produto = db.get(ProdutoServico, int(produto_id))
        if not produto or produto.empresa_id != empresa.id:
            continue
        quantidade = int(quantidades[idx]) if idx < len(quantidades) and str(quantidades[idx]).isdigit() else 1
        valor_unitario = texto_para_float(valores_unitarios[idx]) if idx < len(valores_unitarios) else (
                produto.valor_base or 0)
        total_item = quantidade * valor_unitario
        db.add(ReservaItem(
            empresa_id=empresa.id,
            solicitacao_id=item.id,
            produto_id=produto.id,
            nome=produto.nome,
            descricao=produto.descricao,
            quantidade=quantidade,
            valor_unitario=valor_unitario,
            valor_total=total_item
        ))
        if primeiro_produto is None:
            primeiro_produto = produto

    item.produto_id = primeiro_produto.id if primeiro_produto else None
    contrato_padrao_id = primeiro_produto.contrato_id if primeiro_produto and primeiro_produto.contrato_id else None
    item.contrato_id = int(contrato_id) if contrato_id else contrato_padrao_id
    db.flush()
    total_itens = sum((linha.valor_total or 0) for linha in item.itens)
    valor_manual = texto_para_float(valor)
    item.valor = total_itens if total_itens > 0 else valor_manual
    item.sinal = texto_para_float(sinal)
    item.observacoes = observacoes
    if primeiro_produto and item.hora_inicio:
        item.hora_fim = somar_minutos(item.hora_inicio, primeiro_produto.duracao_minutos or 240)

    # Salvar não significa aceitar nem enviar.
    # Antes do aceite, o contrato continua como rascunho até o usuário liberar o envio.
    # Depois de um contrato aceito, qualquer edição volta para pendente de novo aceite.
    if status_reserva_confirmada(item.status):
        item.status = "aguardando_aceite"
        db.query(Agenda).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).delete()
    elif acao == "enviar" and primeiro_produto and item.contrato_id:
        item.status = "contrato_enviado"
    elif item.status not in ["contrato_enviado", "aguardando_aceite"]:
        item.status = "pre_reserva"

    db.commit()
    return RedirectResponse(f"/painel/solicitacao/{solicitacao_id}", status_code=303)


@app.post("/painel/solicitacao/{solicitacao_id}/excluir")
def excluir_solicitacao_completa(
        solicitacao_id: int,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)
    if existe_pagamento_conciliado(item):
        msg = quote("Pagamento conciliado. Chame o financeiro antes de excluir este contrato.")
        return RedirectResponse(f"/painel/solicitacao/{solicitacao_id}?erro={msg}", status_code=303)

    cliente = item.cliente
    pagamento_ids = [p.id for p in (item.pagamentos or [])]
    if pagamento_ids:
        db.query(LancamentoBanco).filter(
            LancamentoBanco.empresa_id == empresa.id,
            LancamentoBanco.pagamento_id.in_(pagamento_ids)
        ).update({LancamentoBanco.pagamento_id: None}, synchronize_session=False)
        db.query(LancamentoManualFinanceiro).filter(
            LancamentoManualFinanceiro.empresa_id == empresa.id,
            LancamentoManualFinanceiro.pagamento_id.in_(pagamento_ids)
        ).update({LancamentoManualFinanceiro.pagamento_id: None}, synchronize_session=False)

    db.query(Agenda).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).delete()
    db.delete(item)
    db.flush()

    if cliente and db.query(Solicitacao).filter_by(empresa_id=empresa.id, cliente_id=cliente.id).count() == 0:
        db.delete(cliente)

    db.commit()
    return RedirectResponse("/painel", status_code=303)


@app.post("/painel/solicitacao/{solicitacao_id}/aceite-manual")
def aceite_manual_solicitacao(
        request: Request,
        solicitacao_id: int,
        observacao_aceite: str = Form(...),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)

    tem_itens = db.query(ReservaItem).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).count() > 0
    if not item.contrato_id or not tem_itens:
        raise HTTPException(400, "Para aceitar manualmente, o contrato precisa ter modelo e pelo menos um item.")

    motivo = observacao_aceite.strip()
    if not motivo:
        raise HTTPException(400, "Informe o motivo do aceite manual.")

    usuario = request.session.get("usuario_sistema", "Usuário")
    item.status = "reserva_confirmada"
    item.aceite_em = agora_utc()
    item.aprovado_em = item.aceite_em
    registro = f"Aceite manual por {usuario}: {motivo}"
    item.observacoes = (item.observacoes + "\n\n" if item.observacoes else "") + registro

    if item.hora_inicio and not item.hora_fim and item.produto and item.produto.duracao_minutos:
        item.hora_fim = somar_minutos(item.hora_inicio, item.produto.duracao_minutos)
    criar_eventos_operacionais(db, item)
    db.commit()
    return RedirectResponse(f"/painel/solicitacao/{solicitacao_id}", status_code=303)


@app.get("/painel/contrato-novo", response_class=HTMLResponse)
def contrato_novo_form(request: Request, busca: str = "", db: Session = Depends(get_db),
                       empresa: Empresa = Depends(empresa_logada)):
    produtos = db.query(ProdutoServico).filter_by(empresa_id=empresa.id, ativo=True).order_by(ProdutoServico.nome).all()
    contratos = db.query(Contrato).filter_by(empresa_id=empresa.id, ativo=True).order_by(Contrato.nome).all()
    busca_limpa = limpar_identificador(busca)
    form = {}
    if busca_limpa:
        # A busca da barra inferior normalmente é telefone ou CPF.
        # Deixamos o dado já preenchido para o contrato nascer sem retrabalho.
        if len(busca_limpa) == 11 and not busca_limpa.startswith(("2", "3", "4", "5", "6", "7", "8", "9")):
            form["cpf"] = busca_limpa
        else:
            form["telefone"] = busca_limpa
    return templates.TemplateResponse("admin/contrato_novo.html", {
        "request": request,
        "empresa": empresa,
        "produtos": produtos,
        "contratos": contratos,
        "erro": "",
        "form": form
    })


def celular_brasileiro_valido(valor: str) -> bool:
    numero = limpar_identificador(valor)
    if numero.startswith("55") and len(numero) == 13:
        numero = numero[2:]
    return len(numero) == 11 and numero[2] == "9" and numero[:2] != "00"


def endereco_cliente_payload(item: EnderecoCliente) -> dict:
    return {
        "id": item.id, "apelido": item.apelido or "", "endereco": item.endereco or "",
        "numero": item.numero or "", "complemento": item.complemento or "",
        "bairro": item.bairro or "", "cidade": item.cidade or "",
        "estado": item.estado or "", "cep": item.cep or ""
    }


def salvar_endereco_cliente(db: Session, empresa_id: int, cliente_id: int, endereco: str, numero: str = "",
                            complemento: str = "", bairro: str = "", cidade: str = "",
                            estado: str = "", cep: str = ""):
    dados = {
        "endereco": (endereco or "").strip(), "numero": (numero or "").strip(),
        "complemento": (complemento or "").strip(), "bairro": (bairro or "").strip(),
        "cidade": (cidade or "").strip(), "estado": (estado or "").strip(), "cep": (cep or "").strip(),
    }
    if not dados["endereco"]:
        return None
    existente = db.query(EnderecoCliente).filter_by(empresa_id=empresa_id, cliente_id=cliente_id, **dados).first()
    if existente:
        existente.ativo = True
        return existente
    item = EnderecoCliente(empresa_id=empresa_id, cliente_id=cliente_id, **dados)
    db.add(item)
    return item


@app.get("/e/{slug}/api/clientes/por-telefone")
def api_publico_cliente_por_telefone(slug: str, telefone: str, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(404)
    tel = limpar_identificador(telefone)
    if tel.startswith("55") and len(tel) == 13:
        tel = tel[2:]
    if len(tel) != 11 or tel[2] != "9":
        return JSONResponse({"encontrado": False, "enderecos": []})
    clientes = db.query(Cliente).filter(Cliente.empresa_id == empresa.id, or_(Cliente.telefone == tel, Cliente.identificador == tel)).all()
    if not clientes:
        return JSONResponse({"encontrado": False, "enderecos": []})
    cliente = clientes[0]
    ids = [c.id for c in clientes]
    enderecos = db.query(EnderecoCliente).filter(EnderecoCliente.empresa_id == empresa.id, EnderecoCliente.cliente_id.in_(ids), EnderecoCliente.ativo == True).order_by(EnderecoCliente.atualizado_em.desc()).all()
    if not enderecos:
        for c in clientes:
            if c.endereco:
                salvar_endereco_cliente(db, empresa.id, c.id, c.endereco, c.numero, c.complemento, c.bairro, c.cidade, c.estado, c.cep)
        db.commit()
        enderecos = db.query(EnderecoCliente).filter(EnderecoCliente.empresa_id == empresa.id, EnderecoCliente.cliente_id.in_(ids), EnderecoCliente.ativo == True).order_by(EnderecoCliente.atualizado_em.desc()).all()
    return JSONResponse({"encontrado": True, "quantidade": len(clientes), "cliente": {"id": cliente.id, "nome": cliente.nome or '', "cpf": cliente.cpf or '', "cnpj": cliente.cnpj or '', "email": cliente.email or '', "telefone": cliente.telefone or tel}, "enderecos": [endereco_cliente_payload(e) for e in enderecos[:10]]})


@app.get("/api/clientes/por-telefone")
def api_cliente_por_telefone(request: Request, telefone: str, db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)):
    tel = limpar_identificador(telefone)
    if tel.startswith("55") and len(tel) == 13:
        tel = tel[2:]
    if len(tel) < 10:
        return JSONResponse({"encontrado": False, "enderecos": []})
    clientes = db.query(Cliente).filter(Cliente.empresa_id == empresa.id, or_(Cliente.telefone == tel, Cliente.identificador == tel)).all()
    if not clientes:
        return JSONResponse({"encontrado": False, "enderecos": []})
    cliente = clientes[0]
    ids = [c.id for c in clientes]
    enderecos = db.query(EnderecoCliente).filter(EnderecoCliente.empresa_id == empresa.id, EnderecoCliente.cliente_id.in_(ids), EnderecoCliente.ativo == True).order_by(EnderecoCliente.atualizado_em.desc()).all()
    # Compatibilidade: transforma o endereço antigo do cliente em endereço oficial na primeira consulta.
    if not enderecos:
        for c in clientes:
            if c.endereco:
                salvar_endereco_cliente(db, empresa.id, c.id, c.endereco, c.numero, c.complemento, c.bairro, c.cidade, c.estado, c.cep)
        db.commit()
        enderecos = db.query(EnderecoCliente).filter(EnderecoCliente.empresa_id == empresa.id, EnderecoCliente.cliente_id.in_(ids), EnderecoCliente.ativo == True).order_by(EnderecoCliente.atualizado_em.desc()).all()
    return JSONResponse({"encontrado": True, "quantidade": len(clientes), "cliente": {"id": cliente.id, "nome": cliente.nome or '', "cpf": cliente.cpf or '', "cnpj": cliente.cnpj or '', "email": cliente.email or '', "telefone": cliente.telefone or tel}, "enderecos": [endereco_cliente_payload(e) for e in enderecos[:10]]})


@app.post("/painel/contrato-novo")
def contrato_novo_salvar(
        request: Request,
        nome: str = Form(""),
        telefone: str = Form(""),
        whatsapp_brasil: str = Form(""),
        cpf: str = Form(""),
        cnpj: str = Form(""),
        email: str = Form(""),
        endereco: str = Form(""),
        numero: str = Form(""),
        complemento: str = Form(""),
        bairro: str = Form(""),
        cidade: str = Form(""),
        estado: str = Form(""),
        cep: str = Form(""),
        produto_id: str = Form(""),
        contrato_id: str = Form(""),
        data_evento: str = Form(""),
        hora_inicio: str = Form(""),
        retirada_obrigatoria: str = Form(""),
        retirada_data: str = Form(""),
        retirada_hora: str = Form(""),
        valor: str = Form("0"),
        sinal: str = Form("0"),
        local_nome: str = Form(""),
        local: str = Form(""),
        acesso_local: str = Form(""),
        local_responsavel_nome: str = Form(""),
        local_responsavel_telefone: str = Form(""),
        observacoes: str = Form(""),
        modo_criacao: str = Form("whatsapp"),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    telefone_limpo = limpar_identificador(telefone)
    cpf_limpo = limpar_identificador(cpf)
    cnpj_limpo = limpar_identificador(cnpj)
    identificador = cpf_limpo or cnpj_limpo or telefone_limpo or uuid.uuid4().hex[:12]

    produtos = db.query(ProdutoServico).filter_by(empresa_id=empresa.id, ativo=True).order_by(ProdutoServico.nome).all()
    contratos = db.query(Contrato).filter_by(empresa_id=empresa.id, ativo=True).order_by(Contrato.nome).all()
    form = {
        "nome": nome, "telefone": telefone, "whatsapp_brasil": whatsapp_brasil,
        "cpf": cpf, "cnpj": cnpj, "email": email, "endereco": endereco,
        "numero": numero, "complemento": complemento, "bairro": bairro,
        "cidade": cidade, "estado": estado, "cep": cep, "produto_id": produto_id,
        "contrato_id": contrato_id, "data_evento": data_evento, "hora_inicio": hora_inicio,
        "retirada_obrigatoria": retirada_obrigatoria, "retirada_data": retirada_data,
        "retirada_hora": retirada_hora, "valor": valor, "sinal": sinal,
        "local_nome": local_nome, "local": local, "acesso_local": acesso_local,
        "local_responsavel_nome": local_responsavel_nome,
        "local_responsavel_telefone": local_responsavel_telefone,
        "observacoes": observacoes, "modo_criacao": modo_criacao,
    }

    def render_erro(mensagem: str):
        return templates.TemplateResponse("admin/contrato_novo.html", {
            "request": request,
            "empresa": empresa,
            "produtos": produtos,
            "contratos": contratos,
            "erro": mensagem,
            "form": form
        }, status_code=400)

    if not nome.strip():
        return render_erro("Informe o nome do cliente.")
    if not telefone.strip():
        return render_erro("Informe o WhatsApp ou telefone do cliente.")
    if whatsapp_brasil and not celular_brasileiro_valido(telefone):
        return render_erro("Informe um WhatsApp brasileiro válido no formato (DD) 9XXXX-XXXX.")
    if cpf_limpo and not cpf_valido(cpf_limpo):
        return render_erro("CPF inválido.")
    if cnpj_limpo and not cnpj_valido(cnpj_limpo):
        return render_erro("CNPJ inválido.")
    if not endereco.strip() or not numero.strip() or not bairro.strip():
        return render_erro("Informe o endereço, número e bairro.")

    cadastro_cliente = modo_criacao == "cadastro"
    if not cadastro_cliente and not celular_brasileiro_valido(local_responsavel_telefone):
        return render_erro("Informe um WhatsApp brasileiro válido para o responsável no local.")
    if not cadastro_cliente and not local_responsavel_nome.strip():
        return render_erro("Informe o nome do responsável no local.")
    if not cadastro_cliente and (not data_evento or not hora_inicio):
        return render_erro("Informe a data e a hora do evento.")
    if not cadastro_cliente and not hora_meia_em_meia_valida(hora_inicio):
        return render_erro("A hora precisa estar em intervalo de 30 minutos. Exemplo: 18:00 ou 18:30.")

    data_evento_obj = datetime.strptime(data_evento, "%Y-%m-%d").date() if data_evento else None
    duplicado_q = None
    if not cadastro_cliente:
        duplicado_q = db.query(Solicitacao).join(Cliente, Solicitacao.cliente_id == Cliente.id).filter(
            Solicitacao.empresa_id == empresa.id,
            Solicitacao.data_evento == data_evento_obj,
            ~Solicitacao.status.in_(["cancelada", "cancelado_cliente", "rejeitada"])
        )
    condicoes = []
    if telefone_limpo:
        condicoes.append(Cliente.telefone == telefone_limpo)
        condicoes.append(Cliente.identificador == telefone_limpo)
    if cpf_limpo:
        condicoes.append(Cliente.cpf == cpf_limpo)
        condicoes.append(Cliente.identificador == cpf_limpo)
    if cnpj_limpo:
        condicoes.append(Cliente.cnpj == cnpj_limpo)
        condicoes.append(Cliente.identificador == cnpj_limpo)
    from sqlalchemy import or_
    if condicoes and duplicado_q is not None:
        duplicado = duplicado_q.filter(or_(*condicoes)).first()
        if duplicado:
            return render_erro(
                f"Já existe uma reserva/contrato para este telefone/CPF/CNPJ nesta data: #{duplicado.id} - {duplicado.cliente.nome}.")

    cliente = None
    if telefone_limpo:
        cliente = db.query(Cliente).filter(Cliente.empresa_id == empresa.id, or_(Cliente.telefone == telefone_limpo, Cliente.identificador == telefone_limpo)).first()
    if not cliente:
        cliente = db.query(Cliente).filter_by(empresa_id=empresa.id, identificador=identificador).first()
    if not cliente:
        cliente = Cliente(empresa_id=empresa.id, identificador=identificador)
        db.add(cliente)

    cliente.nome = nome.strip()
    cliente.telefone = telefone_limpo or telefone.strip()
    cliente.cpf = cpf_limpo
    cliente.cnpj = cnpj_limpo
    cliente.email = email.strip()
    cliente.endereco = endereco.strip()
    cliente.numero = numero.strip()
    cliente.complemento = complemento.strip()
    cliente.bairro = bairro.strip()
    cliente.cidade = cidade.strip()
    cliente.estado = estado.strip()
    cliente.cep = cep.strip()
    cliente.observacoes = observacoes.strip()
    db.flush()
    salvar_endereco_cliente(db, empresa.id, cliente.id, endereco, numero, complemento, bairro, cidade, estado, cep)

    if cadastro_cliente:
        db.commit()
        return RedirectResponse(f"/painel/cliente/{cliente.id}?cadastro=salvo", status_code=303)

    produto = db.get(ProdutoServico, int(produto_id)) if produto_id else None
    if produto and produto.empresa_id != empresa.id:
        raise HTTPException(404)
    if modo_criacao == "manual" and not produto:
        return render_erro("No contrato manual, informe pelo menos um item principal.")

    inicio_obj = datetime.strptime(hora_inicio, "%H:%M").time()
    retirada_obrigatoria_bool = bool(retirada_obrigatoria)
    retirada_data_obj = datetime.strptime(retirada_data, "%Y-%m-%d").date() if retirada_data else data_evento_obj
    retirada_hora_obj = datetime.strptime(retirada_hora, "%H:%M").time() if retirada_hora else None
    valor_float = texto_para_float(valor)
    sinal_float = texto_para_float(sinal)
    manual = modo_criacao == "manual"

    item = Solicitacao(
        empresa_id=empresa.id,
        cliente_id=cliente.id,
        produto_id=produto.id if produto else None,
        contrato_id=int(contrato_id) if contrato_id else (produto.contrato_id if produto and produto.contrato_id else None),
        data_evento=data_evento_obj,
        hora_inicio=inicio_obj,
        hora_fim=somar_minutos(inicio_obj, produto.duracao_minutos or 240) if produto else None,
        retirada_obrigatoria=retirada_obrigatoria_bool,
        retirada_data=retirada_data_obj if retirada_obrigatoria_bool else None,
        retirada_hora=retirada_hora_obj,
        bairro=bairro.strip(),
        local=endereco.strip(),
        local_nome=local_nome.strip(),
        local_responsavel_nome=local_responsavel_nome.strip(),
        local_responsavel_telefone=limpar_identificador(
            local_responsavel_telefone) or local_responsavel_telefone.strip(),
        acesso_local=acesso_local.strip(),
        valor=valor_float,
        sinal=sinal_float,
        observacoes=observacoes.strip(),
        status="reserva_confirmada" if manual else ("aguardando_aceite" if (contrato_id or (produto and produto.contrato_id)) and produto else "pre_reserva"),
        aprovado_em=agora_utc() if manual else None,
        aceite_em=agora_utc() if manual else None,
        sinal_recebido=True if manual and sinal_float > 0 else False,
        valor_pago=sinal_float if manual and sinal_float > 0 else 0,
        pagamento_confirmado_em=agora_utc() if manual and sinal_float > 0 else None
    )
    if item.retirada_obrigatoria and not item.retirada_hora:
        item.retirada_hora = item.hora_fim or item.hora_inicio

    db.add(item)
    db.flush()

    if produto:
        db.add(ReservaItem(
            empresa_id=empresa.id,
            solicitacao_id=item.id,
            produto_id=produto.id,
            nome=produto.nome,
            descricao=produto.descricao,
            quantidade=1,
            valor_unitario=valor_float,
            valor_total=valor_float
        ))

    if manual and sinal_float > 0:
        db.add(Pagamento(
            empresa_id=empresa.id,
            solicitacao_id=item.id,
            data_pagamento=date.today(),
            valor=sinal_float,
            forma_pagamento="pix",
            comprovante_no_nome_cliente=True,
            nome_comprovante=cliente.nome,
            observacoes="Sinal informado no contrato manual.",
            usuario_registro=request.session.get("usuario_sistema", "Usuário")
        ))

    db.commit()
    return RedirectResponse(f"/painel/solicitacao/{item.id}", status_code=303)


def awaitable_form_fallback(request: Request) -> dict:
    # Em rotas síncronas o FastAPI já consumiu os campos do Form.
    # Mantemos um dicionário vazio apenas para o template não quebrar em caso de erro.
    return {}


def form_solicitacao_completo(item: Solicitacao) -> dict:
    """Monta o formulário único com todos os dados já preenchidos para edição completa."""
    cliente = item.cliente
    return {
        "nome": cliente.nome if cliente else "",
        "telefone": cliente.telefone if cliente else "",
        "cpf": cliente.cpf if cliente else "",
        "cnpj": cliente.cnpj if cliente else "",
        "email": cliente.email if cliente else "",
        "endereco": cliente.endereco if cliente else "",
        "numero": cliente.numero if cliente else "",
        "complemento": cliente.complemento if cliente else "",
        "bairro": cliente.bairro if cliente else item.bairro or "",
        "cidade": cliente.cidade if cliente else "",
        "estado": cliente.estado if cliente else "",
        "cep": cliente.cep if cliente else "",
        "data_evento": item.data_evento.isoformat() if item.data_evento else "",
        "hora_inicio": item.hora_inicio.strftime("%H:%M") if item.hora_inicio else "",
        "retirada_obrigatoria": "1" if retirada_obrigatoria_ativa(item) else "",
        "retirada_data": item.retirada_data.isoformat() if item.retirada_data else (item.data_evento.isoformat() if item.data_evento else ""),
        "retirada_hora": item.retirada_hora.strftime("%H:%M") if item.retirada_hora else (item.hora_fim.strftime("%H:%M") if item.hora_fim else ""),
        "produto_id": str(item.produto_id or ""),
        "contrato_id": str(item.contrato_id or ""),
        "valor": moeda_br(item.valor or 0),
        "sinal": moeda_br(item.sinal or 0),
        "local_nome": item.local_nome or "",
        "local": item.local or "",
        "acesso_local": item.acesso_local or "",
        "local_responsavel_nome": item.local_responsavel_nome or "",
        "local_responsavel_telefone": item.local_responsavel_telefone or "",
        "observacoes": item.observacoes or "",
        "modo_criacao": "manual",
    }


@app.get("/painel/solicitacao/{solicitacao_id}/editar-completo", response_class=HTMLResponse)
def editar_solicitacao_completa(
        solicitacao_id: int,
        request: Request,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)

    produtos = db.query(ProdutoServico).filter_by(empresa_id=empresa.id, ativo=True).order_by(ProdutoServico.nome).all()
    contratos = db.query(Contrato).filter_by(empresa_id=empresa.id, ativo=True).order_by(Contrato.nome).all()
    return templates.TemplateResponse("admin/contrato_novo.html", {
        "request": request,
        "empresa": empresa,
        "produtos": produtos,
        "contratos": contratos,
        "erro": "",
        "form": form_solicitacao_completo(item),
        "modo_edicao": True,
        "item": item,
    })


@app.post("/painel/solicitacao/{solicitacao_id}/editar-completo")
def salvar_solicitacao_completa(
        solicitacao_id: int,
        request: Request,
        nome: str = Form(""),
        telefone: str = Form(""),
        cpf: str = Form(""),
        cnpj: str = Form(""),
        email: str = Form(""),
        endereco: str = Form(""),
        numero: str = Form(""),
        complemento: str = Form(""),
        bairro: str = Form(""),
        cidade: str = Form(""),
        estado: str = Form(""),
        cep: str = Form(""),
        produto_id: str = Form(""),
        contrato_id: str = Form(""),
        data_evento: str = Form(""),
        hora_inicio: str = Form(""),
        retirada_obrigatoria: str = Form(""),
        retirada_data: str = Form(""),
        retirada_hora: str = Form(""),
        valor: str = Form("0"),
        sinal: str = Form("0"),
        local_nome: str = Form(""),
        local: str = Form(""),
        acesso_local: str = Form(""),
        local_responsavel_nome: str = Form(""),
        local_responsavel_telefone: str = Form(""),
        observacoes: str = Form(""),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id or not item.cliente:
        raise HTTPException(404)

    produtos = db.query(ProdutoServico).filter_by(empresa_id=empresa.id, ativo=True).order_by(ProdutoServico.nome).all()
    contratos = db.query(Contrato).filter_by(empresa_id=empresa.id, ativo=True).order_by(Contrato.nome).all()
    form = dict(
        nome=nome, telefone=telefone, cpf=cpf, cnpj=cnpj, email=email, endereco=endereco,
        numero=numero, complemento=complemento, bairro=bairro, cidade=cidade, estado=estado,
        cep=cep, produto_id=produto_id, contrato_id=contrato_id, data_evento=data_evento,
        hora_inicio=hora_inicio, retirada_obrigatoria=retirada_obrigatoria,
        retirada_data=retirada_data, retirada_hora=retirada_hora,
        valor=valor, sinal=sinal, local_nome=local_nome, local=local,
        acesso_local=acesso_local, local_responsavel_nome=local_responsavel_nome,
        local_responsavel_telefone=local_responsavel_telefone, observacoes=observacoes,
        modo_criacao="manual"
    )

    def render_erro(mensagem: str):
        return templates.TemplateResponse("admin/contrato_novo.html", {
            "request": request, "empresa": empresa, "produtos": produtos, "contratos": contratos,
            "erro": mensagem, "form": form, "modo_edicao": True, "item": item
        }, status_code=400)

    telefone_limpo = limpar_identificador(telefone)
    cpf_limpo = limpar_identificador(cpf)
    cnpj_limpo = limpar_identificador(cnpj)

    if not nome.strip():
        return render_erro("Informe o nome do cliente.")
    if not telefone_limpo and not cpf_limpo and not cnpj_limpo:
        return render_erro("Informe pelo menos telefone, CPF ou CNPJ.")
    if not hora_meia_em_meia_valida(hora_inicio):
        return render_erro("A hora precisa estar em intervalo de 30 minutos. Exemplo: 18:00 ou 18:30.")
    if cpf_limpo and not cpf_valido(cpf_limpo):
        return render_erro("CPF inválido.")
    if cnpj_limpo and not cnpj_valido(cnpj_limpo):
        return render_erro("CNPJ inválido.")

    produto = db.get(ProdutoServico, int(produto_id)) if produto_id else None
    if produto and produto.empresa_id != empresa.id:
        raise HTTPException(404)

    cliente = item.cliente
    cliente.nome = nome.strip()
    cliente.telefone = telefone_limpo or telefone.strip()
    cliente.cpf = cpf_limpo
    cliente.cnpj = cnpj_limpo
    cliente.email = email.strip()
    cliente.endereco = endereco.strip()
    cliente.numero = numero.strip()
    cliente.complemento = complemento.strip()
    cliente.bairro = bairro.strip()
    cliente.cidade = cidade.strip()
    cliente.estado = estado.strip()
    cliente.cep = cep.strip()

    inicio_obj = datetime.strptime(hora_inicio, "%H:%M").time()
    data_evento_obj = datetime.strptime(data_evento, "%Y-%m-%d").date()
    retirada_obrigatoria_bool = bool(retirada_obrigatoria)
    retirada_data_obj = datetime.strptime(retirada_data, "%Y-%m-%d").date() if retirada_data else data_evento_obj
    retirada_hora_obj = datetime.strptime(retirada_hora, "%H:%M").time() if retirada_hora else None
    valor_float = texto_para_float(valor)
    sinal_float = texto_para_float(sinal)

    item.produto_id = produto.id if produto else None
    item.contrato_id = int(contrato_id) if contrato_id else (produto.contrato_id if produto and produto.contrato_id else None)
    item.data_evento = data_evento_obj
    item.hora_inicio = inicio_obj
    item.hora_fim = somar_minutos(inicio_obj, produto.duracao_minutos or 240) if produto else item.hora_fim
    item.retirada_obrigatoria = retirada_obrigatoria_bool
    item.retirada_data = retirada_data_obj if retirada_obrigatoria_bool else None
    item.retirada_hora = retirada_hora_obj or (item.hora_fim or item.hora_inicio if retirada_obrigatoria_bool else None)
    item.bairro = bairro.strip()
    item.local = local.strip() or endereco.strip()
    item.local_nome = local_nome.strip()
    item.local_responsavel_nome = local_responsavel_nome.strip()
    item.local_responsavel_telefone = limpar_identificador(
        local_responsavel_telefone) or local_responsavel_telefone.strip()
    item.acesso_local = acesso_local.strip()
    item.valor = valor_float
    item.sinal = sinal_float
    item.observacoes = observacoes.strip()

    if produto:
        item_principal = item.itens[0] if item.itens else None
        if not item_principal:
            item_principal = ReservaItem(empresa_id=empresa.id, solicitacao_id=item.id, quantidade=1)
            db.add(item_principal)
        item_principal.produto_id = produto.id
        item_principal.nome = produto.nome
        item_principal.descricao = produto.descricao
        item_principal.valor_unitario = valor_float
        item_principal.valor_total = valor_float

    criar_eventos_operacionais(db, item)
    db.commit()
    return RedirectResponse(f"/painel/solicitacao/{item.id}", status_code=303)


@app.get("/painel/clientes", response_class=HTMLResponse)
def clientes(request: Request, busca: str = "", db: Session = Depends(get_db),
             empresa: Empresa = Depends(empresa_logada)):
    termo_texto = (busca or "").strip()
    termo_limpo = limpar_identificador(busca)
    itens = []
    if termo_texto:
        condicoes = [
            Cliente.nome.ilike(f"%{termo_texto}%"),
            Cliente.email.ilike(f"%{termo_texto}%"),
        ]
        if termo_limpo:
            condicoes.extend([
                Cliente.cpf.contains(termo_limpo),
                Cliente.cnpj.contains(termo_limpo),
                Cliente.telefone.contains(termo_limpo),
                Cliente.identificador.contains(termo_limpo),
            ])
        itens = (
            db.query(Cliente)
            .filter(Cliente.empresa_id == empresa.id)
            .filter(or_(*condicoes))
            .order_by(Cliente.nome)
            .all()
        )
    return templates.TemplateResponse("admin/clientes.html",
                                      {"request": request, "empresa": empresa, "itens": itens, "busca": busca})


@app.get("/painel/cliente/{cliente_id}", response_class=HTMLResponse)
def cliente_detalhe(cliente_id: int, request: Request, db: Session = Depends(get_db),
                    empresa: Empresa = Depends(empresa_logada)):
    cliente = db.get(Cliente, cliente_id)
    if not cliente or cliente.empresa_id != empresa.id:
        raise HTTPException(404)
    equipamentos = db.query(EquipamentoCliente).filter_by(empresa_id=empresa.id, cliente_id=cliente.id).order_by(
        EquipamentoCliente.nome).all()
    solicitacoes = db.query(Solicitacao).filter_by(empresa_id=empresa.id, cliente_id=cliente.id).order_by(
        Solicitacao.criado_em.desc()).all()
    produtos = db.query(ProdutoServico).filter_by(empresa_id=empresa.id, ativo=True).order_by(ProdutoServico.nome).all()
    contratos = db.query(Contrato).filter_by(empresa_id=empresa.id, ativo=True).order_by(Contrato.nome).all()
    return templates.TemplateResponse("admin/cliente_detalhe.html",
                                      {"request": request, "empresa": empresa, "cliente": cliente,
                                       "equipamentos": equipamentos, "solicitacoes": solicitacoes, "produtos": produtos,
                                       "contratos": contratos})


@app.post("/painel/solicitacao/{solicitacao_id}/usar-como-base")
def usar_solicitacao_como_base(
        solicitacao_id: int,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    origem = db.get(Solicitacao, solicitacao_id)
    if not origem or origem.empresa_id != empresa.id:
        raise HTTPException(404)

    nova = Solicitacao(
        empresa_id=empresa.id,
        cliente_id=origem.cliente_id,
        produto_id=origem.produto_id,
        contrato_id=origem.contrato_id,
        data_evento=origem.data_evento,
        hora_inicio=origem.hora_inicio,
        hora_fim=origem.hora_fim,
        bairro=origem.bairro,
        local=origem.local,
        local_nome=origem.local_nome,
        local_responsavel_nome=origem.local_responsavel_nome,
        local_responsavel_telefone=origem.local_responsavel_telefone,
        acesso_local=origem.acesso_local,
        valor=origem.valor,
        sinal=origem.sinal,
        valor_pago=0,
        sinal_recebido=False,
        observacoes=origem.observacoes,
        status="pre_reserva",
    )
    db.add(nova)
    db.flush()

    for it in origem.itens:
        db.add(ReservaItem(
            empresa_id=empresa.id,
            solicitacao_id=nova.id,
            produto_id=it.produto_id,
            nome=it.nome,
            descricao=it.descricao,
            quantidade=it.quantidade,
            valor_unitario=it.valor_unitario,
            valor_total=it.valor_total,
        ))

    db.commit()
    return RedirectResponse(f"/painel/solicitacao/{nova.id}/editar-completo", status_code=303)


@app.post("/painel/cliente/{cliente_id}/dados")
def atualizar_cliente_dados(
        cliente_id: int,
        nome: str = Form(""),
        telefone: str = Form(""),
        cpf: str = Form(""),
        cnpj: str = Form(""),
        email: str = Form(""),
        endereco: str = Form(""),
        numero: str = Form(""),
        complemento: str = Form(""),
        bairro: str = Form(""),
        cidade: str = Form(""),
        estado: str = Form(""),
        cep: str = Form(""),
        observacoes: str = Form(""),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    cliente = db.get(Cliente, cliente_id)
    if not cliente or cliente.empresa_id != empresa.id:
        raise HTTPException(404)

    cliente.nome = nome.strip() or cliente.nome
    cliente.telefone = limpar_identificador(telefone)
    cliente.cpf = limpar_identificador(cpf)
    cliente.cnpj = limpar_identificador(cnpj)
    cliente.email = email.strip()
    cliente.endereco = endereco.strip()
    cliente.numero = numero.strip()
    cliente.complemento = complemento.strip()
    cliente.bairro = bairro.strip()
    cliente.cidade = cidade.strip()
    cliente.estado = estado.strip()
    cliente.cep = limpar_identificador(cep)
    cliente.observacoes = observacoes.strip()

    if empresa.identificador_principal == "cpf" and cliente.cpf:
        cliente.identificador = cliente.cpf
    elif empresa.identificador_principal == "cnpj" and cliente.cnpj:
        cliente.identificador = cliente.cnpj
    elif cliente.telefone:
        cliente.identificador = cliente.telefone

    db.commit()
    return RedirectResponse(f"/painel/cliente/{cliente.id}", status_code=303)


@app.post("/painel/cliente/{cliente_id}/pre-reserva-rapida")
def criar_pre_reserva_rapida(
        cliente_id: int,
        produto_id: str = Form(""),
        contrato_id: str = Form(""),
        data_evento: str = Form(""),
        hora_inicio: str = Form(""),
        valor: str = Form("0"),
        sinal: str = Form("0"),
        local_nome: str = Form(""),
        local: str = Form(""),
        local_responsavel_nome: str = Form(""),
        local_responsavel_telefone: str = Form(""),
        observacoes: str = Form(""),
        acao: str = Form("salvar"),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    cliente = db.get(Cliente, cliente_id)
    if not cliente or cliente.empresa_id != empresa.id:
        raise HTTPException(404)
    produto = db.get(ProdutoServico, int(produto_id)) if produto_id else None
    if produto and produto.empresa_id != empresa.id:
        raise HTTPException(404)
    inicio_obj = datetime.strptime(hora_inicio, "%H:%M").time()
    item = Solicitacao(
        empresa_id=empresa.id,
        cliente_id=cliente.id,
        produto_id=produto.id if produto else None,
        contrato_id=int(contrato_id) if contrato_id else (produto.contrato_id if produto and produto.contrato_id else None),
        data_evento=datetime.strptime(data_evento, "%Y-%m-%d").date(),
        hora_inicio=inicio_obj,
        hora_fim=somar_minutos(inicio_obj, produto.duracao_minutos or 240) if produto else None,
        bairro=cliente.bairro,
        local=local,
        local_nome=local_nome,
        local_responsavel_nome=local_responsavel_nome,
        local_responsavel_telefone=local_responsavel_telefone,
        valor=texto_para_float(valor),
        sinal=texto_para_float(sinal),
        observacoes=observacoes,
        status="aguardando_aceite"
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    if produto:
        db.add(ReservaItem(
            empresa_id=empresa.id,
            solicitacao_id=item.id,
            produto_id=produto.id,
            nome=produto.nome,
            descricao=produto.descricao,
            quantidade=1,
            valor_unitario=texto_para_float(valor),
            valor_total=texto_para_float(valor)
        ))
        db.commit()
    return RedirectResponse(f"/painel/solicitacao/{item.id}", status_code=303)


@app.post("/painel/cliente/{cliente_id}/equipamentos")
def salvar_equipamento_cliente(
        cliente_id: int,
        nome: str = Form(...), marca: str = Form(""), modelo: str = Form(""), numero_serie: str = Form(""),
        observacoes: str = Form(""),
        acao: str = Form("salvar"),
        db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)
):
    cliente = db.get(Cliente, cliente_id)
    if not cliente or cliente.empresa_id != empresa.id:
        raise HTTPException(404)
    db.add(EquipamentoCliente(
        empresa_id=empresa.id, cliente_id=cliente.id, nome=nome.strip(), marca=marca.strip(),
        modelo=modelo.strip(), numero_serie=numero_serie.strip(), observacoes=observacoes.strip()
    ))
    db.commit()
    return RedirectResponse(f"/painel/cliente/{cliente_id}", status_code=303)


def usuario_pode_financeiro(request: Request, empresa: Empresa, db: Session) -> bool:
    usuario_sistema = request.session.get("usuario_sistema")
    if usuario_sistema and empresa.usuario_admin and usuario_sistema.lower() == empresa.usuario_admin.lower():
        return True
    usuario = db.query(UsuarioEmpresa).filter_by(empresa_id=empresa.id,
                                                 usuario=usuario_sistema).first() if usuario_sistema else None
    return True if not usuario else bool(getattr(usuario, "visualiza_financeiro", True))


def garantir_contas_financeiras(db: Session, empresa_id: int):
    contas = db.query(ContaFinanceira).filter_by(empresa_id=empresa_id).all()
    if not contas:
        for nome, tipo in [("Banco Principal", "banco"), ("Dinheiro", "dinheiro"), ("Cartão", "cartao")]:
            db.add(ContaFinanceira(empresa_id=empresa_id, nome=nome, tipo=tipo, saldo_inicial=0))
        db.commit()
    return db.query(ContaFinanceira).filter_by(empresa_id=empresa_id, ativa=True).order_by(ContaFinanceira.id).all()


def parse_valor_banco(valor) -> float:
    if valor is None:
        return 0.0
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    if not texto:
        return 0.0
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except Exception:
        return 0.0


def parse_data_banco(valor):
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except Exception:
            pass
    return None


def texto_normalizado_financeiro(valor: str) -> str:
    texto = (valor or "").strip().lower()
    trocas = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüçñ", "aaaaaeeeeiiiiooooouuuucn")
    texto = texto.translate(trocas)
    texto = re.sub(r"\s+", " ", texto)
    return texto


def categoria_sugerida(historico: str, valor: float) -> str:
    h = texto_normalizado_financeiro(historico)
    if any(p in h for p in
           ["uber", "tim", "claro", "vivo", "light", "enel", "internet", "telefone", "google", "meta", "facebook",
            "conta azul", "mei", "simples", "taxa", "tarifa", "maquininha", "stone", "mercado pago", "nic br",
            "hospedagem", "dominio"]):
        return "empresa"
    if any(p in h for p in
           ["mercado", "farmacia", "padaria", "ifood", "restaurante", "posto", "combustivel", "condominio",
            "aluguel casa"]):
        return "casa"
    if any(p in h for p in ["agua", "aguas", "manut", "reparo", "peca", "assistencia"]):
        return "manutencao"
    if valor > 0 or "pix recebido" in h or "pix devolvido" in h:
        return "aluguel"
    return "empresa"


def hash_lancamento_banco(empresa_id: int, conta_id: int, data_lanc, historico: str, documento: str, valor: float,
                          saldo: float) -> str:
    base = "|".join([
        str(empresa_id), str(conta_id), str(data_lanc),
        texto_normalizado_financeiro(historico), texto_normalizado_financeiro(documento),
        f"{float(valor or 0):.2f}", f"{float(saldo or 0):.2f}"
    ])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def melhores_vinculos_para_banco(lancamento, pagamentos, limite=5):
    return melhores_vinculos_financeiros(
        data_lanc=lancamento.data,
        texto_lanc=lancamento.historico,
        valor_lanc=lancamento.valor,
        pagamentos=pagamentos,
        limite=limite
    )


def melhores_vinculos_para_manual(lancamento, pagamentos, limite=5):
    return melhores_vinculos_financeiros(
        data_lanc=lancamento.data,
        texto_lanc=lancamento.descricao,
        valor_lanc=lancamento.valor,
        pagamentos=pagamentos,
        limite=limite
    )


def melhores_vinculos_financeiros(data_lanc, texto_lanc, valor_lanc, pagamentos, limite=5):
    if (valor_lanc or 0) <= 0:
        return []
    hist = texto_normalizado_financeiro(texto_lanc)
    candidatos = []
    for p in pagamentos:
        nome = texto_normalizado_financeiro(
            getattr(p.solicitacao.cliente, "nome", "")) if p.solicitacao and p.solicitacao.cliente else ""
        diff_valor = abs(float(valor_lanc or 0) - float(p.valor or 0))
        diff_dias = abs((data_lanc - p.data_pagamento).days) if data_lanc and p.data_pagamento else 99
        nome_score = SequenceMatcher(None, hist, nome).ratio() if nome else 0
        if nome and nome in hist:
            nome_score = max(nome_score, 0.95)
        score = 0
        if diff_valor < 0.01:
            score += 100
        else:
            score += max(0, 45 - min(diff_valor, 45))
        score += max(0, 30 - min(diff_dias, 30))
        score += nome_score * 40
        if diff_valor <= 10 or diff_dias <= 3 or nome_score >= .55:
            candidatos.append({"pagamento": p, "score": score, "diff_valor": diff_valor, "diff_dias": diff_dias})
    return sorted(candidatos, key=lambda x: (-x["score"], x["diff_valor"], x["diff_dias"]))[:limite]


def ler_extrato_upload(upload: UploadFile):
    nome = upload.filename or "extrato"
    conteudo = upload.file.read()
    linhas = []
    if nome.lower().endswith(".csv"):
        texto = conteudo.decode("utf-8-sig", errors="ignore")
        amostra = texto[:2048]
        delimitador = ";" if amostra.count(";") > amostra.count(",") else ","
        leitor = csv.reader(StringIO(texto), delimiter=delimitador)
        linhas = [linha for linha in leitor]
    else:
        try:
            from openpyxl import load_workbook
        except Exception:
            raise HTTPException(400, "Para importar XLSX, instale openpyxl ou envie o extrato em CSV.")
        wb = load_workbook(BytesIO(conteudo), data_only=True)
        ws = wb.active
        linhas = [[cell for cell in row] for row in ws.iter_rows(values_only=True)]

    cabecalho_idx = None
    for idx, linha in enumerate(linhas):
        normal = [str(c or "").strip().lower() for c in linha]
        if "data" in normal and any("hist" in c for c in normal) and any("valor" in c for c in normal):
            cabecalho_idx = idx
            break
    if cabecalho_idx is None:
        raise HTTPException(400, "Não encontrei as colunas Data, Histórico, Valor e Saldo no extrato.")

    cab = [str(c or "").strip().lower() for c in linhas[cabecalho_idx]]

    def achar(nome):
        for i, c in enumerate(cab):
            if nome in c:
                return i
        return -1

    i_data = achar("data")
    i_hist = next((i for i, c in enumerate(cab) if "hist" in c), -1)
    i_doc = achar("documento")
    i_valor = achar("valor")
    i_saldo = achar("saldo")
    registros = []
    for linha in linhas[cabecalho_idx + 1:]:
        if not linha or len(linha) <= max(i_data, i_hist, i_valor):
            continue
        data_lanc = parse_data_banco(linha[i_data])
        historico = str(linha[i_hist] or "").strip()
        valor = parse_valor_banco(linha[i_valor])
        if not data_lanc or not historico:
            continue
        saldo = parse_valor_banco(linha[i_saldo]) if i_saldo >= 0 and len(linha) > i_saldo else 0
        documento = str(linha[i_doc] or "").strip() if i_doc >= 0 and len(linha) > i_doc else ""
        registros.append(
            {"data": data_lanc, "historico": historico, "documento": documento, "valor": valor, "saldo": saldo})
    return registros


def garantir_ordem_financeira(db: Session, empresa_id: int):
    # Preenche a ordem dos registros antigos. A ordem fica editável depois pelos botões ↑/↓.
    alterou = False
    for obj in db.query(LancamentoBanco).filter(LancamentoBanco.empresa_id == empresa_id,
                                                (LancamentoBanco.ordem == None) | (LancamentoBanco.ordem == 0)).all():
        obj.ordem = obj.id or 0
        alterou = True
    for obj in db.query(LancamentoManualFinanceiro).filter(LancamentoManualFinanceiro.empresa_id == empresa_id,
                                                           (LancamentoManualFinanceiro.ordem == None) | (
                                                                   LancamentoManualFinanceiro.ordem == 0)).all():
        obj.ordem = obj.id or 0
        alterou = True
    if alterou:
        db.commit()


def mover_lancamento_na_lista(db: Session, modelo, lanc, direcao: str):
    if direcao not in ["cima", "baixo"]:
        raise HTTPException(400, "Direção inválida.")
    base = db.query(modelo).filter(
        modelo.empresa_id == lanc.empresa_id,
        modelo.conta_id == lanc.conta_id,
        modelo.data == lanc.data,
    )
    if hasattr(modelo, "tipo"):
        base = base.filter(modelo.tipo == getattr(lanc, "tipo", "real"))
    linhas = base.order_by(modelo.ordem.asc(), modelo.id.asc()).all()
    pos = next((i for i, item in enumerate(linhas) if item.id == lanc.id), -1)
    if pos < 0:
        return
    destino = pos - 1 if direcao == "cima" else pos + 1
    if destino < 0 or destino >= len(linhas):
        return
    outro = linhas[destino]
    atual_ordem = lanc.ordem or lanc.id or 0
    outra_ordem = outro.ordem or outro.id or 0
    lanc.ordem, outro.ordem = outra_ordem, atual_ordem
    db.commit()


@app.get("/painel/financeiro", response_class=HTMLResponse)
def financeiro(
        request: Request,
        conta_id: int = 0,
        data_inicial: str = "",
        data_final: str = "",
        categoria: str = "",
        busca: str = "",
        status_sistema: str = "pendente",
        mes_cards: str = "",
        semana_cards: str = "",
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    if not usuario_pode_financeiro(request, empresa, db):
        raise HTTPException(403, "Usuário sem permissão para visualizar o financeiro.")

    garantir_ordem_financeira(db, empresa.id)

    contas = garantir_contas_financeiras(db, empresa.id)
    conta = db.get(ContaFinanceira, conta_id) if conta_id else (contas[0] if contas else None)

    hoje = date.today()
    data_inicial = data_inicial or hoje.replace(day=1).isoformat()
    data_final = data_final or hoje.isoformat()
    inicio = datetime.strptime(data_inicial, "%Y-%m-%d").date()
    fim = datetime.strptime(data_final, "%Y-%m-%d").date()

    # Períodos independentes dos cards: mês vigente no topo e semana vigente (segunda a domingo) no rodapé.
    def primeiro_dia_mes(valor: date) -> date:
        return valor.replace(day=1)

    def avancar_mes(valor: date, quantidade: int) -> date:
        indice = (valor.year * 12 + valor.month - 1) + quantidade
        return date(indice // 12, indice % 12 + 1, 1)

    mes_vigente = primeiro_dia_mes(hoje)
    try:
        mes_cards_inicio = datetime.strptime(mes_cards, "%Y-%m").date().replace(day=1) if mes_cards else mes_vigente
    except ValueError:
        mes_cards_inicio = mes_vigente
    mes_cards_fim = avancar_mes(mes_cards_inicio, 1) - timedelta(days=1)
    meses_cards = [avancar_mes(mes_vigente, deslocamento) for deslocamento in range(3)]

    # Semanas do mês selecionado. A primeira e a última podem ser parciais,
    # garantindo que todos os contratos do mês apareçam em exatamente uma semana.
    semanas_cards = []
    cursor_semana = mes_cards_inicio
    while cursor_semana <= mes_cards_fim:
        dias_ate_domingo = 6 - cursor_semana.weekday()
        fim_periodo = min(cursor_semana + timedelta(days=dias_ate_domingo), mes_cards_fim)
        semanas_cards.append({"inicio": cursor_semana, "fim": fim_periodo})
        cursor_semana = fim_periodo + timedelta(days=1)

    semana_cards_inicio_solicitada = None
    try:
        if semana_cards:
            semana_cards_inicio_solicitada = datetime.strptime(semana_cards, "%Y-%m-%d").date()
    except ValueError:
        semana_cards_inicio_solicitada = None

    semana_selecionada = next(
        (periodo for periodo in semanas_cards
         if periodo["inicio"] == semana_cards_inicio_solicitada),
        None
    )
    if not semana_selecionada:
        semana_selecionada = next(
            (periodo for periodo in semanas_cards
             if periodo["inicio"] <= hoje <= periodo["fim"]),
            semanas_cards[0]
        )

    semana_cards_inicio = semana_selecionada["inicio"]
    semana_cards_fim = semana_selecionada["fim"]

    q_banco = db.query(LancamentoBanco).filter(LancamentoBanco.empresa_id == empresa.id)
    q_manual_real = db.query(LancamentoManualFinanceiro).filter(
        LancamentoManualFinanceiro.empresa_id == empresa.id,
        LancamentoManualFinanceiro.tipo == "real"
    )
    q_receber = db.query(LancamentoManualFinanceiro).filter(
        LancamentoManualFinanceiro.empresa_id == empresa.id,
        LancamentoManualFinanceiro.tipo == "receber",
        LancamentoManualFinanceiro.recebido == False
    )
    if conta:
        q_banco = q_banco.filter(LancamentoBanco.conta_id == conta.id)
        q_manual_real = q_manual_real.filter(LancamentoManualFinanceiro.conta_id == conta.id)
        q_receber = q_receber.filter(LancamentoManualFinanceiro.conta_id == conta.id)
    if data_inicial:
        q_banco = q_banco.filter(LancamentoBanco.data >= inicio)
        q_manual_real = q_manual_real.filter(LancamentoManualFinanceiro.data >= inicio)
        q_receber = q_receber.filter(LancamentoManualFinanceiro.data >= inicio)
    if data_final:
        q_banco = q_banco.filter(LancamentoBanco.data <= fim)
        q_manual_real = q_manual_real.filter(LancamentoManualFinanceiro.data <= fim)
        q_receber = q_receber.filter(LancamentoManualFinanceiro.data <= fim)
    if categoria == "sem_categoria":
        q_banco = q_banco.filter(or_(LancamentoBanco.categoria == None, LancamentoBanco.categoria == ""))
        q_manual_real = q_manual_real.filter(or_(
            LancamentoManualFinanceiro.categoria == None,
            LancamentoManualFinanceiro.categoria == ""
        ))
        q_receber = q_receber.filter(or_(
            LancamentoManualFinanceiro.categoria == None,
            LancamentoManualFinanceiro.categoria == ""
        ))
    elif categoria:
        q_banco = q_banco.filter(LancamentoBanco.categoria == categoria)
        q_manual_real = q_manual_real.filter(LancamentoManualFinanceiro.categoria == categoria)
        q_receber = q_receber.filter(LancamentoManualFinanceiro.categoria == categoria)
    if busca:
        like = f"%{busca.strip()}%"
        q_banco = q_banco.filter(LancamentoBanco.historico.ilike(like))
        q_manual_real = q_manual_real.filter(LancamentoManualFinanceiro.descricao.ilike(like))
        q_receber = q_receber.filter(LancamentoManualFinanceiro.descricao.ilike(like))

    banco = q_banco.order_by(LancamentoBanco.data.desc(), LancamentoBanco.ordem.asc(), LancamentoBanco.id.asc()).all()
    manuais_reais = q_manual_real.order_by(LancamentoManualFinanceiro.data.desc(),
                                           LancamentoManualFinanceiro.ordem.asc(),
                                           LancamentoManualFinanceiro.id.asc()).all()
    receber = q_receber.order_by(LancamentoManualFinanceiro.data.asc(), LancamentoManualFinanceiro.id.asc()).all()

    q_contratos_receber = db.query(Solicitacao).join(Cliente).filter(
        Solicitacao.empresa_id == empresa.id,
        Solicitacao.cancelado_em == None,
        (func.coalesce(Solicitacao.valor, 0) - func.coalesce(Solicitacao.valor_pago, 0)) > 0.009
    )
    if data_inicial:
        q_contratos_receber = q_contratos_receber.filter(Solicitacao.data_evento >= inicio)
    if data_final:
        q_contratos_receber = q_contratos_receber.filter(Solicitacao.data_evento <= fim)
    if busca:
        like = f"%{busca.strip()}%"
        q_contratos_receber = q_contratos_receber.filter(Cliente.nome.ilike(like))
    contratos_receber = q_contratos_receber.order_by(Solicitacao.data_evento.asc(), Solicitacao.id.asc()).all()
    total_contratos_receber = sum(max((c.valor or 0) - (c.valor_pago or 0), 0) for c in contratos_receber)

    hoje = date.today()
    contratos_vencidos = [c for c in contratos_receber if c.data_evento and c.data_evento < hoje]
    contratos_em_dia = [c for c in contratos_receber if not c.data_evento or c.data_evento >= hoje]
    total_contratos_vencidos = sum(max((c.valor or 0) - (c.valor_pago or 0), 0) for c in contratos_vencidos)
    total_contratos_em_dia = sum(max((c.valor or 0) - (c.valor_pago or 0), 0) for c in contratos_em_dia)

    q_pagamentos_sistema = db.query(Pagamento).join(Solicitacao).join(Cliente).filter(
        Pagamento.empresa_id == empresa.id
    )
    if data_inicial:
        q_pagamentos_sistema = q_pagamentos_sistema.filter(Pagamento.data_pagamento >= inicio)
    if data_final:
        q_pagamentos_sistema = q_pagamentos_sistema.filter(Pagamento.data_pagamento <= fim)
    if busca:
        like = f"%{busca.strip()}%"
        q_pagamentos_sistema = q_pagamentos_sistema.filter(Cliente.nome.ilike(like))

    pagamentos_sistema_mes = q_pagamentos_sistema.order_by(Pagamento.data_pagamento.desc(), Pagamento.id.desc()).all()
    total_contratos_pagos_mes = sum(float(p.valor or 0) for p in pagamentos_sistema_mes)

    if status_sistema == "vinculado":
        q_pagamentos_sistema = q_pagamentos_sistema.filter(Pagamento.conciliado_em != None)
    elif status_sistema != "todos":
        status_sistema = "pendente"
        q_pagamentos_sistema = q_pagamentos_sistema.filter(Pagamento.conciliado_em == None)

    pagamentos_sistema = q_pagamentos_sistema.order_by(Pagamento.data_pagamento.desc(), Pagamento.id.desc()).all()

    pagamentos_pendentes_vinculo = db.query(Pagamento).join(Solicitacao).join(Cliente).filter(
        Pagamento.empresa_id == empresa.id,
        Pagamento.conciliado_em == None
    ).all()

    # Cards superiores: sempre obedecem somente ao pequeno seletor de mês.
    q_banco_cards = db.query(LancamentoBanco).filter(
        LancamentoBanco.empresa_id == empresa.id,
        LancamentoBanco.data >= mes_cards_inicio,
        LancamentoBanco.data <= mes_cards_fim
    )
    q_manual_cards = db.query(LancamentoManualFinanceiro).filter(
        LancamentoManualFinanceiro.empresa_id == empresa.id,
        LancamentoManualFinanceiro.data >= mes_cards_inicio,
        LancamentoManualFinanceiro.data <= mes_cards_fim
    )
    if conta:
        q_banco_cards = q_banco_cards.filter(LancamentoBanco.conta_id == conta.id)
        q_manual_cards = q_manual_cards.filter(LancamentoManualFinanceiro.conta_id == conta.id)

    banco_cards = q_banco_cards.all()
    manuais_cards = q_manual_cards.all()
    entradas = sum(float(l.valor or 0) for l in banco_cards if (l.valor or 0) > 0) + sum(
        float(l.valor or 0) for l in manuais_cards if l.tipo == "real" and (l.valor or 0) > 0)
    saidas = sum(abs(float(l.valor or 0)) for l in banco_cards if (l.valor or 0) < 0) + sum(
        abs(float(l.valor or 0)) for l in manuais_cards if l.tipo == "real" and (l.valor or 0) < 0)
    saldo_real = entradas - saidas
    total_receber = sum(
        max(float(l.valor or 0), 0) for l in manuais_cards if l.tipo == "receber" and not l.recebido)

    contratos_cards = db.query(Solicitacao).filter(
        Solicitacao.empresa_id == empresa.id,
        Solicitacao.cancelado_em == None,
        Solicitacao.data_evento >= mes_cards_inicio,
        Solicitacao.data_evento <= mes_cards_fim
    ).all()
    quantidade_contratos_cards = len(contratos_cards)
    total_contratos_receber_cards = sum(
        max(float(c.valor or 0) - float(c.valor_pago or 0), 0) for c in contratos_cards)

    # Acumulado do banco: independente do mês escolhido nos cards.
    # Considera todas as movimentações reais do ano corrente até hoje.
    inicio_ano = hoje.replace(month=1, day=1)

    def saldo_real_conta(conta_calculo):
        """
        Calcula quanto existe na conta neste momento.

        Regra:
        entradas - saídas do ano corrente até hoje.

        O seletor de mês afeta apenas os cards e o relatório mensal. Lançamentos
        futuros não entram no saldo atual.
        """
        # O acumulado anual representa somente as movimentações reais do ano.
        # O saldo inicial cadastrado na conta não entra neste cartão.
        total_importado = db.query(
            func.coalesce(func.sum(LancamentoBanco.valor), 0)
        ).filter(
            LancamentoBanco.empresa_id == empresa.id,
            LancamentoBanco.conta_id == conta_calculo.id,
            LancamentoBanco.data >= inicio_ano,
            LancamentoBanco.data <= hoje
        ).scalar() or 0

        total_manual = db.query(
            func.coalesce(func.sum(LancamentoManualFinanceiro.valor), 0)
        ).filter(
            LancamentoManualFinanceiro.empresa_id == empresa.id,
            LancamentoManualFinanceiro.conta_id == conta_calculo.id,
            LancamentoManualFinanceiro.tipo == "real",
            LancamentoManualFinanceiro.data >= inicio_ano,
            LancamentoManualFinanceiro.data <= hoje
        ).scalar() or 0

        return float(total_importado) + float(total_manual)

    saldo_banco = saldo_real_conta(conta) if conta else 0.0
    saldo_todos = sum(saldo_real_conta(c) for c in contas if c.ativa)

    # Relatório mensal por semana, sempre limitado ao mês selecionado.
    relatorio_semanal = []
    for indice, periodo in enumerate(semanas_cards, start=1):
        contratos_periodo = db.query(Solicitacao).filter(
            Solicitacao.empresa_id == empresa.id,
            Solicitacao.cancelado_em == None,
            Solicitacao.data_evento >= periodo["inicio"],
            Solicitacao.data_evento <= periodo["fim"]
        ).all()
        valor_total_periodo = sum(float(c.valor or 0) for c in contratos_periodo)
        valor_recebido_periodo = sum(min(float(c.valor_pago or 0), float(c.valor or 0)) for c in contratos_periodo)
        valor_receber_periodo = sum(
            max(float(c.valor or 0) - float(c.valor_pago or 0), 0) for c in contratos_periodo
        )
        relatorio_semanal.append({
            "numero": indice,
            "inicio": periodo["inicio"],
            "fim": periodo["fim"],
            "quantidade": len(contratos_periodo),
            "valor_total": valor_total_periodo,
            "valor_recebido": valor_recebido_periodo,
            "valor_receber": valor_receber_periodo,
        })

    relatorio_total = {
        "quantidade": sum(item["quantidade"] for item in relatorio_semanal),
        "valor_total": sum(item["valor_total"] for item in relatorio_semanal),
        "valor_recebido": sum(item["valor_recebido"] for item in relatorio_semanal),
        "valor_receber": sum(item["valor_receber"] for item in relatorio_semanal),
    }

    saldo_previsto = saldo_real + total_receber + total_contratos_receber_cards

    # Cards inferiores: semana escolhida, sempre de segunda-feira a domingo.
    contratos_semana = db.query(Solicitacao).filter(
        Solicitacao.empresa_id == empresa.id,
        Solicitacao.cancelado_em == None,
        Solicitacao.data_evento >= semana_cards_inicio,
        Solicitacao.data_evento <= semana_cards_fim
    ).all()
    quantidade_contratos_semana = len(contratos_semana)
    valor_total_contratos_semana = sum(float(c.valor or 0) for c in contratos_semana)
    valor_receber_contratos_semana = sum(
        max(float(c.valor or 0) - float(c.valor_pago or 0), 0) for c in contratos_semana)

    candidatos_vinculo = {
        l.id: melhores_vinculos_para_banco(l, pagamentos_pendentes_vinculo)
        for l in banco
        if not l.pagamento_id and l.categoria == "aluguel"
    }
    candidatos_manual = {
        m.id: melhores_vinculos_para_manual(m, pagamentos_pendentes_vinculo)
        for m in manuais_reais
        if not getattr(m, "pagamento_id", None) and m.categoria == "aluguel" and (m.valor or 0) > 0
    }

    return templates.TemplateResponse("admin/financeiro.html", {
        "request": request, "empresa": empresa, "contas": contas, "conta": conta,
        "data_inicial": data_inicial, "data_final": data_final, "categoria": categoria, "busca": busca,
        "status_sistema": status_sistema,
        "mes_cards": mes_cards_inicio.strftime("%Y-%m"), "meses_cards": meses_cards,
        "mes_cards_inicio": mes_cards_inicio, "mes_cards_fim": mes_cards_fim,
        "semana_cards": semana_cards_inicio.isoformat(), "semanas_cards": semanas_cards,
        "semana_cards_inicio": semana_cards_inicio, "semana_cards_fim": semana_cards_fim,
        "timedelta": timedelta,
        "banco": banco, "manuais_reais": manuais_reais, "receber": receber, "pagamentos_sistema": pagamentos_sistema,
        "contratos_receber": contratos_receber, "total_contratos_receber": total_contratos_receber,
        "quantidade_contratos_cards": quantidade_contratos_cards,
        "total_contratos_receber_cards": total_contratos_receber_cards,
        "quantidade_contratos_semana": quantidade_contratos_semana,
        "valor_total_contratos_semana": valor_total_contratos_semana,
        "valor_receber_contratos_semana": valor_receber_contratos_semana,
        "contratos_vencidos": contratos_vencidos, "contratos_em_dia": contratos_em_dia,
        "total_contratos_vencidos": total_contratos_vencidos, "total_contratos_em_dia": total_contratos_em_dia,
        "pagamentos_sistema_mes": pagamentos_sistema_mes, "total_contratos_pagos_mes": total_contratos_pagos_mes,
        "entradas": entradas, "saidas": saidas, "saldo_real": saldo_real, "total_receber": total_receber,
        "saldo_previsto": saldo_previsto, "saldo_banco": saldo_banco, "saldo_todos": saldo_todos,
        "relatorio_semanal": relatorio_semanal, "relatorio_total": relatorio_total,
        "candidatos_vinculo": candidatos_vinculo,
        "candidatos_manual": candidatos_manual,
        "categorias": [("casa", "Casa"), ("empresa", "Empresa"), ("aluguel", "Aluguel"), ("manutencao", "Manutenção")]
    })



def _relatorio_financeiro_mensal(db: Session, empresa_id: int, mes_ref: str):
    try:
        inicio_mes = datetime.strptime(mes_ref, "%Y-%m").date().replace(day=1)
    except ValueError:
        raise HTTPException(400, "Mês inválido.")
    indice = inicio_mes.year * 12 + inicio_mes.month
    fim_mes = date(indice // 12, indice % 12 + 1, 1) - timedelta(days=1)

    semanas = []
    cursor = inicio_mes
    numero = 1
    while cursor <= fim_mes:
        fim_semana = min(cursor + timedelta(days=6 - cursor.weekday()), fim_mes)
        contratos = db.query(Solicitacao).filter(
            Solicitacao.empresa_id == empresa_id,
            Solicitacao.cancelado_em == None,
            Solicitacao.data_evento >= cursor,
            Solicitacao.data_evento <= fim_semana
        ).all()
        valor_total = sum(float(c.valor or 0) for c in contratos)
        recebido = sum(min(float(c.valor_pago or 0), float(c.valor or 0)) for c in contratos)
        receber = sum(max(float(c.valor or 0) - float(c.valor_pago or 0), 0) for c in contratos)
        semanas.append({
            "numero": numero,
            "inicio": cursor,
            "fim": fim_semana,
            "quantidade": len(contratos),
            "valor_total": valor_total,
            "valor_recebido": recebido,
            "valor_receber": receber,
        })
        cursor = fim_semana + timedelta(days=1)
        numero += 1

    total = {
        "quantidade": sum(s["quantidade"] for s in semanas),
        "valor_total": sum(s["valor_total"] for s in semanas),
        "valor_recebido": sum(s["valor_recebido"] for s in semanas),
        "valor_receber": sum(s["valor_receber"] for s in semanas),
    }
    return inicio_mes, fim_mes, semanas, total


def _xlsx_relatorio_financeiro(inicio_mes, semanas, total):
    # Gera um XLSX simples e válido sem dependência adicional.
    linhas = [
        ["Relatório financeiro mensal", "", "", "", "", ""],
        [inicio_mes.strftime("%m/%Y"), "", "", "", "", ""],
        ["Semana", "Período", "Qtd. contratos", "Valor total", "Recebido", "A receber"],
    ]
    for item in semanas:
        linhas.append([
            f"Semana {item['numero']}",
            f"{item['inicio'].strftime('%d/%m/%Y')} a {item['fim'].strftime('%d/%m/%Y')}",
            item["quantidade"],
            item["valor_total"],
            item["valor_recebido"],
            item["valor_receber"],
        ])
    linhas.append([
        "TOTAL DO MÊS", "",
        total["quantidade"], total["valor_total"],
        total["valor_recebido"], total["valor_receber"],
    ])

    def coluna_excel(numero):
        resultado = ""
        while numero:
            numero, resto = divmod(numero - 1, 26)
            resultado = chr(65 + resto) + resultado
        return resultado

    cells = []
    for r, linha in enumerate(linhas, start=1):
        for c, valor in enumerate(linha, start=1):
            ref = f"{coluna_excel(c)}{r}"
            if isinstance(valor, (int, float)):
                estilo = ' s="2"' if c >= 4 else ' s="1"'
                cells.append(f'<c r="{ref}"{estilo}><v>{valor}</v></c>')
            else:
                estilo = ' s="3"' if r == 1 else (' s="4"' if r in (3, len(linhas)) else '')
                cells.append(f'<c r="{ref}" t="inlineStr"{estilo}><is><t>{xml_escape(str(valor))}</t></is></c>')

    rows_xml = []
    idx = 0
    for r, linha in enumerate(linhas, start=1):
        quantidade = len(linha)
        rows_xml.append(f'<row r="{r}">' + "".join(cells[idx:idx+quantidade]) + '</row>')
        idx += quantidade

    sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<cols><col min="1" max="1" width="18" customWidth="1"/><col min="2" max="2" width="28" customWidth="1"/>
<col min="3" max="3" width="16" customWidth="1"/><col min="4" max="6" width="17" customWidth="1"/></cols>
<sheetData>{''.join(rows_xml)}</sheetData>
<mergeCells count="2"><mergeCell ref="A1:F1"/><mergeCell ref="A2:F2"/></mergeCells>
</worksheet>'''
    styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="1"><numFmt numFmtId="164" formatCode="R$ #,##0.00"/></numFmts>
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="12"/><name val="Calibri"/></font></fonts>
<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellXfs count="5">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/>
</cellXfs></styleSheet>'''
    arquivos = {
        "[Content_Types].xml": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>''',
        "_rels/.rels": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>''',
        "xl/workbook.xml": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Relatório mensal" sheetId="1" r:id="rId1"/></sheets></workbook>''',
        "xl/_rels/workbook.xml.rels": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>''',
        "xl/worksheets/sheet1.xml": sheet_xml,
        "xl/styles.xml": styles_xml,
    }
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as pacote:
        for nome, conteudo in arquivos.items():
            pacote.writestr(nome, conteudo)
    return buffer.getvalue()


@app.get("/painel/financeiro/relatorio-mensal.xlsx")
def financeiro_relatorio_excel(
        request: Request,
        mes: str,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    if not usuario_pode_financeiro(request, empresa, db):
        raise HTTPException(403, "Usuário sem permissão para visualizar o financeiro.")
    inicio_mes, _, semanas, total = _relatorio_financeiro_mensal(db, empresa.id, mes)
    conteudo = _xlsx_relatorio_financeiro(inicio_mes, semanas, total)
    nome = f"relatorio-financeiro-{inicio_mes.strftime('%Y-%m')}.xlsx"
    return Response(
        conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'}
    )


@app.get("/painel/financeiro/relatorio-mensal.pdf")
def financeiro_relatorio_pdf(
        request: Request,
        mes: str,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    if not usuario_pode_financeiro(request, empresa, db):
        raise HTTPException(403, "Usuário sem permissão para visualizar o financeiro.")
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    except Exception:
        raise HTTPException(500, "Para gerar PDF, instale a dependência reportlab.")

    inicio_mes, _, semanas, total = _relatorio_financeiro_mensal(db, empresa.id, mes)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph(f"Relatório financeiro mensal - {inicio_mes.strftime('%m/%Y')}", estilos["Title"]),
        Spacer(1, 14),
    ]
    dados = [["Semana", "Período", "Qtd. contratos", "Valor total", "Recebido", "A receber"]]
    moeda = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    for item in semanas:
        dados.append([
            f"Semana {item['numero']}",
            f"{item['inicio'].strftime('%d/%m/%Y')} a {item['fim'].strftime('%d/%m/%Y')}",
            str(item["quantidade"]),
            moeda(item["valor_total"]),
            moeda(item["valor_recebido"]),
            moeda(item["valor_receber"]),
        ])
    dados.append([
        "TOTAL DO MÊS", "", str(total["quantidade"]),
        moeda(total["valor_total"]), moeda(total["valor_recebido"]), moeda(total["valor_receber"])
    ])
    tabela = Table(dados, colWidths=[80, 155, 90, 105, 105, 105], repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF2FF")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F8FAFC")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F8FAFC")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    elementos.append(tabela)
    doc.build(elementos)
    nome = f"relatorio-financeiro-{inicio_mes.strftime('%Y-%m')}.pdf"
    return Response(
        buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'}
    )


@app.post("/painel/financeiro/conta")
def financeiro_salvar_conta(
        request: Request,
        conta_id: int = Form(0),
        saldo_inicial: str = Form("0"),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    conta = db.get(ContaFinanceira, conta_id)
    if not conta or conta.empresa_id != empresa.id:
        raise HTTPException(404)
    conta.saldo_inicial = texto_para_float(saldo_inicial)
    db.commit()
    return redirect_preservando_filtros(request, f"/painel/financeiro?conta_id={conta.id}")


@app.post("/painel/financeiro/importar")
def financeiro_importar_extrato(
        request: Request,
        conta_id: int = Form(...),
        arquivo: UploadFile = File(...),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    conta = db.get(ContaFinanceira, conta_id)
    if not conta or conta.empresa_id != empresa.id:
        raise HTTPException(404)
    registros = ler_extrato_upload(arquivo)
    importados = 0
    duplicados = 0
    conciliados = 0
    hashes_do_arquivo = set()
    proxima_ordem = int(db.query(func.coalesce(func.max(LancamentoBanco.ordem), 0)).filter_by(empresa_id=empresa.id,
                                                                                              conta_id=conta.id).scalar() or 0) + 1
    for idx_registro, r in enumerate(registros):
        h = hash_lancamento_banco(empresa.id, conta.id, r["data"], r["historico"], r["documento"], r["valor"],
                                  r["saldo"])
        if h in hashes_do_arquivo:
            duplicados += 1
            continue
        hashes_do_arquivo.add(h)
        existe = db.query(LancamentoBanco).filter(
            LancamentoBanco.empresa_id == empresa.id,
            LancamentoBanco.conta_id == conta.id,
            (LancamentoBanco.hash_importacao == h) | (
                    (LancamentoBanco.data == r["data"]) &
                    (LancamentoBanco.historico == r["historico"]) &
                    (LancamentoBanco.documento == r["documento"]) &
                    (LancamentoBanco.valor == r["valor"]) &
                    (LancamentoBanco.saldo == r["saldo"])
            )
        ).first()
        if existe:
            if existe.pagamento_id:
                conciliados += 1
            else:
                duplicados += 1
            if not getattr(existe, "hash_importacao", None):
                existe.hash_importacao = h
            continue
        db.add(LancamentoBanco(
            empresa_id=empresa.id,
            conta_id=conta.id,
            data=r["data"],
            historico=r["historico"],
            documento=r["documento"],
            valor=r["valor"],
            saldo=r["saldo"],
            categoria=categoria_sugerida(r["historico"], r["valor"]),
            categoria_confirmada=False,
            hash_importacao=h,
            origem_importacao=arquivo.filename,
            ordem=proxima_ordem + idx_registro
        ))
        importados += 1
    db.commit()
    return redirect_preservando_filtros(request, f"/painel/financeiro?conta_id={conta.id}",
                                        {"importados": importados, "duplicados": duplicados,
                                         "conciliados": conciliados})


@app.post("/painel/financeiro/banco/{lancamento_id}/categoria")
def financeiro_categoria_banco(
        request: Request,
        lancamento_id: int,
        categoria: str = Form(...),
        confirmado: str = Form("0"),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    lanc = db.get(LancamentoBanco, lancamento_id)
    if not lanc or lanc.empresa_id != empresa.id:
        raise HTTPException(404)
    if categoria not in ["casa", "empresa", "aluguel", "manutencao"]:
        raise HTTPException(400, "Categoria inválida.")
    lanc.categoria = categoria
    lanc.categoria_confirmada = confirmado == "1"
    db.commit()
    return RedirectResponse(request.headers.get("referer") or "/painel/financeiro", status_code=303)


@app.post("/painel/financeiro/banco/{lancamento_id}/vincular")
def financeiro_vincular_banco(
        request: Request,
        lancamento_id: int,
        pagamento_id: int = Form(...),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    lanc = db.get(LancamentoBanco, lancamento_id)
    pagamento = db.get(Pagamento, pagamento_id)
    if not lanc or lanc.empresa_id != empresa.id or not pagamento or pagamento.empresa_id != empresa.id:
        raise HTTPException(404)
    lanc.pagamento_id = pagamento.id
    lanc.categoria = "aluguel"
    pagamento.conciliado_em = agora_utc()
    pagamento.conciliado_por = request.session.get("usuario_nome") or "Financeiro"
    db.commit()
    return RedirectResponse(request.headers.get("referer") or "/painel/financeiro", status_code=303)


@app.post("/painel/financeiro/banco/{lancamento_id}/desvincular")
def financeiro_desvincular_banco(
        request: Request,
        lancamento_id: int,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    lanc = db.get(LancamentoBanco, lancamento_id)
    if not lanc or lanc.empresa_id != empresa.id:
        raise HTTPException(404)
    if lanc.pagamento:
        lanc.pagamento.conciliado_em = None
        lanc.pagamento.conciliado_por = None
    lanc.pagamento_id = None
    db.commit()
    return RedirectResponse(request.headers.get("referer") or "/painel/financeiro", status_code=303)


@app.post("/painel/financeiro/banco/{lancamento_id}/excluir")
def financeiro_excluir_banco(
        request: Request,
        lancamento_id: int,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    lanc = db.get(LancamentoBanco, lancamento_id)
    if not lanc or lanc.empresa_id != empresa.id:
        raise HTTPException(404)
    if lanc.pagamento:
        lanc.pagamento.conciliado_em = None
        lanc.pagamento.conciliado_por = None
    db.delete(lanc)
    db.commit()
    return RedirectResponse(request.headers.get("referer") or "/painel/financeiro", status_code=303)


@app.post("/painel/financeiro/banco/{lancamento_id}/mover")
def financeiro_mover_banco(
        request: Request,
        lancamento_id: int,
        direcao: str = Form(...),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    lanc = db.get(LancamentoBanco, lancamento_id)
    if not lanc or lanc.empresa_id != empresa.id:
        raise HTTPException(404)
    mover_lancamento_na_lista(db, LancamentoBanco, lanc, direcao)
    return RedirectResponse(request.headers.get("referer") or "/painel/financeiro", status_code=303)


@app.post("/painel/financeiro/sistema/{pagamento_id}/lancar")
def financeiro_lancar_pagamento_sistema(
        request: Request,
        pagamento_id: int,
        conta_id: int = Form(...),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    conta = db.get(ContaFinanceira, conta_id)
    pagamento = db.get(Pagamento, pagamento_id)
    if not conta or conta.empresa_id != empresa.id or not pagamento or pagamento.empresa_id != empresa.id:
        raise HTTPException(404)

    existente_banco = db.query(LancamentoBanco).filter_by(empresa_id=empresa.id, pagamento_id=pagamento.id).first()
    existente_manual = db.query(LancamentoManualFinanceiro).filter_by(empresa_id=empresa.id, pagamento_id=pagamento.id, tipo="real").first()
    if not existente_banco and not existente_manual:
        proxima_ordem = int(db.query(func.coalesce(func.max(LancamentoManualFinanceiro.ordem), 0)).filter_by(
            empresa_id=empresa.id, conta_id=conta.id).scalar() or 0) + 1
        cliente_nome = pagamento.solicitacao.cliente.nome if pagamento.solicitacao and pagamento.solicitacao.cliente else "Cliente"
        forma = (pagamento.forma_pagamento or "pagamento").strip()
        db.add(LancamentoManualFinanceiro(
            empresa_id=empresa.id,
            conta_id=conta.id,
            data=pagamento.data_pagamento,
            descricao=f"{cliente_nome} - {forma}",
            valor=pagamento.valor or 0,
            categoria="aluguel",
            tipo="real",
            recebido=False,
            pagamento_id=pagamento.id,
            ordem=proxima_ordem
        ))
    pagamento.conciliado_em = agora_utc()
    pagamento.conciliado_por = request.session.get("usuario_nome") or "Financeiro"
    db.commit()
    return RedirectResponse(request.headers.get("referer") or f"/painel/financeiro?conta_id={conta.id}", status_code=303)


@app.post("/painel/financeiro/manual")
def financeiro_lancamento_manual(
        request: Request,
        conta_id: int = Form(...),
        data: str = Form(...),
        descricao: str = Form(...),
        valor: str = Form("0"),
        categoria: str = Form("empresa"),
        tipo: str = Form("real"),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    conta = db.get(ContaFinanceira, conta_id)
    if not conta or conta.empresa_id != empresa.id:
        raise HTTPException(404)
    if categoria not in ["casa", "empresa", "aluguel", "manutencao"]:
        raise HTTPException(400, "Categoria inválida.")
    if tipo not in ["real", "receber"]:
        raise HTTPException(400, "Tipo inválido.")
    valor_float = texto_para_float(valor)
    proxima_ordem = int(
        db.query(func.coalesce(func.max(LancamentoManualFinanceiro.ordem), 0)).filter_by(empresa_id=empresa.id,
                                                                                         conta_id=conta.id).scalar() or 0) + 1
    if tipo == "receber" and valor_float < 0:
        valor_float = abs(valor_float)
    db.add(LancamentoManualFinanceiro(
        empresa_id=empresa.id,
        conta_id=conta.id,
        data=datetime.strptime(data, "%Y-%m-%d").date(),
        descricao=descricao.strip(),
        valor=valor_float,
        categoria=categoria,
        tipo=tipo,
        recebido=False,
        ordem=proxima_ordem
    ))
    db.commit()
    return redirect_preservando_filtros(request, f"/painel/financeiro?conta_id={conta.id}")


@app.post("/painel/financeiro/manual/{lancamento_id}/mover")
def financeiro_mover_manual(
        request: Request,
        lancamento_id: int,
        direcao: str = Form(...),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    lanc = db.get(LancamentoManualFinanceiro, lancamento_id)
    if not lanc or lanc.empresa_id != empresa.id or lanc.tipo != "real":
        raise HTTPException(404)
    mover_lancamento_na_lista(db, LancamentoManualFinanceiro, lanc, direcao)
    return RedirectResponse(request.headers.get("referer") or f"/painel/financeiro?conta_id={lanc.conta_id}",
                            status_code=303)


@app.post("/painel/financeiro/manual/{lancamento_id}/editar")
def financeiro_editar_manual(
        request: Request,
        lancamento_id: int,
        data: str = Form(...),
        descricao: str = Form(...),
        valor: str = Form("0"),
        categoria: str = Form("empresa"),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    lanc = db.get(LancamentoManualFinanceiro, lancamento_id)
    if not lanc or lanc.empresa_id != empresa.id:
        raise HTTPException(404)
    if categoria not in ["casa", "empresa", "aluguel", "manutencao"]:
        raise HTTPException(400, "Categoria inválida.")
    lanc.data = datetime.strptime(data, "%Y-%m-%d").date()
    lanc.descricao = descricao.strip()
    lanc.valor = texto_para_float(valor)
    lanc.categoria = categoria
    if categoria != "aluguel" and getattr(lanc, "pagamento_id", None):
        pagamento = db.get(Pagamento, lanc.pagamento_id)
        if pagamento:
            pagamento.conciliado_em = None
        lanc.pagamento_id = None
    db.commit()
    return redirect_preservando_filtros(request, f"/painel/financeiro?conta_id={lanc.conta_id}")


@app.post("/painel/financeiro/manual/{lancamento_id}/vincular")
def financeiro_vincular_manual(
        request: Request,
        lancamento_id: int,
        pagamento_id: int = Form(...),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    lanc = db.get(LancamentoManualFinanceiro, lancamento_id)
    pagamento = db.get(Pagamento, pagamento_id)
    if not lanc or lanc.empresa_id != empresa.id or lanc.tipo != "real" or not pagamento or pagamento.empresa_id != empresa.id:
        raise HTTPException(404)
    lanc.pagamento_id = pagamento.id
    lanc.categoria = "aluguel"
    pagamento.conciliado_em = agora_utc()
    pagamento.conciliado_por = request.session.get("usuario_nome") or "Financeiro"
    db.commit()
    return RedirectResponse(request.headers.get("referer") or f"/painel/financeiro?conta_id={lanc.conta_id}",
                            status_code=303)


@app.post("/painel/financeiro/manual/{lancamento_id}/desvincular")
def financeiro_desvincular_manual(
        request: Request,
        lancamento_id: int,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    lanc = db.get(LancamentoManualFinanceiro, lancamento_id)
    if not lanc or lanc.empresa_id != empresa.id or lanc.tipo != "real":
        raise HTTPException(404)
    if lanc.pagamento:
        lanc.pagamento.conciliado_em = None
        lanc.pagamento.conciliado_por = None
    lanc.pagamento_id = None
    db.commit()
    return RedirectResponse(request.headers.get("referer") or f"/painel/financeiro?conta_id={lanc.conta_id}",
                            status_code=303)


@app.post("/painel/financeiro/manual/{lancamento_id}/excluir")
def financeiro_excluir_manual(
        request: Request,
        lancamento_id: int,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    lanc = db.get(LancamentoManualFinanceiro, lancamento_id)
    if not lanc or lanc.empresa_id != empresa.id or lanc.tipo != "real":
        raise HTTPException(404)
    conta_id = lanc.conta_id
    if lanc.pagamento:
        lanc.pagamento.conciliado_em = None
        lanc.pagamento.conciliado_por = None
    db.delete(lanc)
    db.commit()
    return RedirectResponse(request.headers.get("referer") or f"/painel/financeiro?conta_id={conta_id}",
                            status_code=303)


@app.post("/painel/financeiro/receber/{lancamento_id}/receber")
def financeiro_marcar_recebido(
        request: Request,
        lancamento_id: int,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    lanc = db.get(LancamentoManualFinanceiro, lancamento_id)
    if not lanc or lanc.empresa_id != empresa.id or lanc.tipo != "receber":
        raise HTTPException(404)
    lanc.recebido = True
    db.add(LancamentoManualFinanceiro(
        empresa_id=empresa.id,
        conta_id=lanc.conta_id,
        data=date.today(),
        descricao=f"Recebido: {lanc.descricao}",
        valor=abs(lanc.valor or 0),
        categoria=lanc.categoria,
        tipo="real",
        recebido=True
    ))
    db.commit()
    return redirect_preservando_filtros(request, f"/painel/financeiro?conta_id={lanc.conta_id}")


@app.post("/painel/solicitacao/{solicitacao_id}/pagamento")
def confirmar_pagamento(
        request: Request,
        solicitacao_id: int,
        data_pagamento: str = Form(""),
        valor_pago: str = Form("0"),
        forma_pagamento: str = Form("pix"),
        comprovante_no_nome_cliente: str = Form("sim"),
        nome_comprovante: str = Form(""),
        observacoes_pagamento: str = Form(""),
        retorno: str = Form(""),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)
    # Pagamento é opcional e independente do aceite.
    # Pode ser informado antes ou depois do contrato aceito; ele apenas gera o lançamento financeiro.
    valor = texto_para_float(valor_pago)
    if valor <= 0:
        return RedirectResponse(retorno or f"/painel/solicitacao/{solicitacao_id}", status_code=303)
    total_atual = sum((p.valor or 0) for p in getattr(item, "pagamentos", []) or [])
    validar_total_pagamentos(item, total_atual + valor)
    data_ref = datetime.strptime(data_pagamento, "%Y-%m-%d").date() if data_pagamento else date.today()
    no_nome = comprovante_no_nome_cliente == "sim"
    pagamento = Pagamento(
        empresa_id=empresa.id,
        solicitacao_id=item.id,
        data_pagamento=data_ref,
        valor=valor,
        forma_pagamento=forma_pagamento,
        comprovante_no_nome_cliente=no_nome,
        nome_comprovante=item.cliente.nome if no_nome else nome_comprovante.strip(),
        observacoes=observacoes_pagamento.strip(),
        usuario_registro=request.session.get("usuario_sistema", "Usuário")
    )
    db.add(pagamento)
    db.flush()
    recalcular_pagamento_solicitacao(db, item)
    # Não altera aceite do contrato. Pagamento muda apenas o resumo financeiro.
    db.commit()
    return RedirectResponse(retorno or f"/painel/solicitacao/{solicitacao_id}", status_code=303)


@app.post("/painel/solicitacao/{solicitacao_id}/pagamento/{pagamento_id}/excluir")
def excluir_pagamento_solicitacao(
        solicitacao_id: int,
        pagamento_id: int,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Solicitacao, solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)

    pagamento = db.get(Pagamento, pagamento_id)
    if not pagamento or pagamento.empresa_id != empresa.id or pagamento.solicitacao_id != item.id:
        raise HTTPException(404)

    db.delete(pagamento)
    db.flush()
    recalcular_pagamento_solicitacao(db, item)

    # Excluir pagamento não altera aceite nem status do contrato.
    db.commit()
    return RedirectResponse(f"/painel/solicitacao/{solicitacao_id}", status_code=303)


@app.post("/painel/pagamento/{pagamento_id}/editar")
def editar_pagamento_financeiro(
        request: Request,
        pagamento_id: int,
        data_pagamento: str = Form(""),
        valor_pago: str = Form("0"),
        forma_pagamento: str = Form("pix"),
        nome_comprovante: str = Form(""),
        observacoes_pagamento: str = Form(""),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    pagamento = db.get(Pagamento, pagamento_id)
    if not pagamento or pagamento.empresa_id != empresa.id:
        raise HTTPException(404)
    item = db.get(Solicitacao, pagamento.solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)

    valor = texto_para_float(valor_pago)
    if valor <= 0:
        raise HTTPException(400, "O valor do pagamento precisa ser maior que zero.")

    total_sem_este = sum((p.valor or 0) for p in db.query(Pagamento).filter(
        Pagamento.empresa_id == empresa.id,
        Pagamento.solicitacao_id == item.id,
        Pagamento.id != pagamento.id
    ).all())
    validar_total_pagamentos(item, total_sem_este + valor)

    pagamento.data_pagamento = datetime.strptime(data_pagamento, "%Y-%m-%d").date() if data_pagamento else date.today()
    pagamento.valor = valor
    pagamento.forma_pagamento = forma_pagamento
    pagamento.nome_comprovante = nome_comprovante.strip() or (item.cliente.nome if item.cliente else "")
    pagamento.observacoes = observacoes_pagamento.strip()
    recalcular_pagamento_solicitacao(db, item)
    db.commit()
    voltar = request.headers.get("referer") or "/painel/financeiro"
    return RedirectResponse(voltar, status_code=303)


@app.post("/painel/pagamento/{pagamento_id}/excluir")
def excluir_pagamento_financeiro(
        request: Request,
        pagamento_id: int,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    pagamento = db.get(Pagamento, pagamento_id)
    if not pagamento or pagamento.empresa_id != empresa.id:
        raise HTTPException(404)
    item = db.get(Solicitacao, pagamento.solicitacao_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)
    db.delete(pagamento)
    db.flush()
    recalcular_pagamento_solicitacao(db, item)
    db.commit()
    voltar = request.headers.get("referer") or "/painel/financeiro"
    return RedirectResponse(voltar, status_code=303)


@app.post("/painel/pagamento/{pagamento_id}/conciliar")
def conciliar_pagamento_financeiro(
        request: Request,
        pagamento_id: int,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    pagamento = db.get(Pagamento, pagamento_id)
    if not pagamento or pagamento.empresa_id != empresa.id:
        raise HTTPException(404)
    if not pagamento.conciliado_em:
        pagamento.conciliado_em = agora_utc()
        pagamento.conciliado_por = request.session.get("usuario_sistema") or request.session.get(
            "usuario_nome") or "Usuário"
        db.commit()
    voltar = request.headers.get("referer") or "/painel/financeiro"
    return RedirectResponse(voltar, status_code=303)


@app.get("/painel/disponibilidade", response_class=HTMLResponse)
def disponibilidade(request: Request, data: str = "", produto_id: int = 0, db: Session = Depends(get_db),
                    empresa: Empresa = Depends(empresa_logada)):
    data_consulta = datetime.strptime(data, "%Y-%m-%d").date() if data else date.today()

    produtos = db.query(ProdutoServico).filter_by(empresa_id=empresa.id, ativo=True).order_by(ProdutoServico.nome).all()

    # Reservas consideradas: locações ativas na data escolhida.
    status_ignorados = ["cancelada", "rejeitada"]
    reservas_do_dia = (
        db.query(Solicitacao)
        .filter(Solicitacao.empresa_id == empresa.id)
        .filter(Solicitacao.data_evento == data_consulta)
        .filter(~Solicitacao.status.in_(status_ignorados))
        .all()
    )

    alugado_por_produto = {}
    locais_por_produto = {}
    for reserva in reservas_do_dia:
        for item in reserva.itens:
            chave = item.produto_id
            if not chave:
                continue
            alugado_por_produto[chave] = alugado_por_produto.get(chave, 0) + (item.quantidade or 1)
            locais_por_produto.setdefault(chave, []).append({
                "cliente": reserva.cliente.nome if reserva.cliente else "Cliente",
                "hora": reserva.hora_inicio.strftime("%H:%M") if reserva.hora_inicio else "-",
                "hora_ordenacao": reserva.hora_inicio or time.min,
                "bairro": reserva.bairro or (reserva.cliente.bairro if reserva.cliente else "") or "-",
                "quantidade": item.quantidade or 1,
                "reserva_id": reserva.id,
                "observacoes": ((reserva.observacoes or "") or (reserva.cliente.observacoes if reserva.cliente else "") or "").strip(),
                "retirada_obrigatoria": retirada_obrigatoria_ativa(reserva),
                "retirada_data": reserva.retirada_data,
                "retirada_hora": reserva.retirada_hora,
            })

    itens = []
    produto_selecionado = None
    for produto in produtos:
        total = produto.quantidade_disponivel or 0
        alugados = alugado_por_produto.get(produto.id, 0)
        disponiveis = max(total - alugados, 0)
        conflito = alugados > total
        status = "conflito" if conflito else ("disponivel" if disponiveis > 1 else ("atencao" if disponiveis == 1 else "indisponivel"))
        locais_ordenados = sorted(
            locais_por_produto.get(produto.id, []),
            key=lambda loc: (loc.get("hora_ordenacao") or time.min, loc.get("reserva_id") or 0)
        )
        dados = {
            "produto": produto,
            "total": total,
            "alugados": alugados,
            "disponiveis": disponiveis,
            "status": status,
            "conflito": conflito,
            "locais": locais_ordenados,
        }
        itens.append(dados)
        if produto.id == produto_id:
            produto_selecionado = dados

    return templates.TemplateResponse(
        "admin/disponibilidade.html",
        {
            "request": request,
            "empresa": empresa,
            "data_consulta": data_consulta,
            "itens": itens,
            "produto_selecionado": produto_selecionado,
        },
    )


@app.get("/painel/agenda", response_class=HTMLResponse)
def agenda(
        request: Request,
        data_inicial: str = "",
        data_final: str = "",
        ativos: str = "1",
        credito: str = "",
        cancelados: str = "",
        equipe: str = "",
        situacao_rota: str = "todos",
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    garantir_agenda_reservas(db, empresa.id)
    equipes_permitidas = equipes_permitidas_usuario(request, db)
    equipe_salva = request.session.get("agenda_equipe")
    equipe_num = int(equipe) if equipe in {"1", "2"} else (equipe_salva if equipe_salva in equipes_permitidas else equipes_permitidas[0])
    if equipe_num not in equipes_permitidas:
        equipe_num = equipes_permitidas[0]
    request.session["agenda_equipe"] = equipe_num
    inicio, fim = periodo_semana_atual()

    # Mantém o último filtro usado na agenda para a equipe não precisar refazer a busca.
    filtro_salvo = request.session.get("agenda_filtro", {}) if not request.query_params else {}
    data_inicial = data_inicial or filtro_salvo.get("data_inicial") or inicio.isoformat()
    data_final = data_final or filtro_salvo.get("data_final") or fim.isoformat()
    if not request.query_params and filtro_salvo:
        ativos = filtro_salvo.get("ativos", "1")
        credito = filtro_salvo.get("credito", "")
        cancelados = filtro_salvo.get("cancelados", "")

    request.session["agenda_filtro"] = {
        "data_inicial": data_inicial,
        "data_final": data_final,
        "ativos": "1" if ativos else "",
        "credito": "1" if credito else "",
        "cancelados": "1" if cancelados else "",
        "equipe": equipe_num,
        "situacao_rota": situacao_rota,
    }

    status_credito = {"aguardando_nova_data"}
    status_cancelados = {"cancelada", "cancelado_cliente", "rejeitada"}
    status_inativos = status_credito | status_cancelados

    filtros_status = []
    if ativos:
        filtros_status.append("ativos")
    if credito:
        filtros_status.append("credito")
    if cancelados:
        filtros_status.append("cancelados")

    q = db.query(Solicitacao).filter_by(empresa_id=empresa.id)
    agenda_ids = db.query(Agenda.solicitacao_id).filter(Agenda.empresa_id == empresa.id)
    if situacao_rota == "roteirizado":
        agenda_ids = agenda_ids.filter(Agenda.previsao_entrega.isnot(None), Agenda.previsao_entrega != "", Agenda.ordem_rota == equipe_num)
        q = q.filter(Solicitacao.id.in_(agenda_ids))
    elif situacao_rota == "nao_roteirizado":
        roteirizados_ids = db.query(Agenda.solicitacao_id).filter(Agenda.empresa_id == empresa.id, Agenda.previsao_entrega.isnot(None), Agenda.previsao_entrega != "", Agenda.ordem_rota.in_([1, 2]))
        q = q.filter(~Solicitacao.id.in_(roteirizados_ids))
    else:
        situacao_rota = "todos"

    if data_inicial:
        q = q.filter(Solicitacao.data_evento >= datetime.strptime(data_inicial, "%Y-%m-%d").date())
    if data_final:
        q = q.filter(Solicitacao.data_evento <= datetime.strptime(data_final, "%Y-%m-%d").date())

    # Agenda deve mostrar todas as locações do período.
    # O filtro de rascunho/contrato sem aceite fica somente na tela inicial (/painel).
    solicitacoes = (
        q.order_by(
            Solicitacao.data_evento.asc(),
            Solicitacao.hora_inicio.asc(),
            Solicitacao.id.asc(),
        )
        .all()
    )

    itens = []
    for s in solicitacoes:
        status_atual = s.status or ""
        eh_credito = status_atual in status_credito
        eh_cancelado = status_atual in status_cancelados
        eh_ativo = status_atual not in status_inativos

        if (eh_ativo and "ativos" in filtros_status) or (eh_credito and "credito" in filtros_status) or (
                eh_cancelado and "cancelados" in filtros_status):
            itens.append(s)

    mensagens = mensagens_empresa(empresa)
    return templates.TemplateResponse("admin/agenda.html", {
        "request": request,
        "itens": itens,
        "total_itens": len(itens),
        "empresa": empresa,
        "data_inicial": data_inicial,
        "data_final": data_final,
        "filtro_ativos": bool(ativos),
        "filtro_credito": bool(credito),
        "filtro_cancelados": bool(cancelados),
        "equipe_selecionada": equipe_num,
        "equipes_permitidas": equipes_permitidas,
        "situacao_rota": situacao_rota,
        "mensagens": mensagens,
    })


@app.post("/painel/solicitacao/{solicitacao_id}/responsavel-retirada")
def salvar_responsavel_retirada(solicitacao_id: int, request: Request, retirada_responsavel_nome: str = Form(""), retirada_responsavel_telefone: str = Form(""), db: Session = Depends(get_db), empresa: Empresa = Depends(empresa_logada)):
    item = db.query(Solicitacao).filter_by(id=solicitacao_id, empresa_id=empresa.id).first()
    if not item:
        raise HTTPException(404)
    if retirada_responsavel_telefone and not celular_brasileiro_valido(retirada_responsavel_telefone):
        raise HTTPException(400, "Informe um WhatsApp brasileiro válido para o responsável pela retirada.")
    item.retirada_responsavel_nome = retirada_responsavel_nome.strip()
    item.retirada_responsavel_telefone = limpar_identificador(retirada_responsavel_telefone) or retirada_responsavel_telefone.strip()
    db.commit()
    return RedirectResponse(request.headers.get("referer") or "/painel/preparar", status_code=303)

@app.post("/painel/agenda/{agenda_id}/roteiro")
def atualizar_roteiro(
        request: Request,
        agenda_id: int,
        direcao: str = Form(""),
        previsao_entrega: str = Form(""),
        data_evento: str = Form(""),
        data_operacao: str = Form(""),
        status_operacional: str = Form("pendente"),
        equipe: int = Form(1),
        link_localizacao: str = Form(""),
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    item = db.get(Agenda, agenda_id)
    if not item or item.empresa_id != empresa.id:
        raise HTTPException(404)

    status_anterior = item.status_operacional
    data_anterior = item.data
    hora_anterior = item.hora_inicio

    novo_status = status_operacional if status_operacional in {"pendente", "concluido"} else "pendente"
    falta_pagamento = 0
    if item.solicitacao:
        falta_pagamento = max((item.solicitacao.valor or 0) - (item.solicitacao.valor_pago or 0), 0)
    if item.tipo_evento == "retirada" and novo_status == "concluido" and falta_pagamento > 0.009:
        destino = request.headers.get("referer") or "/painel/reservas"
        partes = urlparse(destino)
        qs = dict(parse_qsl(partes.query, keep_blank_values=True))
        qs["op_erro"] = f"Não é possível encerrar a busca: falta receber R$ {falta_pagamento:,.2f}.".replace(",", "X").replace(".", ",").replace("X", ".")
        destino = urlunparse((partes.scheme, partes.netloc, partes.path, partes.params, urlencode(qs), partes.fragment))
        return RedirectResponse(destino, status_code=303)

    equipes_permitidas = equipes_permitidas_usuario(request, db)
    if equipe not in equipes_permitidas:
        raise HTTPException(403, "Você não possui acesso a esta equipe.")
    item.ordem_rota = equipe  # campo existente reaproveitado para identificar a equipe
    item.previsao_entrega = previsao_entrega
    item.link_localizacao = link_localizacao
    item.status_operacional = novo_status

    retirada_bloqueada = bool(item.tipo_evento == "retirada" and item.solicitacao and retirada_obrigatoria_ativa(item.solicitacao))

    nova_data = None
    data_informada = (data_operacao or data_evento or "").strip()
    if not retirada_bloqueada and data_informada:
        try:
            nova_data = datetime.strptime(data_informada, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(400, "Data da operação inválida.")

        data_limite_evento = item.solicitacao.data_evento if item.solicitacao else None
        if item.tipo_evento == "entrega" and data_limite_evento and nova_data > data_limite_evento:
            raise HTTPException(400, "A data da entrega não pode ser posterior à data do contrato.")
        if item.tipo_evento == "retirada" and data_limite_evento and nova_data < data_limite_evento:
            raise HTTPException(400, "A data da busca não pode ser anterior à data do contrato.")
        item.data = nova_data

    previsao_entrega = (previsao_entrega or "").strip()
    if not data_informada or not previsao_entrega:
        raise HTTPException(400, "Informe data, hora e equipe para roteirizar.")
    if not retirada_bloqueada and previsao_entrega:
        try:
            nova_hora = datetime.strptime(previsao_entrega, "%H:%M").time()
        except ValueError:
            raise HTTPException(400, "Hora da operação inválida.")
        item.previsao_entrega = previsao_entrega
        item.hora_inicio = nova_hora
    elif retirada_bloqueada:
        item.data = item.solicitacao.retirada_data or item.solicitacao.data_evento
        item.hora_inicio = item.solicitacao.retirada_hora or item.solicitacao.hora_fim or item.solicitacao.hora_inicio
        item.previsao_entrega = item.hora_inicio.strftime("%H:%M") if item.hora_inicio else ""

    # Marca visualmente que este card já foi roteirizado.
    # A cor cinza clara da tela usa este marcador dentro do histórico.
    usuario = request.session.get("usuario_nome") or request.session.get("usuario") or "Usuário"
    registro = (
        f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] "
        f"Roteirização salva por {usuario}. "
        f"Entrega: {data_anterior.strftime('%d/%m/%Y') if data_anterior else '-'} "
        f"{hora_anterior.strftime('%H:%M') if hora_anterior else '-'} → "
        f"{item.data.strftime('%d/%m/%Y') if item.data else '-'} "
        f"{item.hora_inicio.strftime('%H:%M') if item.hora_inicio else '-'}."
    )
    item.observacoes_operacionais = ((item.observacoes_operacionais or "") + "\n" + registro).strip()

    if item.tipo_evento == "entrega" and status_anterior != "concluido" and item.status_operacional == "concluido":
        criar_retirada_apos_entrega(db, item)

    db.commit()
    destino = request.headers.get("referer") or "/painel/reservas"
    return RedirectResponse(destino, status_code=303)


@app.post("/painel/reservas/roteirizacao")
async def salvar_roteirizacao_geral(
        request: Request,
        db: Session = Depends(get_db),
        empresa: Empresa = Depends(empresa_logada)
):
    dados = await request.json()
    ids = dados.get("ordem", [])
    usuario = request.session.get("usuario_nome") or request.session.get("usuario") or "Usuário"
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    for posicao, agenda_id in enumerate(ids, start=1):
        try:
            agenda_id = int(agenda_id)
        except (TypeError, ValueError):
            continue

        item = db.get(Agenda, agenda_id)
        if not item or item.empresa_id != empresa.id:
            continue

        item.ordem_rota = posicao
        marcador = f"[{agora}] Roteirização salva por {usuario}. Ordem da rota: {posicao}."
        item.observacoes_operacionais = ((item.observacoes_operacionais or "") + "\n" + marcador).strip()

    db.commit()
    return {"ok": True}


@app.get("/e/{slug}", response_class=HTMLResponse)
def portal_empresa(slug: str, request: Request, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    if not empresa:
        raise HTTPException(404, "Empresa não encontrada")
    return templates.TemplateResponse("publico/identificar.html", {"request": request, "empresa": empresa})


@app.post("/e/{slug}/buscar")
def buscar_cliente(slug: str, identificador: str = Form(...), db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    if not empresa:
        raise HTTPException(404)
    ident = limpar_identificador(identificador)
    return RedirectResponse(f"/e/{slug}/cadastro?identificador={ident}", status_code=303)


@app.get("/e/{slug}/pre-contrato", response_class=HTMLResponse)
def pre_contrato_cliente(slug: str, request: Request, erro: str = "", db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    if not empresa:
        raise HTTPException(404)
    return templates.TemplateResponse("publico/cadastro.html", {
        "request": request, "empresa": empresa, "cliente": None, "identificador": "",
        "cliente_encontrado": False, "cpf_confirmacao": "", "erro": erro,
        "campos_cfg": {ce.campo.chave: ce for ce in
                       db.query(CampoEmpresa).join(CampoGlobal).filter(CampoEmpresa.empresa_id == empresa.id).all()}
    })


@app.get("/e/{slug}/cadastro", response_class=HTMLResponse)
def cadastro_cliente(slug: str, request: Request, identificador: str = "", cpf_confirmacao: str = "", erro: str = "",
                     db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    ident = limpar_identificador(identificador)
    cliente_encontrado = db.query(Cliente).filter_by(empresa_id=empresa.id, identificador=ident).first()
    cliente = None
    cpf_limpo = limpar_identificador(cpf_confirmacao)
    if cliente_encontrado and cpf_limpo and limpar_identificador(cliente_encontrado.cpf) == cpf_limpo:
        cliente = cliente_encontrado
    return templates.TemplateResponse("publico/cadastro.html", {
        "request": request, "empresa": empresa, "cliente": cliente, "identificador": ident,
        "cliente_encontrado": bool(cliente_encontrado), "cpf_confirmacao": cpf_confirmacao, "erro": erro,
        "campos_cfg": {ce.campo.chave: ce for ce in
                       db.query(CampoEmpresa).join(CampoGlobal).filter(CampoEmpresa.empresa_id == empresa.id).all()}
    })


@app.post("/e/{slug}/reserva")
@app.post("/e/{slug}/pre-cadastro")
def salvar_pre_cadastro(
        request: Request, slug: str, identificador: str = Form(...), tipo_pessoa: str = Form("fisica"),
        nome: str = Form(""), data_nascimento: str = Form(""), telefone: str = Form(""), cpf: str = Form(""),
        cnpj: str = Form(""), email: str = Form(""), endereco: str = Form(""), numero: str = Form(""),
        complemento: str = Form(""),
        bairro: str = Form(""), cidade: str = Form(""), estado: str = Form(""), cep: str = Form(""),
        local: str = Form(""),
        local_nome: str = Form(""), acesso_local: str = Form(""), local_responsavel_nome: str = Form(""),
        local_responsavel_telefone: str = Form(""),
        data_evento: str = Form(...), hora_inicio: str = Form(...), observacoes: str = Form(""),
        acao: str = Form("salvar"),
        db: Session = Depends(get_db)
):
    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    cpf_limpo = limpar_identificador(cpf)
    cnpj_limpo = limpar_identificador(cnpj)
    telefone_limpo = limpar_identificador(telefone)
    ident = limpar_identificador(identificador)
    if not ident or ident == "novo":
        # Pré-contrato em branco: o identificador nasce dos dados reais enviados.
        # Prioridade: CPF/CNPJ quando existir; senão celular; senão código temporário.
        ident = cpf_limpo or cnpj_limpo or telefone_limpo or uuid.uuid4().hex[:12]
    campos_empresa = {
        ce.campo.chave: ce for ce in
        db.query(CampoEmpresa).join(CampoGlobal).filter(CampoEmpresa.empresa_id == empresa.id).all()
    }

    def campo_obrigatorio(chave: str) -> bool:
        ce = campos_empresa.get(chave)
        return bool(ce and ce.visivel and ce.obrigatorio)

    form_data = {
        "tipo_pessoa": tipo_pessoa, "nome": nome, "data_nascimento": data_nascimento, "telefone": telefone,
        "cpf": cpf, "cnpj": cnpj, "email": email, "endereco": endereco, "numero": numero, "complemento": complemento,
        "bairro": bairro, "cidade": cidade, "estado": estado, "cep": cep, "local": local, "local_nome": local_nome,
        "acesso_local": acesso_local, "local_responsavel_nome": local_responsavel_nome,
        "local_responsavel_telefone": local_responsavel_telefone, "data_evento": data_evento,
        "hora_inicio": hora_inicio, "observacoes": observacoes
    }

    def render_erro(codigo: str):
        cliente_encontrado = db.query(Cliente).filter_by(empresa_id=empresa.id, identificador=ident).first()
        return templates.TemplateResponse("publico/cadastro.html", {
            "request": request, "empresa": empresa, "cliente": None, "identificador": ident,
            "cliente_encontrado": bool(cliente_encontrado), "cpf_confirmacao": "", "erro": codigo,
            "campos_cfg": campos_empresa, "form": form_data
        }, status_code=400)

    if not celular_brasileiro_valido(telefone):
        return render_erro("whatsapp_invalido")
    if not celular_brasileiro_valido(local_responsavel_telefone):
        return render_erro("responsavel_whatsapp_invalido")
    if not local_responsavel_nome.strip():
        return render_erro("responsavel_whatsapp_invalido")
    if cpf_limpo and cnpj_limpo:
        return render_erro("cpf_cnpj")
    if tipo_pessoa == "fisica" and cpf_limpo and not cpf_valido(cpf_limpo):
        return render_erro("cpf_invalido")
    if tipo_pessoa == "fisica" and campo_obrigatorio("cpf") and not cpf_limpo:
        return render_erro("cpf_invalido")
    if tipo_pessoa == "juridica" and cnpj_limpo and not cnpj_valido(cnpj_limpo):
        return render_erro("cnpj_invalido")
    if tipo_pessoa == "juridica" and campo_obrigatorio("cnpj") and not cnpj_limpo:
        return render_erro("cnpj_invalido")
    cliente = db.query(Cliente).filter_by(empresa_id=empresa.id, identificador=ident).first()
    if not cliente:
        cliente = Cliente(empresa_id=empresa.id, identificador=ident)
        db.add(cliente)
    cliente.nome = nome
    cliente.data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date() if data_nascimento else None
    cliente.telefone = telefone_limpo or telefone
    cliente.cpf = cpf_limpo
    cliente.cnpj = cnpj_limpo
    cliente.email = email
    cliente.endereco = endereco
    cliente.numero = numero
    cliente.complemento = complemento
    cliente.bairro = bairro
    cliente.cidade = cidade
    cliente.estado = estado
    cliente.cep = cep
    cliente.observacoes = observacoes
    db.commit()
    db.refresh(cliente)

    if not hora_meia_em_meia_valida(hora_inicio):
        return render_erro("hora_invalida")
    data_obj = datetime.strptime(data_evento, "%Y-%m-%d").date()
    rascunho_existente = (
        db.query(Solicitacao)
        .join(Cliente, Solicitacao.cliente_id == Cliente.id)
        .filter(
            Solicitacao.empresa_id == empresa.id,
            Solicitacao.data_evento == data_obj,
            Solicitacao.status.in_(["reserva", "pre_reserva", "contrato_enviado", "aguardando_aceite"]),
            Cliente.telefone == (telefone_limpo or telefone)
        )
        .first()
    )
    if rascunho_existente:
        return render_erro("rascunho_duplicado")
    inicio_obj = datetime.strptime(hora_inicio, "%H:%M").time()
    fim_obj = None
    solicitacao = Solicitacao(
        empresa_id=empresa.id, cliente_id=cliente.id, data_evento=data_obj, hora_inicio=inicio_obj,
        hora_fim=fim_obj, bairro=bairro, local=endereco.strip(), local_nome=local_nome,
        local_responsavel_nome=local_responsavel_nome, local_responsavel_telefone=local_responsavel_telefone,
        acesso_local=acesso_local, observacoes=observacoes, status="pre_reserva"
    )
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)
    return RedirectResponse(f"/e/{slug}/obrigado/{solicitacao.id}", status_code=303)


def _wrap_pdf_text(c, texto, x, y, largura, leading=14, fonte="Helvetica", tamanho=10):
    """Quebra texto respeitando margem inferior para não invadir o rodapé."""
    margem_inferior = 110
    margem_superior = c._pagesize[1] - 70

    def nova_pagina_se_precisar(y_atual):
        if y_atual < margem_inferior:
            c.showPage()
            c.setFont(fonte, tamanho)
            return margem_superior
        return y_atual

    c.setFont(fonte, tamanho)
    for paragrafo in (texto or "").splitlines():
        palavras = paragrafo.split()
        if not palavras:
            y -= leading
            y = nova_pagina_se_precisar(y)
            continue
        linha = ""
        for palavra in palavras:
            teste = (linha + " " + palavra).strip()
            if c.stringWidth(teste, fonte, tamanho) <= largura:
                linha = teste
            else:
                y = nova_pagina_se_precisar(y)
                c.drawString(x, y, linha)
                y -= leading
                linha = palavra
        if linha:
            y = nova_pagina_se_precisar(y)
            c.drawString(x, y, linha)
            y -= leading
    return y


@app.get("/e/{slug}/contrato/{solicitacao_id}.pdf")
def contrato_cliente_pdf(slug: str, solicitacao_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
    except Exception:
        raise HTTPException(500, "Para gerar PDF, instale a dependência: reportlab")

    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    item = db.get(Solicitacao, solicitacao_id)
    if not empresa or not item or item.empresa_id != empresa.id:
        raise HTTPException(404)
    contrato = db.get(Contrato, item.contrato_id) if item.contrato_id else None
    produto = item.produto
    itens_reserva = db.query(ReservaItem).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).all()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    y = h - 70

    logo = empresa.logo_url or empresa.logo_idb_url
    if logo and logo.startswith("/static/"):
        logo_path = Path(logo.lstrip("/"))
        if logo_path.exists():
            try:
                c.drawImage(ImageReader(str(logo_path)), 40, y - 42, width=70, height=42, preserveAspectRatio=True,
                            mask='auto')
            except Exception:
                pass
    c.setFont("Helvetica-Bold", 16)
    c.drawString(120, y, empresa.nome or "Contrato")
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, y - 62, f"Contrato / Reserva #{item.id}")
    y -= 88

    c.setFont("Helvetica-Bold", 11);
    c.drawString(40, y, "Dados preenchidos");
    y -= 16
    for linha in linhas_informacoes_preenchidas_contrato(item, formato="texto"):
        if y < 110:
            c.showPage();
            y = h - 70
        y = _wrap_pdf_text(c, linha, 40, y, w - 80, leading=13, tamanho=9)
    y -= 8

    c.setFont("Helvetica-Bold", 11);
    c.drawString(40, y, "Itens");
    y -= 16
    if itens_reserva:
        for ri in itens_reserva:
            c.drawString(50, y, f"{ri.quantidade or 1}x {ri.nome} - R$ {moeda_br(ri.valor_total or 0)}")
            y -= 14
    elif produto:
        c.drawString(50, y, produto.nome);
        y -= 14
    y -= 10

    c.setFont("Helvetica-Bold", 11);
    c.drawString(40, y, contrato.nome if contrato else "Contrato");
    y -= 16
    y = _wrap_pdf_text(c, contrato.clausulas if contrato else (item.observacoes or ""), 40, y, w - 80)
    y -= 24
    if y < 120:
        c.showPage();
        y = h - 70
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Declaro estar ciente e de acordo com as condições desta locação.")
    y -= 42
    c.line(40, y, 330, y)
    y -= 14
    c.drawString(40, y, "Assinatura do cliente")
    y -= 28
    c.drawString(40, y, "Data: ____/____/________")
    y -= 20
    c.setFont("Helvetica", 9)
    if y < 90:
        c.showPage()
        y = h - 70
    c.drawString(40, y, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} - {empresa.nome}")
    c.save()
    buffer.seek(0)
    nome_pdf = f"contrato_{empresa.slug}_{item.id}.pdf"
    return Response(buffer.read(), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{nome_pdf}"'})


@app.get("/e/{slug}/contrato/{solicitacao_id}/clausulas", response_class=HTMLResponse)
def contrato_cliente_clausulas(slug: str, solicitacao_id: int, request: Request, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    item = db.get(Solicitacao, solicitacao_id)
    if not empresa or not item or item.empresa_id != empresa.id:
        raise HTTPException(404)
    contrato_ids = set()
    if item.contrato_id:
        contrato_ids.add(item.contrato_id)
    itens_reserva = db.query(ReservaItem).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).all()
    for ri in itens_reserva:
        if ri.produto_id:
            produto = db.get(ProdutoServico, ri.produto_id)
            if produto and produto.contrato_id:
                contrato_ids.add(produto.contrato_id)
    contratos_clausulas = []
    for cid in contrato_ids:
        c = db.get(Contrato, cid)
        if c and c.empresa_id == empresa.id and c.ativo:
            contratos_clausulas.append(c)
    if not contratos_clausulas and item.observacoes:
        contratos_clausulas = []
    return templates.TemplateResponse("publico/clausulas.html", {
        "request": request,
        "empresa": empresa,
        "item": item,
        "contratos_clausulas": contratos_clausulas,
    })


@app.get("/e/{slug}/contrato/{solicitacao_id}", response_class=HTMLResponse)
def contrato_cliente(slug: str, solicitacao_id: int, request: Request, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    item = db.get(Solicitacao, solicitacao_id)
    if not empresa or not item or item.empresa_id != empresa.id or item.status not in ["pre_reserva", "reserva",
                                                                                       "aguardando_aceite",
                                                                                       "contrato_enviado", "aceito",
                                                                                       "aguardando_pagamento",
                                                                                       "reserva_confirmada",
                                                                                       "cancelado_cliente"]:
        raise HTTPException(404)
    contrato = db.get(Contrato, item.contrato_id) if item.contrato_id else None
    produto = db.get(ProdutoServico, item.produto_id) if item.produto_id else None
    itens_reserva = db.query(ReservaItem).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).all()
    return templates.TemplateResponse("publico/contrato.html",
                                      {"request": request, "empresa": empresa, "item": item, "contrato": contrato,
                                       "produto": produto, "itens_reserva": itens_reserva})


@app.get("/e/{slug}/contrato/{solicitacao_id}/editar", response_class=HTMLResponse)
def editar_dados_contrato_cliente(slug: str, solicitacao_id: int, request: Request, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    item = db.get(Solicitacao, solicitacao_id)
    if not empresa or not item or item.empresa_id != empresa.id or not item.cliente:
        raise HTTPException(404)
    if status_reserva_confirmada(item.status) or item.status == "cancelado_cliente":
        return RedirectResponse(f"/e/{slug}/contrato/{item.id}", status_code=303)

    return templates.TemplateResponse("publico/cadastro.html", {
        "request": request,
        "empresa": empresa,
        "cliente": item.cliente,
        "identificador": item.cliente.identificador or item.cliente.telefone or item.cliente.cpf or "",
        "cliente_encontrado": True,
        "cpf_confirmacao": "",
        "erro": "",
        "modo_edicao_contrato": True,
        "item": item,
        "form": {
            "tipo_pessoa": "juridica" if item.cliente.cnpj else "fisica",
            "nome": item.cliente.nome or "",
            "telefone": item.cliente.telefone or "",
            "cpf": item.cliente.cpf or "",
            "cnpj": item.cliente.cnpj or "",
            "email": item.cliente.email or "",
            "endereco": item.cliente.endereco or "",
            "numero": item.cliente.numero or "",
            "complemento": item.cliente.complemento or "",
            "bairro": item.bairro or item.cliente.bairro or "",
            "cidade": item.cliente.cidade or "",
            "estado": item.cliente.estado or "",
            "cep": item.cliente.cep or "",
            "local": item.local or "",
            "local_nome": item.local_nome or "",
            "acesso_local": item.acesso_local or "",
            "local_responsavel_nome": item.local_responsavel_nome or "",
            "local_responsavel_telefone": item.local_responsavel_telefone or "",
            "data_evento": item.data_evento.isoformat() if item.data_evento else "",
            "hora_inicio": item.hora_inicio.strftime("%H:%M") if item.hora_inicio else "",
            "observacoes": item.observacoes or item.cliente.observacoes or "",
        },
        "campos_cfg": {ce.campo.chave: ce for ce in
                       db.query(CampoEmpresa).join(CampoGlobal).filter(CampoEmpresa.empresa_id == empresa.id).all()}
    })


@app.post("/e/{slug}/contrato/{solicitacao_id}/editar")
def salvar_dados_contrato_cliente(
        slug: str, solicitacao_id: int,
        identificador: str = Form(""), tipo_pessoa: str = Form("fisica"),
        nome: str = Form(""), data_nascimento: str = Form(""), telefone: str = Form(""), cpf: str = Form(""),
        cnpj: str = Form(""), email: str = Form(""), endereco: str = Form(""), numero: str = Form(""),
        complemento: str = Form(""), bairro: str = Form(""), cidade: str = Form(""), estado: str = Form(""),
        cep: str = Form(""), local: str = Form(""), local_nome: str = Form(""), acesso_local: str = Form(""),
        local_responsavel_nome: str = Form(""), local_responsavel_telefone: str = Form(""),
        data_evento: str = Form(...), hora_inicio: str = Form(...), observacoes: str = Form(""),
        db: Session = Depends(get_db)
):
    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    item = db.get(Solicitacao, solicitacao_id)
    if not empresa or not item or item.empresa_id != empresa.id or not item.cliente:
        raise HTTPException(404)
    if status_reserva_confirmada(item.status) or item.status == "cancelado_cliente":
        return RedirectResponse(f"/e/{slug}/contrato/{item.id}", status_code=303)

    cliente = item.cliente
    cliente.nome = nome.strip()
    cliente.data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date() if data_nascimento else None
    cliente.telefone = limpar_identificador(telefone) or telefone.strip()
    cliente.cpf = limpar_identificador(cpf)
    cliente.cnpj = limpar_identificador(cnpj)
    cliente.email = email.strip()
    cliente.endereco = endereco.strip()
    cliente.numero = numero.strip()
    cliente.complemento = complemento.strip()
    cliente.bairro = bairro.strip()
    cliente.cidade = cidade.strip()
    cliente.estado = estado.strip()
    cliente.cep = limpar_identificador(cep) or cep.strip()
    cliente.observacoes = observacoes.strip()
    cliente.identificador = cliente.cpf or cliente.cnpj or cliente.telefone or limpar_identificador(identificador) or cliente.identificador

    item.data_evento = datetime.strptime(data_evento, "%Y-%m-%d").date()
    item.hora_inicio = datetime.strptime(hora_inicio, "%H:%M").time()
    item.bairro = bairro.strip()
    item.local = local.strip() or endereco.strip()
    item.local_nome = local_nome.strip()
    item.acesso_local = acesso_local.strip()
    item.local_responsavel_nome = local_responsavel_nome.strip()
    item.local_responsavel_telefone = limpar_identificador(local_responsavel_telefone) or local_responsavel_telefone.strip()
    item.observacoes = observacoes.strip()

    db.commit()
    return RedirectResponse(f"/e/{slug}/contrato/{item.id}", status_code=303)


@app.post("/e/{slug}/cancelar/{solicitacao_id}")
def cancelar_contrato(slug: str, solicitacao_id: int, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    item = db.get(Solicitacao, solicitacao_id)
    if not empresa or not item or item.empresa_id != empresa.id:
        raise HTTPException(404)
    if item.status != "cancelado_cliente":
        item.status = "cancelado_cliente"
        item.cancelado_em = agora_utc()
        db.commit()
    return RedirectResponse(f"/e/{slug}/obrigado/{solicitacao_id}", status_code=303)


@app.post("/e/{slug}/aceitar/{solicitacao_id}")
def aceitar_contrato(slug: str, solicitacao_id: int, aceite: Optional[str] = Form(None), db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter_by(slug=slug, ativa=True).first()
    item = db.get(Solicitacao, solicitacao_id)
    if not empresa or not item or item.empresa_id != empresa.id:
        raise HTTPException(404)
    itens_reserva = db.query(ReservaItem).filter_by(empresa_id=empresa.id, solicitacao_id=item.id).count()
    if item.status in ["aguardando_aceite", "contrato_enviado"] and item.contrato_id and itens_reserva > 0:
        item.status = "aguardando_pagamento" if (item.sinal or 0) > 0 else "reserva_confirmada"
        item.aceite_em = agora_utc()
        item.aprovado_em = item.aceite_em
        fim_obj = item.hora_fim or (somar_minutos(item.hora_inicio,
                                                  item.produto.duracao_minutos) if item.produto and item.produto.duracao_minutos else None)
        item.hora_fim = fim_obj
        criar_eventos_operacionais(db, item)
        db.commit()
    return RedirectResponse(f"/e/{slug}/obrigado/{solicitacao_id}", status_code=303)


@app.get("/e/{slug}/obrigado/{solicitacao_id}", response_class=HTMLResponse)
def obrigado(slug: str, solicitacao_id: int, request: Request, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    solicitacao = db.get(Solicitacao, solicitacao_id)
    return templates.TemplateResponse("publico/obrigado.html",
                                      {"request": request, "empresa": empresa, "solicitacao": solicitacao})
