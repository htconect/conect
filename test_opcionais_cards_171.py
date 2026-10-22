"""Regressões 1.0.171: todos os opcionais em cards, auditoria de cadastro e saldo."""
from pathlib import Path
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request
from database import Base
from models import OpcionalEmpresa, SolicitacaoOpcional
import app
from test_estoque_operacao_170 import _db_com_operacoes, _req


def test_card_exibe_opcional_vinculado_e_nao_vinculado_com_quantidades():
    db, empresa, _, sol, _ = _db_com_operacoes()
    # Simula dois opcionais diferentes no mesmo contrato, um com estoque e outro sem.
    db.add(SolicitacaoOpcional(empresa_id=empresa.id, solicitacao_id=sol.id,
        nome="Catálogo Encadernado", quantidade=1, valor_total=10,
        item_estoque_id=None))
    db.commit()
    a = app._analises_estoque_lote(db, [sol])[sol.id]
    assert [(o['nome'], o['quantidade'], o['controla_estoque']) for o in a['opcionais']] == [
        ('Catálogo Encadernado',1,False), ('Pedestal extra',1,True)]
    assert {r['nome']: r['necessario'] for r in a['recursos']} == {'Microfone':2, 'Pedestal':1}
    assert [x['nome'] for x in a['opcionais_sem_estoque']] == ['Catálogo Encadernado']
    db.close()


def test_ajuste_manual_e_opcionais_nao_causam_baixa_dupla():
    from models import SolicitacaoRecurso
    db, empresa, _, sol, _ = _db_com_operacoes()
    ped = next(x for x in app._itens_estoque_empresa(db, empresa.id) if x.nome=='Pedestal')
    db.add(SolicitacaoRecurso(empresa_id=empresa.id, solicitacao_id=sol.id,
      item_estoque_id=ped.id, quantidade=2))
    db.commit()
    a=app._analises_estoque_lote(db,[sol])[sol.id]
    rec = next(x for x in a['recursos'] if x['nome']=='Pedestal')
    assert rec['padrao']==1 and rec['necessario']==2 and rec['ajustado']
    assert len(a['opcionais'])==1 and a['opcionais'][0]['quantidade']==1
    db.close()


def test_auditoria_examina_todos_opcionais_ativos_e_snapshot_sem_vinculo():
    db, empresa, _, sol, _=_db_com_operacoes()
    recurso=next(x for x in app._itens_estoque_empresa(db,empresa.id) if x.nome=='Pedestal')
    vinculado=OpcionalEmpresa(empresa_id=empresa.id, nome='Catálogo Encadernado',
          ativo=True,quantidade=1,item_estoque_id=recurso.id)
    sem=OpcionalEmpresa(empresa_id=empresa.id,nome='Outro opcional',ativo=True,
          quantidade=1, item_estoque_id=None)
    db.add_all([vinculado,sem]);db.flush()
    db.add(SolicitacaoOpcional(empresa_id=empresa.id, solicitacao_id=sol.id,
          opcional_id=vinculado.id, item_estoque_id=None, nome='Catálogo Encadernado',
          quantidade=1, valor_total=10))
    db.commit()
    resp=app.relatorio_estoque_operacao(_req(),data=date.today().isoformat(),db=db,empresa=empresa)
    msgs=' '.join(a['mensagem'] for a in resp.context['avisos'] if a['contrato']==sol.id)
    assert 'vínculo no contrato diferente do cadastro' in msgs
    assert 'não entram no estoque' in msgs
    assert any(a['nome']=='Outro opcional' for a in resp.context['avisos_cadastro'])
    db.close()


def test_cards_operacao_e_agenda_incluem_opcionais():
    root=Path(__file__).parent
    for p in ('templates/admin/preparar.html','templates/admin/agenda.html'):
        html=(root/p).read_text()
        assert 'ae.opcionais' in html
        assert 'op.quantidade' in html and 'op.nome' in html
        assert 'sem vínculo de estoque' in html
        app.templates.get_template(p.replace('templates/',''))


def test_opcional_soma_ao_recurso_do_proprio_equipamento_uma_vez():
    db, empresa, _, sol, _ = _db_com_operacoes()
    from models import ItemProdutoServicoEstoque
    micro = db.query(ItemProdutoServicoEstoque).filter_by(empresa_id=empresa.id,nome='Microfone').first()
    db.add(SolicitacaoOpcional(empresa_id=empresa.id, solicitacao_id=sol.id,
        nome="Microfone extra", quantidade=1, valor_total=20,item_estoque_id=micro.id))
    db.commit()
    a=app._analises_estoque_lote(db,[sol])[sol.id]
    recurso = next(x for x in a['recursos'] if x['nome']=='Microfone')
    assert recurso['padrao']==3 and recurso['necessario']==3
    assert sum(x['quantidade'] for x in a['opcionais'] if x['nome']=='Microfone extra')==1
    resp=app.relatorio_estoque_operacao(_req(),data=date.today().isoformat(),db=db,empresa=empresa)
    micro_linha=next(x for x in resp.context['recursos'] if x['nome']=='Microfone')
    assert micro_linha['a_preparar']==3
    db.close()
