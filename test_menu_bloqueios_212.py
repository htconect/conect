"""Regressão do menu único de bloqueios (1.0.212)."""
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.requests import Request

import app
from database import Base
from models import BloqueioData, BloqueioProduto, Empresa, ProdutoServico


@pytest.fixture
def ambiente():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        a = Empresa(nome='Empresa A', slug='a')
        b = Empresa(nome='Empresa B', slug='b')
        db.add_all([a, b])
        db.flush()
        p = ProdutoServico(empresa_id=a.id, nome='Portátil', quantidade_disponivel=3, ativo=True)
        q = ProdutoServico(empresa_id=b.id, nome='Produto de outra empresa', quantidade_disponivel=3, ativo=True)
        db.add_all([p, q])
        db.flush()
        dia = date.today() + timedelta(days=6)
        db.add_all([
            BloqueioData(empresa_id=a.id, data_inicio=dia, data_fim=dia, ativo=True),
            BloqueioData(empresa_id=b.id, data_inicio=dia, data_fim=dia, ativo=True),
            BloqueioProduto(empresa_id=a.id, produto_id=p.id, data_inicio=dia, data_fim=dia, ativo=True),
            BloqueioProduto(empresa_id=b.id, produto_id=q.id, data_inicio=dia, data_fim=dia, ativo=True),
        ])
        db.commit()
        yield db, a, b, p, dia
    engine.dispose()


def requisicao(empresa_id, acesso_total=False, **acessos):
    return Request({
        'type': 'http', 'method': 'GET', 'path': '/painel/bloqueios',
        'root_path': '', 'scheme': 'http', 'server': ('testserver', 80),
        'query_string': b'', 'headers': [], 'app': app.app,
        'session': {'empresa_id': empresa_id, 'usuario_nome': 'Teste',
                    'acesso_total': acesso_total, 'acessos': acessos},
    })


def test_central_exibe_ambos_e_isola_empresa(ambiente):
    db, a, b, p, dia = ambiente
    resp = app.painel_bloqueios(requisicao(a.id, acesso_total=True), db=db, empresa=a)
    html = resp.body.decode('utf-8')
    assert resp.status_code == 200
    assert 'Bloqueio geral' in html
    assert 'Bloquear equipamento' in html
    assert 'Portátil' in html
    assert 'Produto de outra empresa' not in html


def test_permissoes_independentes(ambiente):
    db, a, b, p, dia = ambiente
    geral = app.painel_bloqueios(requisicao(a.id, agenda=True), db=db, empresa=a).body.decode()
    assert 'Bloquear todas as locações' in geral
    assert 'Bloquear equipamento' not in geral
    individual = app.painel_bloqueios(requisicao(a.id, cadastros=True), db=db, empresa=a).body.decode()
    assert 'Bloquear todas as locações' not in individual
    assert 'Bloquear equipamento' in individual
    with pytest.raises(app.HTTPException) as exc:
        app.painel_bloqueios(requisicao(a.id), db=db, empresa=a)
    assert exc.value.status_code == 403


def test_bloqueio_geral_antigo_segue_ativo(ambiente):
    db, a, b, p, dia = ambiente
    resposta = app.criar_bloqueio_data(request=requisicao(a.id), data_inicio=dia.isoformat(),
        data_fim=(dia + timedelta(days=2)).isoformat(), descricao='Feriado', db=db, empresa=a)
    assert resposta.status_code == 303
    assert '/painel/bloqueios?salvo=geral' in resposta.headers['location']
    bloqueio = db.query(BloqueioData).filter_by(empresa_id=a.id, descricao='Feriado').one()
    assert app._bloqueio_data_empresa(db, a.id, dia) is not None
    resposta = app.excluir_bloqueio_data(bloqueio.id, request=requisicao(a.id), db=db, empresa=a)
    assert resposta.status_code == 303
    assert db.get(BloqueioData, bloqueio.id) is None


def test_bloqueio_individual_volta_ao_novo_menu(ambiente):
    db, a, b, p, dia = ambiente
    resposta = app.criar_bloqueio_produto(produto_id=p.id, data_inicio=dia.isoformat(),
        data_fim=(dia + timedelta(days=1)).isoformat(), descricao='Manutenção', db=db, empresa=a)
    assert resposta.status_code == 303
    assert '/painel/bloqueios?salvo=equipamento' in resposta.headers['location']
    bloqueio = db.query(BloqueioProduto).filter_by(empresa_id=a.id, descricao='Manutenção').one()
    resposta = app.excluir_bloqueio_produto(bloqueio.id, db=db, empresa=a)
    assert '/painel/bloqueios?salvo=removeu_equipamento' in resposta.headers['location']
