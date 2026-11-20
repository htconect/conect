"""Novo modelo: combo utiliza só 1 unidade do ProdutoServico principal + seus próprios recursos."""
from datetime import date,timedelta,time
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import Base
from models import Empresa, ProdutoServico, ProdutoServicoRecurso, ItemProdutoServicoEstoque, Solicitacao, ReservaItem, Cliente, SolicitacaoOpcional
import app


def _setup():
    engine=create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine


def _reservar(db, empresa, cliente, produto, qtd, dia, status='aceito'):
    pedido=Solicitacao(empresa_id=empresa.id,cliente_id=cliente.id,data_evento=dia,hora_inicio=time(19),status=status,retirada_data=dia+timedelta(days=1))
    db.add(pedido);db.flush()
    db.add(ReservaItem(empresa_id=empresa.id,solicitacao_id=pedido.id,produto_id=produto.id,quantidade=qtd,nome=produto.nome))
    db.flush()
    return pedido


def _consulta(db,empresa,dia):
    return {linha['produto'].nome: linha['disponiveis'] for linha in app._itens_vitrine_publica(db,empresa,dia,apenas_disponibilidade=True)}


def test_jukebox_pro_compartilha_quatro_jukebox_sem_herdar_opcionais_da_jukebox():
    engine=_setup()
    with Session(engine) as db:
        emp=Empresa(nome='Jukebox',slug='jbx221',modulo_recursos_ativo=True)
        db.add(emp);db.flush()
        jbl=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='JBL',quantidade_estoque=8,ativo=True)
        microfone=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='Microfone',quantidade_estoque=0,ativo=True)
        principal=ProdutoServico(empresa_id=emp.id,nome='Jukebox',quantidade_disponivel=4,ativo=True,vitrine_ativo=True)
        combo=ProdutoServico(empresa_id=emp.id,nome='Jukebox Pro',eh_combo=True,produto_principal_id=None,quantidade_disponivel=0,ativo=True,vitrine_ativo=True)
        db.add_all([jbl,microfone,principal,combo]);db.flush()
        combo.produto_principal_id=principal.id
        db.add_all([
            ProdutoServicoRecurso(empresa_id=emp.id,produto_id=principal.id,item_estoque_id=microfone.id,quantidade_por_unidade=1),
            ProdutoServicoRecurso(empresa_id=emp.id,produto_id=combo.id,item_estoque_id=jbl.id,quantidade_por_unidade=2),
        ])
        cliente=Cliente(empresa_id=emp.id,nome='Cliente',identificador='cliente221');db.add(cliente);db.flush()
        dia=date.today()+timedelta(days=8)
        assert _consulta(db,emp,dia)=={'Jukebox':0,'Jukebox Pro':4}, 'Pro não herda microfone zerado do Jukebox'
        _reservar(db,emp,cliente,combo,1,dia);db.commit()
        assert _consulta(db,emp,dia)=={'Jukebox':0,'Jukebox Pro':3}
        assert app._comprometimento_recursos_data(db,emp.id,dia).get(jbl.id)==2
        assert app._comprometimento_recursos_data(db,emp.id,dia).get(microfone.id,0)==0
    engine.dispose()


def test_tres_jbl_alugadas_permite_combo_uma_jbl_mas_bloqueia_duas():
    engine=_setup()
    with Session(engine) as db:
        emp=Empresa(nome='Teste',slug='t221',modulo_recursos_ativo=True);db.add(emp);db.flush()
        jbl=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='JBL',quantidade_estoque=4,ativo=True)
        portatil=ProdutoServico(empresa_id=emp.id,nome='Portátil',quantidade_disponivel=5,ativo=True,vitrine_ativo=True)
        jbl_avulsa=ProdutoServico(empresa_id=emp.id,nome='JBL avulsa',quantidade_disponivel=4,ativo=True,vitrine_ativo=True)
        combo=ProdutoServico(empresa_id=emp.id,nome='Portátil com JBL',eh_combo=True,quantidade_disponivel=0,ativo=True,vitrine_ativo=True)
        plus=ProdutoServico(empresa_id=emp.id,nome='Portátil Plus',eh_combo=True,quantidade_disponivel=0,ativo=True,vitrine_ativo=True)
        db.add_all([jbl,portatil,jbl_avulsa,combo,plus]);db.flush()
        combo.produto_principal_id=portatil.id;plus.produto_principal_id=portatil.id
        for prod,quant in ((jbl_avulsa,1),(combo,1),(plus,2)):
            db.add(ProdutoServicoRecurso(empresa_id=emp.id,produto_id=prod.id,item_estoque_id=jbl.id,quantidade_por_unidade=quant))
        cliente=Cliente(empresa_id=emp.id,nome='Cliente',identificador='cli221');db.add(cliente);db.flush()
        dia=date.today()+timedelta(days=5)
        _reservar(db,emp,cliente,jbl_avulsa,3,dia);db.commit()
        assert _consulta(db,emp,dia)=={'JBL avulsa':1,'Portátil':5,'Portátil com JBL':1,'Portátil Plus':0}
        tentar=_reservar(db,emp,cliente,plus,1,dia,status='aguardando_aceite')
        try:
            app._validar_estoque_antes_de_confirmar(db,emp,tentar)
        except HTTPException as exc:
            assert exc.status_code==409 and 'JBL' in str(exc.detail)
        else:
            assert False,'A confirmação não pode aceitar duas JBL quando só há uma'
    engine.dispose()


def test_quatro_jukebox_uma_pro_e_tres_normais_compartilham_mesmo_limite():
    engine=_setup()
    with Session(engine) as db:
        emp=Empresa(nome='Jukebox',slug='t222',modulo_recursos_ativo=False);db.add(emp);db.flush()
        normal=ProdutoServico(empresa_id=emp.id,nome='Jukebox',quantidade_disponivel=4,ativo=True,vitrine_ativo=True)
        pro=ProdutoServico(empresa_id=emp.id,nome='Jukebox Pro',eh_combo=True,quantidade_disponivel=999,ativo=True,vitrine_ativo=True)
        db.add_all([normal,pro]);db.flush();pro.produto_principal_id=normal.id
        cliente=Cliente(empresa_id=emp.id,nome='Cliente',identificador='t222');db.add(cliente);db.flush()
        dia=date.today()+timedelta(days=6)
        assert _consulta(db,emp,dia)=={'Jukebox':4,'Jukebox Pro':4}
        _reservar(db,emp,cliente,pro,1,dia)
        assert _consulta(db,emp,dia)=={'Jukebox':3,'Jukebox Pro':3}
        _reservar(db,emp,cliente,normal,3,dia)
        assert _consulta(db,emp,dia)=={'Jukebox':0,'Jukebox Pro':0}
        tentativa=_reservar(db,emp,cliente,pro,1,dia,status='aguardando_aceite')
        try:
            app._validar_estoque_antes_de_confirmar(db,emp,tentativa)
        except HTTPException as exc:
            assert exc.status_code==409 and 'Jukebox' in str(exc.detail)
        else:
            assert False,'Não pode alugar quinto Jukebox por combo com módulo de recursos inativo'
        assert _consulta(db,emp,dia+timedelta(days=1))=={'Jukebox':4,'Jukebox Pro':4}
    engine.dispose()


def test_combo_sem_principal_ou_como_pai_outro_combo_fica_indisponivel():
    engine=_setup()
    with Session(engine) as db:
        emp=Empresa(nome='Teste',slug='inval221');db.add(emp);db.flush()
        base=ProdutoServico(empresa_id=emp.id,nome='Base',quantidade_disponivel=4,ativo=True,vitrine_ativo=True)
        filho=ProdutoServico(empresa_id=emp.id,nome='Filho',eh_combo=True,quantidade_disponivel=200,ativo=True,vitrine_ativo=True)
        neto=ProdutoServico(empresa_id=emp.id,nome='Neto',eh_combo=True,quantidade_disponivel=20,ativo=True,vitrine_ativo=True)
        db.add_all([base,filho,neto]);db.flush()
        neto.produto_principal_id=filho.id
        assert _consulta(db,emp,date.today())=={'Base':4,'Filho':0,'Neto':0}
        filho.produto_principal_id=base.id
        assert _consulta(db,emp,date.today())=={'Base':4,'Filho':4,'Neto':0}
    engine.dispose()


def test_addon_opcional_separado_consome_mesmo_estoque_do_combo():
    engine=_setup()
    with Session(engine) as db:
        emp=Empresa(nome='Teste',slug='opts221',modulo_recursos_ativo=True);db.add(emp);db.flush()
        jbl=ItemProdutoServicoEstoque(empresa_id=emp.id,nome='JBL',quantidade_estoque=4,ativo=True)
        portatil=ProdutoServico(empresa_id=emp.id,nome='Portátil',quantidade_disponivel=3,ativo=True,vitrine_ativo=True)
        pro=ProdutoServico(empresa_id=emp.id,nome='Portátil Pro',eh_combo=True,quantidade_disponivel=0,ativo=True,vitrine_ativo=True)
        db.add_all([jbl,portatil,pro]);db.flush();pro.produto_principal_id=portatil.id
        db.add(ProdutoServicoRecurso(empresa_id=emp.id,produto_id=pro.id,item_estoque_id=jbl.id,quantidade_por_unidade=2))
        cliente=Cliente(empresa_id=emp.id,nome='Cliente',identificador='opts221');db.add(cliente);db.flush()
        dia=date.today()+timedelta(days=4)
        for q in (2,1):
            pedido=Solicitacao(empresa_id=emp.id,cliente_id=cliente.id,data_evento=dia,hora_inicio=time(19),status='aceito')
            db.add(pedido);db.flush()
            db.add(SolicitacaoOpcional(empresa_id=emp.id,solicitacao_id=pedido.id,item_estoque_id=jbl.id,nome='JBL',quantidade=q,valor_unitario=10,valor_total=10*q))
        db.commit()
        assert _consulta(db,emp,dia)=={'Portátil':3,'Portátil Pro':0}
    engine.dispose()
