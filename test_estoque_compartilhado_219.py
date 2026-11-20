"""Regressões: modelos com componentes compartilhados, produtos principais e datas."""
from datetime import date, timedelta, time
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import Base
from models import Empresa, ProdutoServico, ProdutoServicoRecurso, ItemProdutoServicoEstoque, Solicitacao, ReservaItem, Cliente
import app


def test_jbl_compartilhada_entre_portatil_e_pro_plus():
    engine=create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        emp=Empresa(nome='Aluguel',slug='locacao',modulo_recursos_ativo=True,exigir_recurso_principal=True)
        db.add(emp); db.flush()
        port=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='Portátil',tipo='principal',quantidade_estoque=4,ativo=True)
        jbl=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='Caixa JBL',tipo='principal',quantidade_estoque=4,ativo=True)
        iphone=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='iPhone',tipo='principal',quantidade_estoque=1,ativo=True)
        comum=ProdutoServico(empresa_id=emp.id,nome='Portátil com JBL',quantidade_disponivel=4,ativo=True,vitrine_ativo=True)
        pro=ProdutoServico(empresa_id=emp.id,nome='Pro Plus',quantidade_disponivel=3,ativo=True,vitrine_ativo=True)
        so_iphone=ProdutoServico(empresa_id=emp.id,nome='iPhone simples',quantidade_disponivel=1,ativo=True,vitrine_ativo=True)
        db.add_all([port,jbl,iphone,comum,pro,so_iphone]);db.flush()
        db.add_all([
            ProdutoServicoRecurso(empresa_id=emp.id,produto_id=comum.id,item_estoque_id=port.id,quantidade_por_unidade=1),
            ProdutoServicoRecurso(empresa_id=emp.id,produto_id=comum.id,item_estoque_id=jbl.id,quantidade_por_unidade=1),
            ProdutoServicoRecurso(empresa_id=emp.id,produto_id=pro.id,item_estoque_id=port.id,quantidade_por_unidade=1),
            ProdutoServicoRecurso(empresa_id=emp.id,produto_id=pro.id,item_estoque_id=jbl.id,quantidade_por_unidade=2),
            ProdutoServicoRecurso(empresa_id=emp.id,produto_id=pro.id,item_estoque_id=iphone.id,quantidade_por_unidade=1),
            ProdutoServicoRecurso(empresa_id=emp.id,produto_id=so_iphone.id,item_estoque_id=iphone.id,quantidade_por_unidade=1),
        ])
        cliente=Cliente(empresa_id=emp.id,nome='Teste',identificador='t219');db.add(cliente);db.flush()
        dia=date.today()+timedelta(days=2)
        pedido=Solicitacao(empresa_id=emp.id,cliente_id=cliente.id,data_evento=dia,hora_inicio=time(18),status='aceito',retirada_data=dia+timedelta(days=1))
        db.add(pedido);db.flush()
        db.add(ReservaItem(empresa_id=emp.id,solicitacao_id=pedido.id,produto_id=comum.id,quantidade=3,nome='Portátil com JBL'))
        db.commit()
        def disp(data):
            return {r['produto'].nome:r['disponiveis'] for r in app._itens_vitrine_publica(db,emp,data,apenas_disponibilidade=True)}
        hoje=disp(dia)
        assert hoje['Portátil com JBL']==1
        assert hoje['Pro Plus']==0, 'Pro Plus exigiria mais 2 JBLs quando só resta 1'
        assert hoje['iPhone simples']==1
        assert disp(dia+timedelta(days=1))['Pro Plus']>=1, 'Na retirada os recursos já estão livres'
        # Agora o iPhone simples é alugado e o Pro Plus também perde disponibilidade.
        outro=Solicitacao(empresa_id=emp.id,cliente_id=cliente.id,data_evento=dia,hora_inicio=time(18),status='aceito')
        db.add(outro);db.flush()
        db.add(ReservaItem(empresa_id=emp.id,solicitacao_id=outro.id,produto_id=so_iphone.id,quantidade=1,nome='iPhone'))
        db.commit()
        saldo=disp(dia)
        assert saldo['Pro Plus']==0
        assert saldo['iPhone simples']==0
        assert app._comprometimento_recursos_data(db,emp.id,dia)[jbl.id]==3
        assert app._produtos_sem_principal(db,emp.id)==[]
    engine.dispose()


def test_produto_publico_sem_principal_bloqueado_somente_apos_ativacao():
    engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(engine)
    with Session(engine) as db:
        emp=Empresa(nome='Teste2',slug='teste-219',modulo_recursos_ativo=True,exigir_recurso_principal=False)
        db.add(emp);db.flush()
        produto=ProdutoServico(empresa_id=emp.id,nome='Sem vínculo',quantidade_disponivel=3,ativo=True,vitrine_ativo=True)
        db.add(produto);db.commit()
        def qtd(): return {r['produto'].id:r['disponiveis'] for r in app._itens_vitrine_publica(db,emp,date.today(),apenas_disponibilidade=True)}[produto.id]
        assert qtd()==3
        assert app._produtos_sem_principal(db,emp.id)==[produto]
        emp.exigir_recurso_principal=True;db.flush()
        assert qtd()==0
    engine.dispose()


def test_tres_jbl_avulsas_permite_um_portatil_jbl_e_bloqueia_plus():
    """Exatamente 3 caixas JBL avulsas, 4 unidades físicas, combo 1x e Plus 2x."""
    engine=create_engine('sqlite:///:memory:'); Base.metadata.create_all(engine)
    with Session(engine) as db:
        emp=Empresa(nome='Teste JBL',slug='jbl219',modulo_recursos_ativo=True)
        db.add(emp); db.flush()
        jbl=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='JBL',tipo='principal',quantidade_estoque=4,ativo=True)
        port=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='Portátil',tipo='principal',quantidade_estoque=5,ativo=True)
        avulsa=ProdutoServico(empresa_id=emp.id,nome='JBL avulsa',quantidade_disponivel=4,ativo=True,vitrine_ativo=True)
        normal=ProdutoServico(empresa_id=emp.id,nome='Portátil com JBL',quantidade_disponivel=5,ativo=True,vitrine_ativo=True,eh_combo=True)
        plus=ProdutoServico(empresa_id=emp.id,nome='Portátil Plus',quantidade_disponivel=5,ativo=True,vitrine_ativo=True,eh_combo=True)
        db.add_all([jbl,port,avulsa,normal,plus]);db.flush()
        for p, comps in [(avulsa,[(jbl,1)]),(normal,[(port,1),(jbl,1)]),(plus,[(port,1),(jbl,2)])]:
            for rec,qtd in comps:
                db.add(ProdutoServicoRecurso(empresa_id=emp.id,produto_id=p.id,item_estoque_id=rec.id,quantidade_por_unidade=qtd))
        cliente=Cliente(empresa_id=emp.id,nome='Teste',identificador='test-jbl'); db.add(cliente);db.flush()
        data=date.today()+timedelta(days=2)
        pedido=Solicitacao(empresa_id=emp.id,cliente_id=cliente.id,data_evento=data,hora_inicio=time(19),status='aceito',retirada_data=data+timedelta(days=1))
        db.add(pedido);db.flush()
        db.add(ReservaItem(empresa_id=emp.id,solicitacao_id=pedido.id,produto_id=avulsa.id,quantidade=3,nome='JBL avulsa'))
        db.commit()
        def consultar():
            return {r['produto'].nome:r['disponiveis'] for r in app._itens_vitrine_publica(db,emp,data,apenas_disponibilidade=True)}
        assert consultar()=={'JBL avulsa':1,'Portátil com JBL':1,'Portátil Plus':0}
        assert app._comprometimento_recursos_data(db,emp.id,data)[jbl.id]==3
        # Não basta esconder Plus na vitrine: o aceite direto precisa ser recusado.
        from fastapi import HTTPException
        tentativa=Solicitacao(empresa_id=emp.id,cliente_id=cliente.id,data_evento=data,hora_inicio=time(19),status='aguardando_aceite')
        db.add(tentativa);db.flush()
        db.add(ReservaItem(empresa_id=emp.id,solicitacao_id=tentativa.id,produto_id=plus.id,quantidade=1,nome='Portátil Plus'))
        db.flush()
        try:
            app._validar_estoque_antes_de_confirmar(db,emp,tentativa)
        except HTTPException as ex:
            assert ex.status_code==409 and 'JBL' in str(ex.detail)
        else:
            assert False,'Não pode confirmar Plus com somente 1 JBL livre'
        tentativa.status='cancelada'
        db.commit()
        # A última JBL também se esgota ao reservar o combo Portátil com JBL.
        pedido2=Solicitacao(empresa_id=emp.id,cliente_id=cliente.id,data_evento=data,hora_inicio=time(19),status='aceito')
        db.add(pedido2);db.flush()
        db.add(ReservaItem(empresa_id=emp.id,solicitacao_id=pedido2.id,produto_id=normal.id,quantidade=1,nome='Portátil com JBL'))
        db.commit()
        assert all(qtd==0 for qtd in consultar().values())
    engine.dispose()


def test_combo_sem_principal_indisponivel_mesmo_sem_protecao_global():
    engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(engine)
    with Session(engine) as db:
        emp=Empresa(nome='Teste combo',slug='combo219',modulo_recursos_ativo=True,exigir_recurso_principal=False)
        db.add(emp);db.flush()
        jbl=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='Caixa JBL',tipo='acessorio',quantidade_estoque=4,ativo=True)
        combo=ProdutoServico(empresa_id=emp.id,nome='Combo sem principal',quantidade_disponivel=8,eh_combo=True,ativo=True,vitrine_ativo=True)
        db.add_all([jbl,combo]);db.flush()
        db.add(ProdutoServicoRecurso(empresa_id=emp.id,produto_id=combo.id,item_estoque_id=jbl.id,quantidade_por_unidade=2))
        db.commit()
        assert app._itens_vitrine_publica(db,emp,date.today(),apenas_disponibilidade=True)[0]['disponiveis']==0
    engine.dispose()


def test_opcional_jbl_dois_contratos_reduz_estoque_combo():
    from models import SolicitacaoOpcional
    engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(engine)
    with Session(engine) as db:
        emp=Empresa(nome='Teste opcionais',slug='op219',modulo_recursos_ativo=True)
        db.add(emp);db.flush()
        jbl=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='JBL',tipo='principal',quantidade_estoque=4,ativo=True)
        port=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='Portátil',tipo='principal',quantidade_estoque=3,ativo=True)
        combo=ProdutoServico(empresa_id=emp.id,nome='Portátil Plus',quantidade_disponivel=3,ativo=True,vitrine_ativo=True,eh_combo=True)
        db.add_all([jbl,port,combo]);db.flush()
        db.add_all([ProdutoServicoRecurso(empresa_id=emp.id,produto_id=combo.id,item_estoque_id=port.id,quantidade_por_unidade=1),ProdutoServicoRecurso(empresa_id=emp.id,produto_id=combo.id,item_estoque_id=jbl.id,quantidade_por_unidade=2)])
        cliente=Cliente(empresa_id=emp.id,nome='Cliente',identificador='oid219');db.add(cliente);db.flush()
        data=date.today()+timedelta(days=1)
        for qtd in (2,1):
            contrato=Solicitacao(empresa_id=emp.id,cliente_id=cliente.id,data_evento=data,hora_inicio=time(18),status='aceito')
            db.add(contrato);db.flush()
            db.add(SolicitacaoOpcional(empresa_id=emp.id,solicitacao_id=contrato.id,item_estoque_id=jbl.id,nome='JBL adicional',quantidade=qtd,valor_unitario=100,valor_total=qtd*100))
        db.commit()
        assert app._comprometimento_recursos_data(db,emp.id,data)[jbl.id]==3
        assert app._itens_vitrine_publica(db,emp,data,apenas_disponibilidade=True)[0]['disponiveis']==0
    engine.dispose()
