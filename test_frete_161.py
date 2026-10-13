"""Testes offline da correção de frete 1.0.161, sem requisições reais."""
from types import SimpleNamespace
from unittest.mock import patch
import json
import app

EMPRESA=SimpleNamespace(id=1,frete_tipo="km",frete_cep_origem="21031700",frete_valor_km=5)
ORIGEM={"cidade":"Rio de Janeiro","estado":"RJ","logradouro":"Av Brasil"}
DESTINO={"cidade":"Rio de Janeiro","estado":"RJ","logradouro":"Rua General Edgardino Pinta","bairro":"Freguesia (Ilha do Governador)"}
DADOS=lambda cep: ORIGEM if cep=="21031700" else DESTINO if cep=="21911280" else {}


def test_cep_valido_rota_incoerente_recupera_por_cep():
    with patch.object(app,"_dados_cep_brasil",side_effect=DADOS), \
         patch.object(app,"_coordenadas_cep",return_value=(-10.0,-43.0,"erro")), \
         patch.object(app,"_coordenadas_cep_numero",return_value=(-22.79,-43.17,"ok")), \
         patch.object(app,"_trecho_rodoviario",side_effect=[(640,22,"osrm"),(18.5,20,"osrm")]) as rota, \
         patch.object(app,"_coordenadas_cep_referencia",side_effect=[(-22.84,-43.25,"brasilapi"),(-22.79,-43.17,"brasilapi")]):
        resposta=app._calcular_frete_vitrine(EMPRESA,"21911-280","135")
        assert resposta["ok"] is True, resposta
        assert resposta["valor"]==185.0
        assert resposta["distancia_ida_km"]==18.5
        assert "cep:" in resposta["fonte"]
        assert rota.call_count == 2


def test_cep_inexistente_nao_calcula():
    with patch.object(app,"_dados_cep_brasil",return_value={}),patch.object(app,"_trecho_rodoviario") as rota:
        r=app._calcular_frete_vitrine(EMPRESA,"00000-000","1")
        assert not r["ok"] and "CEP não localizado" in r["erro"]
        rota.assert_not_called()


def test_referencia_indisponivel_nao_fabrica_frete():
    with patch.object(app,"_dados_cep_brasil",side_effect=DADOS), \
         patch.object(app,"_coordenadas_cep",return_value=(-10.0,-43.0,"erro")), \
         patch.object(app,"_coordenadas_cep_numero",return_value=(-22.79,-43.17,"ok")), \
         patch.object(app,"_trecho_rodoviario",return_value=(640,22,"osrm")), \
         patch.object(app,"_coordenadas_cep_referencia",return_value=(None,None,"indisponivel")):
        r=app._calcular_frete_vitrine(EMPRESA,"21911-280","135")
        assert not r["ok"] and "CEP confirmado" in r["erro"]


def test_frete_normal_sem_consultas_adicionais():
    with patch.object(app,"_dados_cep_brasil",side_effect=DADOS), \
         patch.object(app,"_coordenadas_cep",return_value=(-22.84,-43.25,"ok")), \
         patch.object(app,"_coordenadas_cep_numero",return_value=(-22.79,-43.17,"ok")), \
         patch.object(app,"_trecho_rodoviario",return_value=(17,30,"osrm")), \
         patch.object(app,"_coordenadas_cep_referencia") as referencia:
        r=app._calcular_frete_vitrine(EMPRESA,"21911-280","135")
        assert r["ok"] and r["valor"]==170
        referencia.assert_not_called()


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
