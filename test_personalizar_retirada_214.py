"""Regressões de horário no aceite já realizado e no catálogo de opcionais."""
from datetime import date, time
from types import SimpleNamespace
import asyncio
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import FormData
from database import Base
from models import Agenda, Empresa, Cliente, Contrato, ProdutoServico, ReservaItem, Solicitacao, HistoricoOpcionalContrato
import app


def _contrato_db(mesmo_dia=False, data_evento=date(2026, 11, 28),
                  frete=38.34, total=338.34, cortesia=True):
    eng = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    db = sessionmaker(bind=eng)()
    empresa = Empresa(nome='Teste', slug='teste', retirada_cortesia_proximo_dia=True,
                      hora_extra_primeira_valor=100, hora_extra_demais_valor=50,
                      retirada_hora_maxima='22:00')
    db.add(empresa); db.flush()
    cli = Cliente(empresa_id=empresa.id, nome='Cliente teste', identificador='5511999999999', telefone='5511999999999')
    contrato = Contrato(empresa_id=empresa.id, nome='Contrato teste', clausulas='Teste')
    produto = ProdutoServico(empresa_id=empresa.id, nome='Karaokê', ativo=True)
    db.add_all([cli, contrato, produto]); db.flush()
    item = Solicitacao(empresa_id=empresa.id, cliente_id=cli.id, contrato_id=contrato.id,
                       produto_id=produto.id, status='reserva_confirmada', public_token='token_teste_214',
                       data_evento=data_evento, hora_inicio=time(15,0), hora_fim=time(20,0),
                       duracao_contratada_minutos=300, retirada_obrigatoria=mesmo_dia,
                       retirada_data=data_evento if mesmo_dia else None,
                       retirada_hora=time(20,0) if mesmo_dia else None,
                       cortesia_retirada=cortesia,
                       horas_adicionais=0, valor_horas_adicionais=0,
                       valor_equipamentos=300, valor_frete=frete, valor_desconto=0, valor=total)
    db.add(item); db.flush()
    db.add(ReservaItem(empresa_id=empresa.id, solicitacao_id=item.id, produto_id=produto.id,
                       nome=produto.nome, quantidade=1, valor_total=300, valor_unitario=300))
    db.commit()
    return db, empresa, item


def test_primeira_hora_sem_alterar_frete_e_com_busca_na_agenda(monkeypatch):
    db, emp, item = _contrato_db()
    monkeypatch.setattr(app, '_infinitepay_habilitada', lambda empresa: False)
    resultado = app.personalizar_horario_solicitacao(item.id, SimpleNamespace(session={'usuario_nome':'Teste'}),
                                                    '1', 1, db, emp)
    assert resultado.status_code == 303
    db.refresh(item)
    assert item.valor == 438.34
    assert item.valor_equipamentos == 300
    assert item.valor_frete == 38.34
    assert item.valor_horas_adicionais == 100
    assert item.horas_adicionais == 1
    assert item.hora_fim == time(21, 0)
    assert item.retirada_obrigatoria and item.retirada_hora == time(21, 0)
    assert item.opcionais_reenvio_pendente
    retirada = db.query(Agenda).filter_by(solicitacao_id=item.id, tipo_evento='retirada').first()
    assert retirada and retirada.hora_inicio == time(21,0) and retirada.data == item.data_evento
    assert db.query(HistoricoOpcionalContrato).filter_by(solicitacao_id=item.id).count() == 1
    db.close()


def test_retorno_para_cortesia_preserva_frete_e_card_de_busca(monkeypatch):
    db, emp, item = _contrato_db()
    monkeypatch.setattr(app, '_infinitepay_habilitada', lambda empresa: False)
    req = SimpleNamespace(session={})
    app.personalizar_horario_solicitacao(item.id, req, '1', 1, db, emp)
    busca = db.query(Agenda).filter_by(solicitacao_id=item.id, tipo_evento='retirada').one()
    busca_id = busca.id
    app.personalizar_horario_solicitacao(item.id, req, None, 0, db, emp)
    db.refresh(item)
    assert item.valor == 338.34
    assert item.valor_frete == 38.34
    assert item.cortesia_retirada and not item.retirada_obrigatoria
    busca = db.query(Agenda).filter_by(solicitacao_id=item.id, tipo_evento='retirada').one()
    assert busca.id == busca_id and busca.data == item.data_evento.replace(day=29)
    db.close()


def test_limite_22h_e_periodo_multidias():
    db, emp, item = _contrato_db()
    with pytest.raises(ValueError, match='22:00'):
        app._projetar_retirada_apos_aceite(db,emp,item,True,3)
    item.retirada_obrigatoria = True
    item.retirada_data = date(2026,11,30)
    with pytest.raises(ValueError,match='outra data'):
        app._projetar_retirada_apos_aceite(db,emp,item,True,1)
    db.close()


def test_impede_edicao_de_retirada_concluida(monkeypatch):
    db, emp, item = _contrato_db()
    monkeypatch.setattr(app, '_infinitepay_habilitada', lambda empresa: False)
    db.add(Agenda(empresa_id=emp.id, solicitacao_id=item.id, tipo_evento='retirada',
                  status_operacional='concluido', data=item.data_evento,
                  hora_inicio=time(20), titulo='Busca concluída'))
    db.commit()
    resultado = app.personalizar_horario_solicitacao(item.id, SimpleNamespace(session={}), '1', 1, db, emp)
    assert 'conclu' in resultado.headers['location']
    db.refresh(item)
    assert item.valor == 338.34
    db.close()


def test_edicao_no_link_publico_sem_opcionais_adicionados(monkeypatch):
    db, emp, item = _contrato_db()
    original = app._empresa_modulo_ativo
    monkeypatch.setattr(app, '_empresa_modulo_ativo', lambda empresa, modulo: True if modulo=='opcionais' else False)
    monkeypatch.setattr(app, '_infinitepay_habilitada', lambda empresa: False)
    class Request:
        async def form(self):
            return FormData([('alterar_retirada','1'), ('retirada_mesmo_dia','1'), ('horas_adicionais','1')])
    result = asyncio.run(app.salvar_opcionais_cliente(emp.slug,item.public_token, Request(), db))
    assert result.status_code == 303 and 'salvo=1' in result.headers['location']
    db.refresh(item)
    assert item.valor == 438.34 and item.valor_frete == 38.34
    assert item.horas_adicionais == 1
    db.close()


def test_painel_e_catalogo_oferecem_edicao():
    from pathlib import Path
    painel = Path('templates/admin/solicitacao_detalhe.html').read_text()
    catalogo = Path('templates/publico/opcionais_contrato.html').read_text()
    assert '/personalizar-horario' in painel
    assert 'name="alterar_retirada"' in catalogo
    assert 'name="horas_adicionais"' in catalogo
    assert 'data-primeira=' in painel and 'data-primeira=' in catalogo


def test_cliente_soma_tv_e_hora_sem_recalcular_frete(monkeypatch):
    from models import OpcionalEmpresa
    db, emp, item = _contrato_db()
    opcional = OpcionalEmpresa(empresa_id=emp.id, nome='TV adicional', valor=80, quantidade=1, ativo=True)
    db.add(opcional); db.commit()
    monkeypatch.setattr(app, '_empresa_modulo_ativo', lambda empresa, modulo: True if modulo=='opcionais' else False)
    monkeypatch.setattr(app, '_infinitepay_habilitada', lambda empresa: False)
    class Request:
        async def form(self):
            return FormData([('alterar_retirada','1'), ('retirada_mesmo_dia','1'),
                             ('horas_adicionais','2'), ('opcional_id',str(opcional.id))])
    resposta=asyncio.run(app.salvar_opcionais_cliente(emp.slug,item.public_token,Request(),db))
    assert resposta.status_code == 303
    db.refresh(item)
    assert round(item.valor,2) == 568.34  # R$ 300 + 80 + 150 + 38,34
    assert item.valor_equipamentos == 380
    assert item.valor_frete == 38.34
    assert item.horas_adicionais == 2 and item.valor_horas_adicionais == 150
    assert item.retirada_hora == time(22,0)
    assert len(item.opcionais_contrato) == 1
    resposta=asyncio.run(app.salvar_opcionais_cliente(emp.slug,item.public_token,Request(),db))
    db.refresh(item)
    assert item.valor == 568.34  # repeated POST is idempotent
    assert db.query(HistoricoOpcionalContrato).filter_by(solicitacao_id=item.id).count() == 1
    db.close()


def test_opcional_sozinho_nao_altera_hora_manual_de_retirada(monkeypatch):
    from models import OpcionalEmpresa
    db,emp,item=_contrato_db(mesmo_dia=True,cortesia=False)
    item.retirada_hora=time(21,30)  # Atendimento agendou 1h30 após o término.
    opcional=OpcionalEmpresa(empresa_id=emp.id,nome='TV',valor=80,quantidade=1,ativo=True)
    db.add(opcional);db.commit()
    monkeypatch.setattr(app, '_empresa_modulo_ativo', lambda empresa,modulo: True if modulo=='opcionais' else False)
    monkeypatch.setattr(app, '_infinitepay_habilitada',lambda empresa:False)
    class Request:
        async def form(self):
            return FormData([('alterar_retirada','1'), ('retirada_mesmo_dia','1'),
                             ('horas_adicionais','0'),('opcional_id',str(opcional.id))])
    asyncio.run(app.salvar_opcionais_cliente(emp.slug,item.public_token,Request(),db))
    db.refresh(item)
    assert item.retirada_hora == time(21,30)
    assert item.valor == 418.34 and item.valor_frete == 38.34
    db.close()
