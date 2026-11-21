"""Regressões v1.0.222: um combo pode consumir vários ProdutosServico e só seus próprios opcionais."""
from datetime import date, timedelta, time
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import Base
from models import (Empresa, ProdutoServico, ComboProdutoPrincipal, ItemProdutoServicoEstoque,
                    ProdutoServicoRecurso, Solicitacao, ReservaItem, Cliente)
import app


def preparar(recursos=False):
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    db = Session(engine)
    emp = Empresa(nome='KRJ', slug='krj222', modulo_recursos_ativo=recursos)
    cliente = Cliente(empresa_id=1, nome='Cliente Teste', identificador='cli222')
    db.add(emp); db.flush()
    cliente.empresa_id = emp.id
    db.add(cliente); db.flush()
    return engine, db, emp, cliente


def reservar(db, emp, cliente, produto, dia, quantidade=1, status='aceito'):
    sol = Solicitacao(empresa_id=emp.id, cliente_id=cliente.id, data_evento=dia,
                      hora_inicio=time(19), retirada_data=dia+timedelta(days=1), status=status)
    db.add(sol); db.flush()
    db.add(ReservaItem(empresa_id=emp.id, solicitacao_id=sol.id,
                      produto_id=produto.id, nome=produto.nome, quantidade=quantidade))
    db.flush()
    return sol


def disponibilidade(db, emp, dia):
    return {row['produto'].nome: row['disponiveis'] for row in
            app._itens_vitrine_publica(db, emp, dia, apenas_disponibilidade=True)}


def test_combo_tres_principais_esgota_quando_um_esta_alugado():
    engine, db, emp, cli = preparar()
    try:
        portatil = ProdutoServico(empresa_id=emp.id, nome='Portátil', quantidade_disponivel=4, ativo=True, vitrine_ativo=True)
        fliperama = ProdutoServico(empresa_id=emp.id, nome='Fliperama', quantidade_disponivel=2, ativo=True, vitrine_ativo=True)
        dance = ProdutoServico(empresa_id=emp.id, nome='Just Dance', quantidade_disponivel=1, ativo=True, vitrine_ativo=True)
        combo = ProdutoServico(empresa_id=emp.id, nome='Festa Completa', eh_combo=True, quantidade_disponivel=999, ativo=True, vitrine_ativo=True)
        db.add_all([portatil, fliperama, dance, combo]); db.flush()
        for principal in (portatil, fliperama, dance):
            db.add(ComboProdutoPrincipal(empresa_id=emp.id, combo_id=combo.id,
                                         produto_principal_id=principal.id, quantidade_por_combo=1))
        dia=date.today()+timedelta(days=7)
        assert disponibilidade(db, emp, dia)=={
            'Portátil':4, 'Fliperama':2, 'Just Dance':1, 'Festa Completa':1}
        reservar(db, emp, cli, dance, dia)
        db.commit()
        assert disponibilidade(db, emp, dia)=={
            'Portátil':4, 'Fliperama':2, 'Just Dance':0, 'Festa Completa':0}
        tentativa = reservar(db, emp, cli, combo, dia, status='aguardando_aceite')
        try:
            app._validar_estoque_antes_de_confirmar(db, emp, tentativa)
        except HTTPException as exc:
            assert exc.status_code==409
            assert 'Just Dance' in str(exc.detail)
        else:
            assert False, 'Faltou bloquear combo que usa Just Dance já alugado'
    finally:
        db.close(); engine.dispose()


def test_multiplos_principais_consume_jukebox_e_fliperama_e_respeita_qtd():
    engine, db, emp, cli=preparar()
    try:
        jukebox=ProdutoServico(empresa_id=emp.id, nome='Jukebox', quantidade_disponivel=4, ativo=True, vitrine_ativo=True)
        flip=ProdutoServico(empresa_id=emp.id,nome='Fliperama', quantidade_disponivel=3, ativo=True, vitrine_ativo=True)
        combo=ProdutoServico(empresa_id=emp.id,nome='Combo Duplo', eh_combo=True, quantidade_disponivel=0, ativo=True, vitrine_ativo=True)
        db.add_all([jukebox,flip,combo]);db.flush()
        db.add_all([
            ComboProdutoPrincipal(empresa_id=emp.id,combo_id=combo.id,produto_principal_id=jukebox.id,quantidade_por_combo=2),
            ComboProdutoPrincipal(empresa_id=emp.id,combo_id=combo.id,produto_principal_id=flip.id,quantidade_por_combo=1)])
        dia=date.today()+timedelta(days=10)
        assert disponibilidade(db,emp,dia)['Combo Duplo']==2
        reservar(db,emp,cli,combo,dia,1);db.commit()
        assert disponibilidade(db,emp,dia)=={'Jukebox':2,'Fliperama':2,'Combo Duplo':1}
        reservar(db,emp,cli,jukebox,dia,2);db.commit()
        assert disponibilidade(db,emp,dia)['Combo Duplo']==0
        assert disponibilidade(db,emp,dia+timedelta(days=1))['Combo Duplo']==2
    finally:
        db.close();engine.dispose()


def test_combo_consume_apenas_seus_recursos_mais_multiplos_principais():
    engine,db,emp,cli=preparar(True)
    try:
        jbl=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='JBL',quantidade_estoque=4,ativo=True)
        tv=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='TV da Jukebox normal',quantidade_estoque=0,ativo=True)
        juke=ProdutoServico(empresa_id=emp.id,nome='Jukebox',quantidade_disponivel=4,ativo=True,vitrine_ativo=True)
        flip=ProdutoServico(empresa_id=emp.id,nome='Fliperama',quantidade_disponivel=2,ativo=True,vitrine_ativo=True)
        combo=ProdutoServico(empresa_id=emp.id,nome='Jukebox+Fliperama PRO',eh_combo=True,quantidade_disponivel=0,ativo=True,vitrine_ativo=True)
        db.add_all([jbl,tv,juke,flip,combo]);db.flush()
        for p in (juke,flip):
            db.add(ComboProdutoPrincipal(empresa_id=emp.id,combo_id=combo.id,produto_principal_id=p.id,quantidade_por_combo=1))
        db.add(ProdutoServicoRecurso(empresa_id=emp.id,produto_id=juke.id,item_estoque_id=tv.id,quantidade_por_unidade=1))
        db.add(ProdutoServicoRecurso(empresa_id=emp.id,produto_id=combo.id,item_estoque_id=jbl.id,quantidade_por_unidade=2))
        dia=date.today()+timedelta(days=5)
        assert disponibilidade(db,emp,dia)=={'Jukebox':0,'Fliperama':2,'Jukebox+Fliperama PRO':2}
        reservar(db,emp,cli,combo,dia)
        db.commit()
        comp=app._comprometimento_recursos_data(db,emp.id,dia)
        assert comp.get(jbl.id)==2 and comp.get(tv.id,0)==0
        assert disponibilidade(db,emp,dia)['Jukebox+Fliperama PRO']==1
    finally:
        db.close();engine.dispose()


def test_bloqueio_manual_do_principal_nao_bloqueia_combo():
    from models import BloqueioProduto
    engine,db,emp,cli=preparar()
    try:
        a=ProdutoServico(empresa_id=emp.id,nome='Portátil',quantidade_disponivel=2,ativo=True,vitrine_ativo=True)
        b=ProdutoServico(empresa_id=emp.id,nome='Fliperama',quantidade_disponivel=2,ativo=True,vitrine_ativo=True)
        combo=ProdutoServico(empresa_id=emp.id,nome='Portátil com Fliperama',eh_combo=True,ativo=True,vitrine_ativo=True)
        db.add_all([a,b,combo]);db.flush()
        for x in (a,b):
            db.add(ComboProdutoPrincipal(empresa_id=emp.id,combo_id=combo.id,produto_principal_id=x.id,quantidade_por_combo=1))
        dia=date.today()+timedelta(days=3)
        db.add(BloqueioProduto(empresa_id=emp.id, produto_id=b.id, data_inicio=dia, data_fim=dia, ativo=True))
        db.flush()
        assert disponibilidade(db,emp,dia)=={'Portátil':2,'Fliperama':0,'Portátil com Fliperama':2}
    finally:
        db.close();engine.dispose()


def test_mapa_componentes_nao_mistura_empresas_e_nao_herda_principais():
    engine,db,emp,cli=preparar()
    try:
        p=ProdutoServico(empresa_id=emp.id,nome='Principal',quantidade_disponivel=3,ativo=True)
        combo=ProdutoServico(empresa_id=emp.id,nome='Combo',eh_combo=True,ativo=True)
        outra=Empresa(nome='Outra',slug='outra222')
        db.add_all([p,combo,outra]);db.flush()
        externo=ProdutoServico(empresa_id=outra.id,nome='Externo',quantidade_disponivel=100,ativo=True)
        db.add(externo);db.flush()
        db.add(ComboProdutoPrincipal(empresa_id=emp.id,combo_id=combo.id,produto_principal_id=externo.id,quantidade_por_combo=1))
        produtos,comp=app._produtos_principais_e_raizes(db,emp.id)
        assert comp[combo.id]=={}
    finally:
        db.close();engine.dispose()


def test_operacao_exibe_tres_componentes_e_reserva_passando_pelo_dia_25():
    engine,db,emp,cli=preparar()
    try:
        a=ProdutoServico(empresa_id=emp.id,nome='Portátil',quantidade_disponivel=4,ativo=True)
        b=ProdutoServico(empresa_id=emp.id,nome='Fliperama',quantidade_disponivel=2,ativo=True)
        c=ProdutoServico(empresa_id=emp.id,nome='Just Dance',quantidade_disponivel=1,ativo=True)
        combo=ProdutoServico(empresa_id=emp.id,nome='Combo Festa',eh_combo=True,ativo=True)
        db.add_all([a,b,c,combo]);db.flush()
        for p in (a,b,c):
            db.add(ComboProdutoPrincipal(empresa_id=emp.id,combo_id=combo.id,produto_principal_id=p.id,quantidade_por_combo=1))
        dia=date(2026,12,24)
        reserva=reservar(db,emp,cli,combo,dia,status='aceito')
        reserva.retirada_data=date(2026,12,26)
        # Outro pedido no dia 25 de Just Dance deve encontrar o estoque esgotado.
        avulso=reservar(db,emp,cli,c,date(2026,12,25),status='aguardando_aceite')
        db.commit()
        assert disponibilidade(db,emp,date(2026,12,25))['Just Dance']==0
        diagnostico=app._analise_estoque_solicitacao(db,reserva)
        assert {linha['nome'] for linha in diagnostico['produtos']}=={'Portátil','Fliperama','Just Dance'}
        try:
            app._validar_estoque_antes_de_confirmar(db,emp,avulso)
        except HTTPException as exc:
            assert exc.status_code==409 and 'Just Dance' in str(exc.detail)
        else:
            assert False,'Reserva avulsa em dia intermediário não pode duplicar Just Dance'
    finally:
        db.close();engine.dispose()


def test_recurso_principal_legado_nao_duplica_estoque_produto():
    engine,db,emp,cli=preparar(True)
    try:
        recurso_legado=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='Jukebox duplicada antigo',tipo='principal',quantidade_estoque=0,ativo=True)
        principal=ProdutoServico(empresa_id=emp.id,nome='Jukebox',quantidade_disponivel=4,ativo=True,vitrine_ativo=True)
        combo=ProdutoServico(empresa_id=emp.id,nome='Jukebox Pro',eh_combo=True,ativo=True,vitrine_ativo=True)
        db.add_all([recurso_legado,principal,combo]);db.flush()
        db.add(ComboProdutoPrincipal(empresa_id=emp.id,combo_id=combo.id,produto_principal_id=principal.id,quantidade_por_combo=1))
        db.add(ProdutoServicoRecurso(empresa_id=emp.id,produto_id=combo.id,item_estoque_id=recurso_legado.id,quantidade_por_unidade=1))
        assert disponibilidade(db,emp,date.today())=={'Jukebox':4,'Jukebox Pro':4}
        assert recurso_legado.id not in app._mapa_recursos_produtos(db,emp.id).get(combo.id,{})
    finally:
        db.close();engine.dispose()
