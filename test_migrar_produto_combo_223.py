"""Regressão 1.0.223: produto existente vira combo sem recadastrar nem perder contratos."""
from datetime import date, timedelta, time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app
from database import Base
from models import (
    Empresa, ProdutoServico, ProdutoFoto, ReservaItem, Cliente, Solicitacao,
    ItemProdutoServicoEstoque, ProdutoServicoRecurso, ComboProdutoPrincipal,
)


def _setup():
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        e = Empresa(nome='Karaoke RJ', slug='krj223', modulo_recursos_ativo=True)
        db.add(e); db.flush()
        principal = ProdutoServico(empresa_id=e.id, nome='Jukebox', quantidade_disponivel=4,
                                   ativo=True, vitrine_ativo=True, valor_base=400)
        antigo = ProdutoServico(empresa_id=e.id, nome='Jukebox Pro', quantidade_disponivel=8,
                                ativo=True, vitrine_ativo=True, valor_base=700,
                                descricao='Descrição já cadastrada')
        db.add_all([principal, antigo]); db.flush()
        foto = ProdutoFoto(empresa_id=e.id, produto_id=antigo.id, arquivo_url='/midia/123',
                           original_url='/midia/123', ordem=1, capa=True)
        jbl = ItemProdutoServicoEstoque(empresa_id=e.id, nome='JBL', quantidade_estoque=4, ativo=True)
        db.add_all([foto, jbl]); db.flush()
        db.add(ProdutoServicoRecurso(empresa_id=e.id, produto_id=antigo.id,
                                    item_estoque_id=jbl.id, quantidade_por_unidade=2))
        cli = Cliente(empresa_id=e.id, nome='Cliente antigo', identificador='cli223')
        db.add(cli); db.flush()
        dia = date.today() + timedelta(days=12)
        contrato = Solicitacao(empresa_id=e.id, cliente_id=cli.id, data_evento=dia,
                               retirada_data=dia + timedelta(days=1), hora_inicio=time(19), status='aceito')
        db.add(contrato); db.flush()
        linha = ReservaItem(empresa_id=e.id, solicitacao_id=contrato.id, produto_id=antigo.id,
                           nome='Jukebox Pro', quantidade=1, valor_unitario=700, valor_total=700)
        db.add(linha)
        ids = (e.id, principal.id, antigo.id, jbl.id, foto.id, contrato.id)
        db.commit()
    return engine, ids, dia


def _client(engine, empresa_id):
    def db_override():
        with Session(engine) as session:
            yield session
    def empresa_override():
        with Session(engine) as session:
            return session.get(Empresa, empresa_id)
    app.app.dependency_overrides[app.get_db] = db_override
    app.app.dependency_overrides[app.empresa_logada] = empresa_override
    return TestClient(app.app, follow_redirects=False)


def test_converter_produto_existente_mantem_id_preco_fotos_e_locacoes():
    engine, (empresa_id, principal_id, pro_id, jbl_id, foto_id, contrato_id), dia = _setup()
    client = _client(engine, empresa_id)
    try:
        resposta = client.get(f'/painel/produto/{pro_id}')
        assert resposta.status_code == 200
        assert 'É combo?' in resposta.text
        assert 'Jukebox' in resposta.text
        assert 'mesmo cadastro, fotos, preços e contratos' in resposta.text

        # Posta os mesmos campos que o navegador gera ao marcar “É combo?” e
        # escolher o principal: não cria um segundo produto nem recadastra JBL.
        resposta = client.post(f'/painel/produto/{pro_id}', data={
            'nome': 'Jukebox Pro', 'descricao': 'Descrição já cadastrada',
            'valor_base': '700,00', 'quantidade_disponivel': '8',
            'vitrine_ativo': '1', 'tipo_cadastro': 'combo',
            'combo_principal_id': str(principal_id),
            'combo_principal_quantidade': '1',
            'recurso_item_id': str(jbl_id), 'recurso_utiliza': '1',
            'recurso_quantidade': '2',
        })
        assert resposta.status_code == 303, resposta.text[:500]
        assert resposta.headers['location'] == f'/painel/produto/{pro_id}?salvo=1'

        with Session(engine) as db:
            prod = db.get(ProdutoServico, pro_id)
            assert prod.eh_combo is True
            assert prod.nome == 'Jukebox Pro'
            assert prod.valor_base == 700
            assert prod.quantidade_disponivel == 8  # metadado original, não estoque combo
            assert db.query(ProdutoServico).filter_by(empresa_id=empresa_id).count() == 2
            assert db.get(ProdutoFoto, foto_id).produto_id == pro_id
            assert db.query(ReservaItem).filter_by(produto_id=pro_id).count() == 1
            assert db.query(ReservaItem).filter_by(solicitacao_id=contrato_id).one().valor_total == 700
            vinculo = db.query(ComboProdutoPrincipal).filter_by(combo_id=pro_id).one()
            assert vinculo.produto_principal_id == principal_id and vinculo.quantidade_por_combo == 1
            recurso = db.query(ProdutoServicoRecurso).filter_by(produto_id=pro_id).one()
            assert recurso.item_estoque_id == jbl_id and recurso.quantidade_por_unidade == 2
            empresa = db.get(Empresa, empresa_id)
            disp = {r['produto'].nome: r['disponiveis'] for r in
                    app._itens_vitrine_publica(db, empresa, dia, apenas_disponibilidade=True)}
            # O aluguel existente de Pro passa a consumir 1 Jukebox e 2 JBL.
            assert disp == {'Jukebox': 3, 'Jukebox Pro': 1}

        lista = client.get('/painel/produtos')
        assert lista.status_code == 200
        assert 'Jukebox Pro' in lista.text
        assert 'Combo · estoque dos principais' in lista.text
    finally:
        app.app.dependency_overrides.clear()
        client.close()
        engine.dispose()


def test_principal_em_uso_por_outro_combo_nao_pode_ser_convertido():
    engine, (empresa_id, principal_id, pro_id, jbl_id, foto_id, contrato_id), dia = _setup()
    client = _client(engine, empresa_id)
    try:
        with Session(engine) as db:
            prod = db.get(ProdutoServico, pro_id)
            prod.eh_combo = True
            db.add(ComboProdutoPrincipal(empresa_id=empresa_id, combo_id=pro_id,
                                         produto_principal_id=principal_id, quantidade_por_combo=1))
            db.commit()
        resposta=client.post(f'/painel/produto/{principal_id}', data={
            'nome':'Jukebox', 'valor_base':'400', 'eh_combo':'true',
            'combo_principal_id':str(pro_id), 'combo_principal_quantidade':'1'
        })
        # Outro combo não é principal válido (evita composicoes cíclicas).
        assert resposta.status_code == 422
        with Session(engine) as db:
            assert db.get(ProdutoServico, principal_id).eh_combo is False
    finally:
        app.app.dependency_overrides.clear()
        client.close()
        engine.dispose()


def test_telas_de_migracao_e_menu_comboficam_disponiveis():
    root = Path(__file__).parent
    produtos=(root/'templates/admin/produtos.html').read_text()
    formulario=(root/'templates/admin/produto_form.html').read_text()
    combos=(root/'templates/admin/combos.html').read_text()
    assert '/painel/produto/{{ p.id }}#tipo-cadastro' in produtos
    assert 'secao?.closest(\'details\')' in formulario
    assert 'name="tipo_cadastro"' in formulario
    assert 'combo_principal_id' in formulario
    assert 'Adicionar produto principal' in formulario
    assert 'href="/painel/combos"' not in produtos
    assert '1.0.224' in (root/'config.py').read_text()
    assert 'tipo_cadastro VARCHAR(20)' in (root/'app.py').read_text()
    assert 'CREATE TABLE IF NOT EXISTS combo_produtos_principais' in (root/'app.py').read_text()


def test_opcional_avulso_usa_jbl_que_combo_ja_consume_sem_estoque_duplo():
    engine, (empresa_id, principal_id, pro_id, jbl_id, _foto_id, _cid), dia = _setup()
    client = _client(engine, empresa_id)
    try:
        # O Pro já tem contrato futuro e 2 JBLs; converter o próprio item em combo.
        post=client.post(f'/painel/produto/{pro_id}',data={
            'nome':'Jukebox Pro', 'valor_base':'700', 'tipo_cadastro':'combo',
            'combo_principal_id':str(principal_id), 'combo_principal_quantidade':'1',
            'recurso_item_id':str(jbl_id), 'recurso_utiliza':'1', 'recurso_quantidade':'2',
            'vitrine_ativo':'1',
        })
        assert post.status_code == 303, post.text
        # JBL avulsa usa o mesmo recurso físico e NÃO recebe estoque de produto.
        post=client.post('/painel/produtos',data={
            'nome':'Aluguel JBL avulsa','valor_base':'80','quantidade_disponivel':'100',
            'tipo_cadastro':'opcional', 'recurso_item_id':str(jbl_id),
            'recurso_utiliza':'1', 'recurso_quantidade':'1', 'vitrine_ativo':'1',
        })
        assert post.status_code==303,post.text
        with Session(engine) as db:
            opc=db.query(ProdutoServico).filter_by(nome='Aluguel JBL avulsa').one()
            assert opc.tipo_cadastro == 'opcional' and not opc.eh_combo
            assert opc.quantidade_disponivel == 0  # SEM estoque próprio
            assert db.query(ItemProdutoServicoEstoque).filter_by(nome='JBL').count()==1
            e=db.get(Empresa,empresa_id)
            dados={r['produto'].nome:r['disponiveis'] for r in
                   app._itens_vitrine_publica(db,e,dia,apenas_disponibilidade=True)}
            assert dados['Aluguel JBL avulsa']==2  # 4 JBL - 2 do Pro já alugado
            api=client.get(f'/api/estoque/produto/{opc.id}', params={'data':dia.isoformat()})
            assert api.status_code==200
            assert api.json()['total_produto']==4  # não mostra estoque fictício no painel
            assert api.json()['disponiveis']==2
            assert dados['Jukebox']==3
            assert dados['Jukebox Pro']==1
            # Alugando as duas JBL restantes como produto avulso, Pro passa a 0.
            cliente=db.query(Cliente).first()
            nova=Solicitacao(empresa_id=empresa_id,cliente_id=cliente.id,data_evento=dia,
                             retirada_data=dia+timedelta(days=1),hora_inicio=time(19),status='aceito')
            db.add(nova); db.flush()
            db.add(ReservaItem(empresa_id=empresa_id,solicitacao_id=nova.id,
                               produto_id=opc.id,nome=opc.nome,quantidade=2,
                               valor_unitario=80,valor_total=160))
            db.commit()
            dados={r['produto'].nome:r['disponiveis'] for r in
                   app._itens_vitrine_publica(db,e,dia,apenas_disponibilidade=True)}
            assert dados['Aluguel JBL avulsa']==0
            assert dados['Jukebox Pro']==0
            assert dados['Jukebox']==3
    finally:
        app.app.dependency_overrides.clear();client.close();engine.dispose()


def test_combos_multiplos_principais_e_menu_unico_sem_estoque_proprio():
    engine, (empresa_id, principal_id, pro_id, jbl_id, _foto_id, _cid), dia=_setup()
    client=_client(engine,empresa_id)
    try:
        pagina=client.get(f'/painel/produto/{pro_id}')
        assert pagina.status_code==200
        assert 'Qual o produto principal?' in pagina.text
        assert '+ Adicionar produto principal' in pagina.text
        assert 'value="opcional"' in pagina.text
        assert 'Categoria da vitrine' in pagina.text
        pagina=client.get('/painel/produtos')
        assert pagina.status_code==200
        assert 'href="/painel/combos"' not in pagina.text
        pagina=client.get('/painel/combos')
        assert pagina.status_code==303
        assert pagina.headers['location']=='/painel/produtos'
        # Mesmo com quantidade antiga de 8, estoque do Pro deve depender só do Jukebox.
        r=client.post(f'/painel/produto/{pro_id}',data={
            'nome':'Jukebox Pro','valor_base':'700','tipo_cadastro':'combo',
            'combo_principal_id':str(principal_id),'combo_principal_quantidade':'1',
            'recurso_item_id':str(jbl_id),'recurso_utiliza':'1','recurso_quantidade':'2',
        })
        assert r.status_code==303
        with Session(engine) as db:
            prod=db.get(ProdutoServico,pro_id)
            assert prod.tipo_cadastro=='combo' and prod.eh_combo
            assert prod.quantidade_disponivel==8  # legado mantido, ignorado no cálculo
            assert db.query(ProdutoServico).filter_by(empresa_id=empresa_id).count()==2
    finally:
        app.app.dependency_overrides.clear();client.close();engine.dispose()
