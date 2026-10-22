"""Testes de atribuição individual no Connect 1.0.167 (sem rede ou banco real)."""
from datetime import date, time, timedelta
from types import SimpleNamespace
from pathlib import Path
from urllib.parse import parse_qs, urlparse


import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request
from fastapi import HTTPException

import app
from database import Base
from models import Empresa, UsuarioEmpresa, Cliente, Solicitacao


def fixture_db():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    empresa = Empresa(
        slug='karaokerj', nome='Karaokê RJ', usuario_admin='admin', ativa=True,
        vitrine_ativa=True, whatsapp_retorno='21911110000',
        pre_contrato_token='cc'*10, pre_contrato_responsavel_nome='Administrador',
        pre_contrato_responsavel_telefone='21999990000',
        vitrine_responsavel_token='bb'*10, vitrine_responsavel_configurado=True,
    )
    db.add(empresa)
    db.flush()
    junior = UsuarioEmpresa(empresa_id=empresa.id, nome='Junior',usuario='junior',senha='teste',
                           ativo=True, telefone='21933334444', pre_contrato_token='aa'*10)
    luiz = UsuarioEmpresa(empresa_id=empresa.id, nome='Luiz',usuario='luiz',senha='teste',
                         ativo=True,telefone='21922223333',pre_contrato_token='bb'*10)
    db.add_all([junior,luiz]);db.commit()
    return db, empresa, junior, luiz


def request_for(path='/', usuario=None):
    scope={'type':'http', 'method':'GET', 'scheme':'https',
           'path':path,'root_path':'','query_string':b'',
           'headers':[(b'host',b'conect.humiat.com.br')],
           'server':('conect.humiat.com.br',443), 'client':('127.0.0.1',12345),
           'session':{'usuario_sistema':usuario} if usuario else {}}
    return Request(scope)


def test_geral_nunca_seleciona_junior_luiz_ou_admin():
    db,empresa,junior,luiz=fixture_db()
    assert app._token_responsavel_vitrine(db,empresa)==''
    assert app._resolver_responsavel_link_vitrine(db,empresa)==''
    assert app._token_responsavel_vitrine(db,empresa,luiz.pre_contrato_token)==luiz.pre_contrato_token
    # Continua genérico mesmo com legado vitrine_responsavel_configurado=True.
    resposta=app.portal_empresa('karaokerj',request_for('/e/karaokerj'),db=db)
    assert resposta.context['responsavel_vitrine_token']==''
    db.close()


def test_link_curto_de_cada_usuario_eh_estavel_e_individual():
    db,empresa,junior,luiz=fixture_db()
    links=[]
    for usuario in (junior,luiz):
        url, compartilhar = app._vitrine_link_do_usuario(request_for('/painel/vitrine', usuario=usuario.usuario),db,empresa)
        assert url.endswith('?u='+usuario.pre_contrato_token[:8])
        assert '219' not in url  # número não aparece no endereço
        codigo=parse_qs(urlparse(url).query)['u'][0]
        assert app._token_por_codigo_curto_vitrine(db,empresa,codigo)==usuario.pre_contrato_token
        assert url in parse_qs(urlparse(compartilhar).query)['text'][0]
        assert urlparse(compartilhar).netloc=='api.whatsapp.com'
        links.append(url)
    assert len(set(links))==2
    db.close()


def test_link_junior_atribui_whatsapp_junior_link_luiz_para_luiz():
    db,empresa,junior,luiz=fixture_db()
    for usuario in (junior,luiz):
        codigo=usuario.pre_contrato_token[:8]
        req=request_for('/e/karaokerj')
        resposta=app.portal_empresa('karaokerj',req,u=codigo,db=db)
        assert resposta.context['responsavel_vitrine_token']==usuario.pre_contrato_token
        nome, whatsapp=app._responsavel_pre_contrato_por_token(db,empresa,resposta.context['responsavel_vitrine_token'])
        assert nome==usuario.nome
        assert whatsapp==app._limpar_tel_whatsapp(usuario.telefone)
    db.close()


def test_troca_whatsapp_cadastro_mantem_link_pessoal():
    db,empresa,junior,luiz=fixture_db()
    codigo=junior.pre_contrato_token[:8]
    junior.telefone='21988887777';db.commit()
    token=app._resolver_responsavel_link_vitrine(db,empresa,u=codigo)
    assert token==junior.pre_contrato_token
    assert app._responsavel_pre_contrato_por_token(db,empresa,token)[1]=='5521988887777'
    db.close()


def test_invalido_inativo_sem_whatsapp_nao_cai_em_outra_pessoa():
    db,empresa,junior,luiz=fixture_db()
    with pytest.raises(HTTPException) as exc:
        app._resolver_responsavel_link_vitrine(db,empresa,u='9999999999')
    assert exc.value.status_code==404
    luiz.ativo=False;db.commit()
    with pytest.raises(HTTPException):
        app._resolver_responsavel_link_vitrine(db,empresa,u=luiz.pre_contrato_token[:8])
    junior.telefone=None;db.commit()
    with pytest.raises(HTTPException):
        app._resolver_responsavel_link_vitrine(db,empresa,u=junior.pre_contrato_token[:8])
    db.close()


def test_generic_direciona_so_para_numero_institucional():
    db,empresa,junior,luiz=fixture_db()
    cli=Cliente(empresa_id=empresa.id, identificador='teste',nome='Cliente')
    db.add(cli);db.flush()
    item=Solicitacao(empresa_id=empresa.id,cliente_id=cli.id,status='pre_reserva',
                     data_evento=date.today()+timedelta(days=10),hora_inicio=time(12),hora_fim=time(16),
                     observacoes='[VITRINE_ORIGEM=1]')
    db.add(item);db.commit()
    nome,telefone=app._responsavel_contrato_dados(request_for('/e/karaokerj'),db,empresa,item,fixar=True)
    assert nome=='Karaokê RJ'
    assert telefone=='5521911110000'
    assert item.responsavel_contrato=='Karaokê RJ'
    assert item.responsavel_contrato_telefone=='5521911110000'
    db.close()


def test_link_legado_funciona_e_vitrine_preserva_token_do_link():
    db,empresa,junior,luiz=fixture_db()
    req=request_for('/e/karaokerj')
    resp=app.portal_empresa('karaokerj',req,r=junior.pre_contrato_token,db=db)
    assert resp.context['responsavel_vitrine_token']==junior.pre_contrato_token
    # O catálogo e o carrinho levam o token em campos escondidos.
    assert 'name="r"' in (app.templates.get_template('publico/vitrine_inicio.html').render(
        empresa=empresa,request=req,hoje=date.today().isoformat(),responsavel_vitrine_token=junior.pre_contrato_token,mensagens_tipo_evento={})).lower()
    assert 'name="responsavel_token"' in app.templates.get_template('publico/vitrine.html').render(
        request=req,empresa=empresa,data_evento=date.today(),tipo_evento='residencial',
        tipo_evento_nome='Residencial', itens=[],categorias=[],erro='',
        cupons_ativos=False,fluxo_vitrine='direto',hoje=date.today().isoformat(),
        whatsapp_inicial='',cep_inicial='',numero_inicial='',frete_inicial=None,
        estado_compartilhado=None,responsavel_vitrine_token=junior.pre_contrato_token,
        bloqueio_data=None,mensagens_tipo_evento={},
    )
    db.close()


def test_vitrine_exibe_somente_acesso_individual_e_compartilhar_whatsapp():
    for pagina in ('admin/vitrine.html','admin/perfil.html','admin/empresa_guiada.html'):
        assert app.templates.get_template(pagina)
    vitrine=Path('templates/admin/vitrine.html').read_text()
    perfil=Path('templates/admin/perfil.html').read_text()
    empresa=Path('templates/admin/empresa_guiada.html').read_text()
    assert 'vitrine_url' in vitrine and 'vitrine_compartilhar_whatsapp' in vitrine
    assert 'Links de todos os atendentes' not in vitrine
    assert 'Link geral (sem atendente vinculado)' not in vitrine
    assert 'link_pessoal_vitrine' not in perfil
    assert 'Link direto sem aprovação' not in empresa
    assert 'Link público:' not in Path('templates/admin/empresas.html').read_text()
    assert 'href="{{ vitrine_url }}"' in vitrine and 'href="{{ vitrine_url }}"' in empresa


def test_vitrine_sem_whatsapp_nao_oferece_link_generico():
    db, empresa, junior, luiz = fixture_db()
    junior.telefone = None
    db.commit()
    assert app._vitrine_link_do_usuario(request_for('/painel/vitrine',usuario='junior'), db, empresa)==('', '')
    db.close()


def test_link_legado_direto_nao_burla_aprovacao():
    db, empresa, junior, luiz = fixture_db()
    empresa.vitrine_link_direto_token='link-direto-legado'
    empresa.vitrine_fluxo='aprovacao'
    db.commit()
    req=request_for('/e/karaokerj/direto/link-direto-legado')
    response=app.portal_empresa_direto('karaokerj','link-direto-legado',req,db=db)
    assert response.status_code==303
    assert response.headers['location']=='/e/karaokerj'
    assert not any(key.startswith('vitrine_direta') for key in req.session)
    fonte=Path('app.py').read_text()
    assert 'fluxo = "direto"  # Vitrine pública' not in fonte
    assert '_vitrine_direta_sessao_valida' not in fonte
    db.close()


def test_reservas_diretas_da_vitrine_sao_marcadas_para_evitar_atribuicao_aleatoria():
    from pathlib import Path
    fonte=Path('app.py').read_text()
    assert 'if pedido_vitrine and not pre_reserva_existente:' in fonte
    assert 'observacoes = "[VITRINE_ORIGEM=1]"' in fonte
