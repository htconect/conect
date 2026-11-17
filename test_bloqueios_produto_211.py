"""Novos bloqueios por equipamento: isolamento, datas e proteção da vitrine."""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app
from database import Base
from models import BloqueioProduto, Empresa, ProdutoServico


@pytest.fixture
def base_simulada():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        a = Empresa(nome='Empresa A', slug='empresa-a')
        b = Empresa(nome='Empresa B', slug='empresa-b')
        db.add_all([a, b])
        db.flush()
        p = ProdutoServico(empresa_id=a.id, nome='Portátil', quantidade_disponivel=3, ativo=True, vitrine_ativo=True)
        outro = ProdutoServico(empresa_id=a.id, nome='Básico', quantidade_disponivel=2, ativo=True, vitrine_ativo=True)
        alheio = ProdutoServico(empresa_id=b.id, nome='Portátil B', quantidade_disponivel=2, ativo=True, vitrine_ativo=True)
        db.add_all([p, outro, alheio]); db.commit()
        yield db, a, b, p, outro, alheio
    engine.dispose()


def test_bloqueio_data_e_empresa(base_simulada):
    db, a, b, p, outro, alheio = base_simulada
    inicio = date.today() + timedelta(days=7)
    fim = inicio + timedelta(days=2)
    db.add(BloqueioProduto(empresa_id=a.id, produto_id=p.id, data_inicio=inicio, data_fim=fim, descricao='Manutenção', ativo=True))
    db.commit()
    assert p.id in app._bloqueios_produtos_na_data(db, a.id, inicio)
    assert p.id in app._bloqueios_produtos_na_data(db, a.id, fim)
    assert p.id not in app._bloqueios_produtos_na_data(db, a.id, fim + timedelta(days=1))
    assert not app._bloqueios_produtos_na_data(db, b.id, inicio)
    assert not app._bloqueio_produto_periodo(db, a.id, p.id, inicio-timedelta(days=2), inicio)
    assert app._bloqueio_produto_periodo(db, a.id, p.id, inicio-timedelta(days=1), inicio+timedelta(days=1))
    assert app._erro_bloqueio_produto(db, a.id, p, inicio) == f'Portátil está bloqueado para aluguel em {inicio:%d/%m/%Y} (Manutenção).'
    assert not app._erro_bloqueio_produto(db, a.id, outro, inicio)


def test_vitrine_especial_nao_ignora_bloqueio_produto(base_simulada):
    db, a, b, p, outro, alheio = base_simulada
    inicio = date.today() + timedelta(days=7)
    db.add(BloqueioProduto(empresa_id=a.id, produto_id=p.id, data_inicio=inicio, data_fim=inicio+timedelta(days=1), ativo=True))
    db.commit()
    def saldos(dia, **kwargs):
        dados = app._itens_vitrine_publica(db, a, dia, 'residencial', apenas_disponibilidade=True, **kwargs)
        return {x['produto'].id:x['disponiveis'] for x in dados}
    try:
        bloqueados = saldos(inicio)
        link_especial = saldos(inicio, ignorar_bloqueio=True)
    except (ValueError, AttributeError, TypeError) as exc:
        pytest.fail(f'falha na vitrine real: {exc}')
    assert bloqueados[p.id] == 0
    assert link_especial[p.id] == 0
    assert link_especial[outro.id] == 2
    minimo, limitante = app._saldo_vitrine_periodo(db, a, p.id, inicio-timedelta(days=1), inicio+timedelta(days=2), 'residencial')
    assert minimo == 0
    assert limitante == inicio
    # Uma entrega antes do bloqueio, com retirada no início do bloqueio, está livre.
    assert app._saldo_vitrine_periodo(db, a, p.id, inicio-timedelta(days=1), inicio, 'residencial')[0] == 3


def test_criacao_exclusao_e_empresa_correta(base_simulada):
    db, a, b, p, outro, alheio = base_simulada
    inicio = date.today() + timedelta(days=3)
    resp = app.criar_bloqueio_produto(produto_id=p.id, data_inicio=inicio.isoformat(), data_fim=(inicio+timedelta(days=1)).isoformat(), descricao='Para revisão', db=db, empresa=a)
    assert resp.status_code == 303
    reg = db.query(BloqueioProduto).filter_by(empresa_id=a.id, produto_id=p.id).one()
    assert reg.descricao == 'Para revisão'
    with pytest.raises(app.HTTPException) as error:
        app.excluir_bloqueio_produto(reg.id, db=db, empresa=b)
    assert error.value.status_code == 404
    assert app.excluir_bloqueio_produto(reg.id, db=db, empresa=a).status_code == 303
    assert db.query(BloqueioProduto).filter_by(id=reg.id).count() == 0
