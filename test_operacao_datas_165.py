"""Regressão das datas da Operação após remarcação de contrato — SQLite isolado."""
from datetime import date, time
from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import Empresa, Cliente, ProdutoServico, Solicitacao, ReservaItem, Equipe, Agenda
import app

ANTIGO = date(2026, 10, 12)
NOVO = date(2026, 11, 7)

def base(obrigatoria=False, concluida=False):
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    empresa = Empresa(nome='Karaokê RJ', slug='karaokerj')
    db.add(empresa); db.flush()
    cliente = Cliente(empresa_id=empresa.id, identificador='cliente-teste', nome='Teste')
    produto = ProdutoServico(empresa_id=empresa.id, nome='Portátil JBL', prazo_retirada_dias=1)
    equipe = Equipe(empresa_id=empresa.id, nome='Equipe 1')
    db.add_all([cliente, produto, equipe]); db.flush()
    item = Solicitacao(empresa_id=empresa.id, cliente_id=cliente.id, produto_id=produto.id, data_evento=ANTIGO,
        hora_inicio=time(9,0), hora_fim=time(13,0), status='reserva_confirmada', retirada_obrigatoria=obrigatoria,
        retirada_data=ANTIGO if obrigatoria else None, retirada_hora=time(13,0) if obrigatoria else None)
    db.add(item); db.flush()
    db.add(ReservaItem(empresa_id=empresa.id, solicitacao_id=item.id, produto_id=produto.id, nome='Portátil JBL'))
    entrega = Agenda(empresa_id=empresa.id, solicitacao_id=item.id, tipo_evento='entrega', data=ANTIGO,
       hora_inicio=time(9), hora_fim=time(13), titulo='Portátil JBL', equipe_id=equipe.id, roteirizado=True,
       previsao_entrega='09:00', status_operacional='concluido' if concluida else 'pendente')
    busca = Agenda(empresa_id=empresa.id, solicitacao_id=item.id, tipo_evento='retirada', data=date(2026,10,12) if obrigatoria else date(2026,10,13),
       hora_inicio=time(13) if obrigatoria else time(8), titulo='Portátil JBL', equipe_id=equipe.id,
       roteirizado=True, previsao_entrega='13:00' if obrigatoria else '08:00', status_operacional='pendente')
    db.add_all([entrega,busca]); db.commit()
    return db, item, entrega, busca, equipe

def test_remarcacao_muda_entrega_e_retirada_pendente():
    db,item,entrega,busca,equipe=base()
    item.data_evento=NOVO
    n,bloqueados=app.sincronizar_datas_operacao_com_contrato(db,item,ANTIGO,usuario='Junior')
    db.commit()
    assert (n,bloqueados)==(2,0)
    assert entrega.data == NOVO and busca.data == date(2026,11,8)
    assert entrega.equipe_id == equipe.id and entrega.roteirizado and entrega.previsao_entrega == '09:00'
    assert busca.equipe_id == equipe.id and busca.roteirizado
    assert 'Junior' in entrega.observacoes_operacionais
    assert '12/10/2026' in entrega.observacoes_operacionais
    # Recarregar não pode remapear uma segunda vez.
    assert app.sincronizar_datas_operacao_com_contrato(db,item,NOVO)==(0,0)
    db.close()

def test_corrigir_operacao_antiga_sem_data_anterior():
    db,item,entrega,busca,equipe=base()
    item.data_evento=NOVO; db.commit()
    # cenário da imagem: contrato alterado, operação antiga ainda 12/10
    assert entrega.data == ANTIGO
    n,bloqueados=app.sincronizar_datas_operacao_com_contrato(db,item,corrigir_existentes=True)
    db.commit()
    assert (n,bloqueados)==(2,0)
    assert entrega.data==NOVO and busca.data==date(2026,11,8)
    assert entrega.equipe_id == equipe.id
    db.close()

def test_retirada_obrigatoria_segue_contrato():
    db,item,entrega,busca,equipe=base(obrigatoria=True)
    item.data_evento=NOVO; item.retirada_data=NOVO; item.retirada_hora=time(14)
    n,_=app.sincronizar_datas_operacao_com_contrato(db,item,ANTIGO)
    assert n==2 and entrega.data==NOVO and busca.data==NOVO and busca.hora_inicio==time(14)
    db.close()

def test_concluidas_nao_alteram_historico():
    db,item,entrega,busca,equipe=base(concluida=True)
    item.data_evento=NOVO
    n,bloqueados=app.sincronizar_datas_operacao_com_contrato(db,item,ANTIGO)
    assert n==0 and bloqueados==1
    assert entrega.data==ANTIGO and busca.data==date(2026,10,13)
    db.close()

def test_retirada_obrigatoria_antiga_e_corrigida():
    db,item,entrega,busca,equipe=base(obrigatoria=True)
    item.data_evento=NOVO
    # Tela antiga pode mudar somente a data do evento, sem editar retirada_data.
    assert item.retirada_data==ANTIGO
    app.sincronizar_datas_operacao_com_contrato(db,item,ANTIGO)
    assert item.retirada_data==NOVO and busca.data==NOVO
    db.close()

def test_correcao_manual_alinha_busca_obrigatoria_desatualizada():
    db,item,entrega,busca,equipe=base(obrigatoria=True)
    item.data_evento=NOVO
    db.commit()
    assert item.retirada_data==ANTIGO
    app.sincronizar_datas_operacao_com_contrato(db,item,corrigir_existentes=True)
    assert item.retirada_data==NOVO and busca.data==NOVO
    db.close()

def test_endpoint_corrige_datas_operacionais_existentes():
    db,item,entrega,busca,equipe=base()
    item.data_evento=NOVO; db.commit()
    req=SimpleNamespace(session={'usuario_nome':'Junior'}, headers={})
    empresa=db.get(Empresa,item.empresa_id)
    response=app.corrigir_data_operacao_pelo_contrato(entrega.id,req,db=db,empresa=empresa)
    assert response.status_code==303
    assert 'data_inicial=2026-11-07' in response.headers['location']
    assert 'datas_ok=2' in response.headers['location']
    assert entrega.data==NOVO and busca.data==date(2026,11,8)
    db.close()

def test_rotas_e_formulario_disponiveis():
    rotas={getattr(r,'path','') for r in app.app.routes}
    assert '/painel/agenda/{agenda_id}/sincronizar-data-contrato' in rotas
    pagina=app.templates.get_template('admin/preparar.html')
    assert pagina is not None

if __name__=='__main__':
    for nome,func in sorted(globals().copy().items()):
        if nome.startswith('test_') and callable(func):
            func()
            print('OK',nome)
