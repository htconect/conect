"""Testes sem rede da integração de frete com a Routes API do Google."""
import json
import os
from types import SimpleNamespace
from unittest.mock import patch

import app


class FakeGoogleResponse:
    def __init__(self, data):
        self.data=data
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size=None): return json.dumps(self.data).encode()


def test_google_rota_real_usa_api_e_menor_alternativa():
    resposta=FakeGoogleResponse({"routes":[{"distanceMeters":47200},{"distanceMeters":46500}],"geocodingResults":{"origin":{"placeId":"origem"},"destination":{"placeId":"destino"}}})
    with patch.dict(os.environ,{"GOOGLE_MAPS_API_KEY":"test-only","GOOGLE_MAPS_ROUTES_TRAFFIC_AWARE":"true"}), \
         patch.object(app,'urlopen',return_value=resposta) as requisicao:
        km=app._calcular_rota_google_km('Rua da Loja, 1, Rio de Janeiro','Rua do Cliente, 4, Rio de Janeiro')
    assert km==46.5
    req=requisicao.call_args.args[0]
    assert req.full_url=='https://routes.googleapis.com/directions/v2:computeRoutes'
    corpo=json.loads(req.data)
    assert corpo['origin']['address'].startswith('Rua da Loja')
    assert corpo['destination']['address'].startswith('Rua do Cliente')
    assert corpo['computeAlternativeRoutes'] is True
    assert corpo['routingPreference']=='TRAFFIC_AWARE'
    assert req.get_header('X-goog-api-key')=='test-only'


def test_google_sem_rotas_nunca_faz_estimativa():
    with patch.dict(os.environ,{"GOOGLE_MAPS_API_KEY":"test-only"}), \
         patch.object(app,'urlopen',return_value=FakeGoogleResponse({"routes":[],"geocodingResults":{"origin":{"placeId":"origem"},"destination":{"placeId":"destino"}}})):
        assert app._calcular_rota_google_km('Endereço loja','Endereço cliente') is None


def test_google_recusa_endereco_parcial():
    dados={"routes":[{"distanceMeters":13100}], "geocodingResults":{"origin":{"placeId":"origem"},"destination":{"placeId":"bairro","partialMatch":True}}}
    with patch.dict(os.environ,{"GOOGLE_MAPS_API_KEY":"test-only"}), \
         patch.object(app,'urlopen',return_value=FakeGoogleResponse(dados)):
        assert app._calcular_rota_google_km('Rua loja 123','Rua destino 456') is None


def test_google_key_nao_exposta_sem_configuracao():
    with patch.dict(os.environ,{"GOOGLE_MAPS_API_KEY":""}), \
         patch.object(app,'urlopen') as requisicao:
        assert app._calcular_rota_google_km('Loja','Cliente') is None
    requisicao.assert_not_called()


def test_share_periodo_frontend_conserva_link_original():
    html=open('templates/publico/vitrine.html',encoding='utf-8').read()
    assert '<button type="button" id="compartilharVitrine"' in html
    assert 'if(OFERTA_PERIODO){' in html
    assert "window.location.origin+window.location.pathname" in html


def test_migracao_coluna_origem_no_startup_leve():
    import inspect
    assert 'frete_endereco_origem' in inspect.getsource(app._garantir_colunas_v113_criticas)
