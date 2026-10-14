"""Regressões do Connect 1.0.166 em banco SQLite isolado."""
from datetime import date, time
from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import Empresa, Cliente, Solicitacao, Agenda, UsuarioEmpresa, ProdutoServico, ReservaItem
import app

DIA=date(2026,10,31)

def base(slug='karaokerj'):
    engine=create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    db=sessionmaker(bind=engine)()
    empresa=Empresa(nome='Karaokê RJ',slug=slug, usuario_admin='admin', retirada_hora_maxima='22:00',
                    vitrine_responsavel_token='luiz-token',vitrine_responsavel_configurado=False,
                    pre_contrato_token='admin-token',pre_contrato_responsavel_nome='Administrador',
                    pre_contrato_responsavel_telefone='21999990000')
    db.add(empresa);db.flush()
    db.add_all([
      UsuarioEmpresa(empresa_id=empresa.id, nome='Luiz', usuario='luiz', senha='teste', ativo=True,
                     telefone='21911112222',pre_contrato_token='luiz-token'),
      UsuarioEmpresa(empresa_id=empresa.id, nome='Júnior', usuario='junior', senha='teste', ativo=True,
                     telefone='21933334444',pre_contrato_token='junior-token'),
    ])
    cliente=Cliente(empresa_id=empresa.id,identificador='cliente',nome='Ana')
    produto=ProdutoServico(empresa_id=empresa.id,nome='JBL')
    db.add_all([cliente,produto]);db.flush()
    item=Solicitacao(empresa_id=empresa.id,cliente_id=cliente.id,produto_id=produto.id,
                     status='reserva_confirmada',data_evento=DIA,hora_inicio=time(12),hora_fim=time(16),
                     retirada_obrigatoria=True,retirada_data=DIA,retirada_hora=time(19),valor=550,
                     responsavel_contrato='Luiz',responsavel_contrato_telefone='21911112222')
    db.add(item);db.flush()
    db.add(ReservaItem(empresa_id=empresa.id,solicitacao_id=item.id,produto_id=produto.id,nome='JBL'))
    entrega=Agenda(empresa_id=empresa.id,solicitacao_id=item.id,tipo_evento='entrega',data=DIA,
                   hora_inicio=time(11),titulo='JBL',roteirizado=True,status_operacional='pendente')
    busca=Agenda(empresa_id=empresa.id,solicitacao_id=item.id,tipo_evento='retirada',data=DIA,
                 hora_inicio=time(19),titulo='JBL',roteirizado=True,previsao_entrega='19:00',
                 status_operacional='pendente')
    db.add_all([entrega,busca]);db.commit()
    return db, empresa, item, entrega, busca

def test_link_geral_vai_para_junior_mesmo_com_fallback_antigo_luiz():
    db,empresa,_,_,_=base()
    assert app._token_responsavel_vitrine(db,empresa)=='junior-token'
    assert app._token_responsavel_vitrine(db,empresa,'luiz-token')=='luiz-token'
    empresa.vitrine_responsavel_configurado=True
    db.commit()
    assert app._token_responsavel_vitrine(db,empresa)=='luiz-token'
    db.close()

def test_outra_empresa_nao_muda_padroes():
    db,empresa,_,_,_=base('vivioke')
    assert app._token_responsavel_vitrine(db,empresa)=='luiz-token'
    db.close()

def test_retirada_19_para_20_sem_mudar_contrato_e_entrega():
    db,empresa,item,entrega,busca=base()
    req=SimpleNamespace(session={'usuario_nome':'Junior'})
    resp=app.atualizar_retirada_obrigatoria_reserva(item.id,req,retirada_hora='20:00',db=db,empresa=empresa)
    assert resp.status_code==303
    assert item.retirada_hora == time(20)
    assert item.hora_fim == time(16)
    assert item.valor == 550
    assert item.status == 'reserva_confirmada'
    assert entrega.hora_inicio == time(11)
    assert busca.hora_inicio == time(20)
    assert busca.previsao_entrega == '20:00'
    assert '19:00' in busca.observacoes_operacionais and '20:00' in busca.observacoes_operacionais
    db.close()

def test_retirada_nao_pode_antes_fim_nem_depois_limite_ou_concluida():
    db,empresa,item,entrega,busca=base()
    req=SimpleNamespace(session={})
    for hora in ('15:00','22:30','inválido'):
        resp=app.atualizar_retirada_obrigatoria_reserva(item.id,req,retirada_hora=hora,db=db,empresa=empresa)
        assert resp.status_code==303 and 'erro=' in resp.headers['location']
        assert item.retirada_hora==time(19) and busca.hora_inicio==time(19)
    busca.status_operacional='concluido';db.commit()
    resp=app.atualizar_retirada_obrigatoria_reserva(item.id,req,retirada_hora='20:00',db=db,empresa=empresa)
    assert resp.status_code==303 and item.retirada_hora==time(19)
    db.close()

def test_corrigir_responsavel_retorna_whatsapp_para_junior_sem_trocar_pagamento():
    db,empresa,item,entrega,busca=base()
    real=app.usuario_empresa_atual
    app.usuario_empresa_atual=lambda db,emp,req: ('admin', None)
    try:
        resp=app.atualizar_responsavel_contrato(item.id, SimpleNamespace(session={}),responsavel_token='junior-token',db=db,empresa=empresa)
    finally:
        app.usuario_empresa_atual=real
    assert resp.status_code==303
    assert item.responsavel_contrato=='Júnior'
    assert item.responsavel_contrato_telefone=='5521933334444'
    assert item.valor==550
    db.close()

def test_templates_e_migracao():
    rotas={r.path for r in app.app.routes}
    assert '/painel/solicitacao/{solicitacao_id}/retirada-obrigatoria' in rotas
    assert '/painel/solicitacao/{solicitacao_id}/responsavel-contrato' in rotas
    for nome in ('admin/contrato_novo.html','admin/solicitacao_detalhe.html','admin/solicitacao_editar.html','admin/vitrine.html'):
        assert app.templates.get_template(nome)

if __name__ == '__main__':
    for nome,func in sorted(globals().copy().items()):
        if nome.startswith('test_') and callable(func):
            func();print('OK',nome)
