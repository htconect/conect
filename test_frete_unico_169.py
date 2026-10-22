"""Verificacoes da composicao de frete unico na vitrine, contrato e cadastro."""
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import app


@pytest.mark.parametrize("itens,desconto,horas,frete,esperado", [
    (350, 0, 0, 57.60, 407.60),
    (650, 0, 0, 57.60, 707.60),
    (650, 65, 0, 57.60, 642.60),
    (650, 65, 100, 57.60, 742.60),
    (0, 0, 0, 57.60, 57.60),
    (650, 800, 0, 57.60, 57.60),
])
def test_total_servidor_com_frete_unico(itens, desconto, horas, frete, esperado):
    assert app._total_pedido_frete_unico(itens, desconto, horas, frete) == esperado


def test_total_persistido_no_contrato_com_dois_equipamentos():
    item = SimpleNamespace(valor_horas_adicionais=0, valor_desconto_manual=0)
    cupom = SimpleNamespace(codigo="KARAOKE10", percentual=10)
    app._aplicar_composicao_comercial(item, 350+300, 57.60, cupom)
    assert item.valor_equipamentos == 650
    assert item.valor_desconto == 65
    assert item.valor_frete == 57.60
    assert item.valor == 642.60
    assert app.composicao_valores_contrato(item)["total"] == 642.60


def test_carrinho_servidor_dois_equipamentos_um_frete():
    empresa = SimpleNamespace(id=1, slug="karaokerj", retirada_cortesia_proximo_dia=False)
    p1 = SimpleNamespace(id=1, nome="Equipamento A", empresa_id=1, ativo=True, vitrine_ativo=True)
    p2 = SimpleNamespace(id=2, nome="Equipamento B", empresa_id=1, ativo=True, vitrine_ativo=True)
    class DB:
        def get(self, _classe, id):
            return {1:p1, 2:p2}[id]
    request = SimpleNamespace(session={"vitrine_pedido_karaokerj": {
        "data_evento":"2026-11-14", "tipo_evento":"residencial", "hora_inicio":"18:00",
        "itens":[{"produto_id":1,"quantidade":1}, {"produto_id":2,"quantidade":1}],
        "frete":{"valor":57.60,"cep":"21031700","numero":"10"},
        "cupom_codigo":"KARAOKE10",
    }})
    with patch.object(app, "_preco_vitrine_produto", side_effect=lambda _db, _empresa, prod, _tipo:{"valor":350 if prod.id==1 else 300, "sob_consulta":False}), \
         patch.object(app, "_duracao_vitrine_produto", return_value=240), \
         patch.object(app, "_empresa_modulo_ativo", side_effect=lambda _empresa, modulo:modulo=="cupons"), \
         patch.object(app, "_cupom_valido", return_value=SimpleNamespace(codigo="KARAOKE10",percentual=10)), \
         patch.object(app, "_foto_capa_produto", return_value=""):
        pedido = app._pedido_vitrine_sessao(request, DB(), empresa)
    assert len(pedido["itens"]) == 2
    assert pedido["subtotal"] == 650
    assert pedido["desconto"] == 65
    assert pedido["frete"]["valor"] == 57.60
    assert pedido["total"] == 642.60


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js nao presente no ambiente")
def test_formula_navegador_dois_equipamentos_um_frete():
    origem=Path(__file__).parent / "templates/publico/vitrine.html"
    fonte=origem.read_text()
    trecho=fonte.split(" function totalPedidoVitrine(",1)[1].split(" function horaInicioValida",1)[0]
    javascript="function totalPedidoVitrine("+trecho+"\n"
    javascript+='''
    const assert = require('node:assert/strict');
    assert.equal(totalPedidoVitrine(350,0,0,57.60),407.6);
    assert.equal(totalPedidoVitrine(650,0,0,57.60),707.6);
    assert.equal(totalPedidoVitrine(650,65,0,57.60),642.6);
    assert.equal(totalPedidoVitrine(650,65,100,57.60),742.6);
    '''
    processo=subprocess.run(["node","-"],input=javascript,text=True,capture_output=True)
    assert processo.returncode==0, processo.stderr


def test_cadastro_item_e_opcionais_exibidos_separados():
    template=(Path(__file__).parent / "templates/publico/cadastro.html").read_text()
    assert "R$ {{ reg.valor_base_total|moeda_br }}" in template
    assert "R$ {{ reg.valor_total|moeda_br }}{% endif %}</small>{% if reg.opcionais %}" not in template
