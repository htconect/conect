"""Testes offline da correção de frete 1.0.161, sem requisições reais."""
from types import SimpleNamespace
from unittest.mock import patch
import json
import os
import app

EMPRESA=SimpleNamespace(id=1,frete_tipo="km",frete_cep_origem="21031700",frete_valor_km=5,frete_endereco_origem="Av Brasil, 1000, Rio de Janeiro, RJ")
ORIGEM={"cidade":"Rio de Janeiro","estado":"RJ","logradouro":"Av Brasil"}
DESTINO={"cidade":"Rio de Janeiro","estado":"RJ","logradouro":"Rua General Edgardino Pinta","bairro":"Freguesia (Ilha do Governador)"}
DADOS=lambda cep: ORIGEM if cep=="21031700" else DESTINO if cep=="21911280" else {}


def test_frete_google_por_km_ida_volta():
    with patch.dict(os.environ,{"GOOGLE_MAPS_API_KEY":"test-only"}), \
         patch.object(app,"_dados_cep_brasil",side_effect=DADOS), \
         patch.object(app,"_calcular_rota_google_km",return_value=47.2) as rota, \
         patch.object(app,"_trecho_rodoviario") as osrm:
        resposta=app._calcular_frete_vitrine(EMPRESA,"21911-280","135")
    assert resposta["ok"], resposta
    assert resposta["fonte"]=="google_routes"
    assert resposta["distancia_ida_km"]==47.2
    assert resposta["quantidade_km"]==94.4
    assert resposta["valor"]==472.0
    assert "135" in rota.call_args.args[1] and "Brasil" in rota.call_args.args[0]
    osrm.assert_not_called()


def test_cep_inexistente_nao_calcula():
    with patch.object(app,"_dados_cep_brasil",return_value={}),patch.object(app,"_trecho_rodoviario") as rota:
        r=app._calcular_frete_vitrine(EMPRESA,"00000-000","1")
        assert not r["ok"] and "CEP não localizado" in r["erro"]
        rota.assert_not_called()


def test_google_indisponivel_nao_fabrica_frete():
    with patch.dict(os.environ,{"GOOGLE_MAPS_API_KEY":"test-only"}), \
         patch.object(app,"_dados_cep_brasil",side_effect=DADOS), \
         patch.object(app,"_calcular_rota_google_km",return_value=None):
        resposta=app._calcular_frete_vitrine(EMPRESA,"21911-280","135")
    assert resposta["ok"] and resposta["consultar"] and resposta["valor"]==0 and resposta["erro_rota"]


def test_google_nao_configurado_nao_usa_osrm():
    with patch.dict(os.environ,{"GOOGLE_MAPS_API_KEY":""}), \
         patch.object(app,"_dados_cep_brasil",side_effect=DADOS), \
         patch.object(app,"_trecho_rodoviario") as osrm:
        resposta=app._calcular_frete_vitrine(EMPRESA,"21911-280","135")
    assert resposta["ok"] and resposta["consultar"] and "Google" in resposta["erro_rota"]
    osrm.assert_not_called()


def test_referencia_municipio_divergente_recusada():
    app._CEP_GEO_REFERENCIA_CACHE.clear()
    class Resp:
        def __init__(self, dados):self.dados=dados
        def __enter__(self):return self
        def __exit__(self,*x):pass
        def read(self):return json.dumps(self.dados).encode()
    respostas=[
        {"cep":"21911280","state":"RJ","city":"Niteroi","location":{"coordinates":{"latitude":"-22.9","longitude":"-43.1"}}},
        {"cep":"21911280","state":"RJ","city":"Niteroi","lat":"-22.9","lng":"-43.1"},
    ]
    with patch.object(app,"urlopen",side_effect=[Resp(item) for item in respostas]):
        r=app._coordenadas_cep_referencia("21911280",DESTINO)
        assert r[0] is None and r[1] is None
        assert "21911280" not in app._CEP_GEO_REFERENCIA_CACHE


def test_referencia_valida_brasilapi():
    app._CEP_GEO_REFERENCIA_CACHE.clear()
    class Resp:
        def __enter__(self):return self
        def __exit__(self,*x):pass
        def read(self):return json.dumps({"cep":"21911-280","state":"RJ","city":"Rio de Janeiro","location":{"coordinates":{"latitude":"-22.7907","longitude":"-43.1752"}}}).encode()
    with patch.object(app,"urlopen",return_value=Resp()):
        r=app._coordenadas_cep_referencia("21911280",DESTINO)
        assert r[2] == "brasilapi" and abs(r[0]+22.7907)<0.0001
        assert app._CEP_GEO_REFERENCIA_CACHE["21911280"] == r

if __name__ == '__main__':
 for k,v in list(globals().items()):
  if k.startswith("test_") and callable(v):
   v(); print('OK',k)
