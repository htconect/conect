"""Regressões dos bloqueios comerciais e do salvamento robusto de combos."""
from datetime import date, timedelta, time
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import app
from models import Empresa, ProdutoServico, ComboProdutoPrincipal
from test_migrar_produto_combo_223 import _setup, _client


def test_componente_invalido_retorna_motivo_sem_gravar():
    engine,(empresa_id,principal_id,pro_id,jbl_id,_,_),_= _setup()
    cliente=_client(engine,empresa_id)
    try:
        resposta=cliente.post(f'/painel/produto/{pro_id}',data={
            'nome':'Jukebox Pro','valor_base':'700','tipo_cadastro':'combo',
            'combo_principal_id':str(pro_id),'combo_principal_quantidade':'1',
        },headers={'Accept':'application/json'})
        assert resposta.status_code==422
        assert 'não pode aparecer duas vezes' in resposta.json()['erro']
        with Session(engine) as db:
            produto=db.get(ProdutoServico,pro_id)
            assert not produto.eh_combo
            assert db.query(ComboProdutoPrincipal).filter_by(combo_id=pro_id).count()==0
    finally:
        app.app.dependency_overrides.clear();cliente.close();engine.dispose()


def test_formulario_exibe_erros_sem_navegar_e_reabre_secao():
    html=(Path(__file__).parent/'templates/admin/produto_form.html').read_text(encoding='utf8')
    assert 'id="erroSalvarProduto"' in html
    assert 'window.exibirErroCadastroProduto' in html
    assert "const resposta=await fetch(form.action" in html
    assert "headers:{'Accept':'application/json'}" in html
    assert 'respostaJson?.erro' in html
    assert "const detalhes=evento.target.closest('details')" in html
    assert 'resposta.status>=500' in html
    assert 'new FormData(form)' in html
    assert "if(acionador?.name)dados.set(acionador.name" in html


def test_bloqueio_manual_nao_causa_cascata_no_combo():
    codigo=(Path(__file__).parent/'app.py').read_text(encoding='utf8')
    assert 'if pid in bloqueios:' in codigo
    assert 'if bloqueio_data or int(produto.id) in bloqueios_produto:' in codigo
    assert 'or any(pid in bloqueios_produto for pid in componentes_produto)' not in codigo
