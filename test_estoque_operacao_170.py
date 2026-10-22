"""Regressões 1.0.170: painel móvel, opcionais em lote e saldo operacional."""
from datetime import date, timedelta, time
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request
from database import Base
from models import (
    Empresa, Cliente, ProdutoServico, Solicitacao, ReservaItem,
    Agenda, ItemProdutoServicoEstoque, ProdutoServicoRecurso,
    SolicitacaoOpcional,
)
import app


def _db_com_operacoes():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    empresa = Empresa(nome="Teste", slug="teste", modulo_recursos_ativo=True)
    db.add(empresa);db.flush()
    cli = Cliente(empresa_id=empresa.id, identificador='teste171', nome='Cliente teste')
    produto = ProdutoServico(empresa_id=empresa.id,nome="Portátil",quantidade_disponivel=3,ativo=True)
    micro = ItemProdutoServicoEstoque(empresa_id=empresa.id,nome="Microfone", quantidade_estoque=6, ativo=True)
    pedestal = ItemProdutoServicoEstoque(empresa_id=empresa.id,nome="Pedestal",quantidade_estoque=3,ativo=True)
    db.add_all([cli,produto,micro,pedestal]);db.flush()
    db.add(ProdutoServicoRecurso(empresa_id=empresa.id,produto_id=produto.id,item_estoque_id=micro.id,quantidade_por_unidade=2))
    hoje = date.today()
    def pedido(data,entrega_status,retirada_status,op_qtd=0,status='reserva_confirmada'):
        sol = Solicitacao(empresa_id=empresa.id, cliente_id=cli.id, data_evento=data, hora_inicio=time(18), status=status)
        db.add(sol);db.flush()
        db.add(ReservaItem(empresa_id=empresa.id,solicitacao_id=sol.id,produto_id=produto.id,nome='Portátil',quantidade=1))
        if op_qtd:
            db.add(SolicitacaoOpcional(empresa_id=empresa.id,solicitacao_id=sol.id,nome='Pedestal extra',quantidade=op_qtd,item_estoque_id=pedestal.id,valor_total=10))
        db.add_all([
            Agenda(empresa_id=empresa.id, solicitacao_id=sol.id, data=data, hora_inicio=time(14),titulo="entrega",tipo_evento='entrega',status_operacional=entrega_status),
            Agenda(empresa_id=empresa.id, solicitacao_id=sol.id, data=data+timedelta(days=1), hora_inicio=time(10),titulo="retirada",tipo_evento='retirada',status_operacional=retirada_status),
        ])
        return sol
    sol_rua=pedido(hoje-timedelta(days=1),'concluido','pendente',2,status='cancelada')
    sol_dia=pedido(hoje,'pendente','pendente',1)
    sol_voltou=pedido(hoje-timedelta(days=4),'concluido','concluido',1)
    db.commit()
    return db,empresa,sol_rua,sol_dia,sol_voltou


def _req():
    return Request({'type':'http','method':'GET','path':'/painel/reservas/consumo-estoque',
      'root_path':'','query_string':b'', 'headers':[(b'host',b'localhost')],
      'scheme':'http','server':('localhost',80),'client':('127.0.0.1',12345),
      'session':{'empresa_id':1, 'acesso_total':True}})


def test_saldo_operacao_estoque_e_entregas():
    db,empresa,sol_rua,sol_dia,sol_voltou=_db_com_operacoes()
    resp=app.relatorio_estoque_operacao(_req(),data=date.today().isoformat(), db=db,empresa=empresa)
    c=resp.context
    produtos={p['nome']:p for p in c['produtos']}
    recursos={p['nome']:p for p in c['recursos']}
    assert produtos['Portátil']['total']==3
    assert produtos['Portátil']['na_rua']==1  # entregue ontem, ainda sem retirada, mesmo contrato cancelado
    assert produtos['Portátil']['na_loja']==2
    assert produtos['Portátil']['saidas_dia']==1
    assert produtos['Portátil']['a_preparar']==1
    assert recursos['Microfone']['na_rua']==2
    assert recursos['Microfone']['a_preparar']==2
    assert recursos['Pedestal']['na_rua']==2  # 2x opcional no contrato antigo
    assert recursos['Pedestal']['a_preparar']==1  # 1x opcional no contrato novo
    assert recursos['Pedestal']['saldo_apos_saida']==0
    assert len(c['contratos'])==2
    db.close()


def test_insuficiencia_sem_antecipar_devolucao():
    dado=app._resumo_quantidades_operacao(3,2,2,2)
    assert (dado['na_loja'],dado['falta'],dado['saldo_apos_saida'])==(1,1,0)
    assert app._resumo_quantidades_operacao(1,2,0,0)['divergencia_fisica']==1


def test_infinitepay_mobile_nao_empilha_letras():
    css=(Path(__file__).parent/'static/css/style.css').read_text()
    html=(Path(__file__).parent/'templates/admin/solicitacao_detalhe.html').read_text()
    assert '.infinitepay-cobranca .infinitepay-principal{min-width:0;' in css
    assert '.infinitepay-cobranca .infinitepay-valor{white-space:nowrap}' in css
    assert 'infinitepay-principal' in html and 'infinitepay-acoes' in html
    assert '/static/css/style.css?v={{ APP_VERSION }}' in (Path(__file__).parent/'templates/base.html').read_text()


def test_analise_em_lote_inclui_opcionais():
    db, empresa, _, sol_dia, _ = _db_com_operacoes()
    resultado=app._analises_estoque_lote(db,[sol_dia])[sol_dia.id]
    consumos={x['nome']:x for x in resultado['recursos']}
    assert consumos['Microfone']['padrao'] == 2
    assert consumos['Pedestal']['padrao'] == 1
    assert consumos['Pedestal']['necessario'] == 1
    assert resultado['tem_conflito'] is False
    db.close()


def test_link_operacao_e_template():
    pagina=(Path(__file__).parent/'templates/admin/preparar.html').read_text()
    assert '/painel/reservas/consumo-estoque?data={{ data_inicial }}' in pagina
    app.templates.get_template('admin/operacao_consumo_estoque.html')
