"""Reserva até a véspera da retirada, incluindo recursos/opcionais."""
from datetime import date, time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import Empresa, Cliente, ProdutoServico, Solicitacao, ReservaItem
import app

def test_estoque_periodo():
    engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(engine)
    db=sessionmaker(bind=engine)()
    emp=Empresa(nome='Teste',slug='teste');db.add(emp);db.flush()
    cli=Cliente(empresa_id=emp.id,identificador='1',nome='Cliente')
    pr=ProdutoServico(empresa_id=emp.id,nome='The Voice',ativo=True,quantidade_disponivel=2)
    db.add_all([cli,pr]);db.flush()
    sol=Solicitacao(empresa_id=emp.id,cliente_id=cli.id,data_evento=date(2026,12,24),retirada_data=date(2026,12,26),retirada_obrigatoria=True,hora_inicio=time(18),status='reserva_confirmada')
    db.add(sol);db.flush()
    db.add(ReservaItem(empresa_id=emp.id,solicitacao_id=sol.id,produto_id=pr.id,nome='The Voice',quantidade=1))
    db.commit()
    for data,esperado in [(date(2026,12,23),0),(date(2026,12,24),1),(date(2026,12,25),1),(date(2026,12,26),0)]:
        reservas=app._reservas_ativas_na_data(db,emp.id,data)
        assert len(reservas)==esperado,(data,len(reservas))
    assert app._data_retirada_manual(date(2026,12,24),'2026-12-26')==date(2026,12,26)
    db.close()
if __name__=='__main__':
    test_estoque_periodo();print('OK test_estoque_periodo')
