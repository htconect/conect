"""Números não localizados usam rota viária por CEP, mantendo aviso operacional."""
import json
import os
from types import SimpleNamespace
from unittest.mock import patch

import app
from test_google_routes_184 import FakeGoogleResponse

CEP = '20735080'
GEO = (-22.902, -43.28)
DADOS = {'logradouro': 'Rua Silva Rabelo', 'bairro': 'Méier', 'cidade': 'Rio de Janeiro', 'estado': 'RJ'}
EMPRESA = SimpleNamespace(id=1, frete_tipo='km', frete_cep_origem='20725000',
                          frete_endereco_origem='Rua de Origem, 45, Méier, Rio de Janeiro, RJ', frete_valor_km=1.7)


def resposta_rota(distancia, *, parcial=False, tipo='postal_code', lat=-22.902, lon=-43.28):
    return {'routes': [{'distanceMeters': distancia, 'legs': [{'endLocation': {'latLng': {'latitude': lat, 'longitude': lon}}}]}],
            'geocodingResults': {'origin': {'placeId': 'loja'}, 'destination': {'placeId': 'local', 'partialMatch': parcial, 'type': [tipo]}}}


def test_quando_numero_nao_resolve_tenta_cep_e_calcula_ida_e_volta():
    chamadas = []
    def google(req, timeout=10):
        dest = json.loads(req.data)['destination']['address']
        chamadas.append(dest)
        if '303' in dest:
            return FakeGoogleResponse(resposta_rota(10400, parcial=True, lat=-23.3, lon=-43.8, tipo='route'))
        return FakeGoogleResponse(resposta_rota(10100))

    with patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'test-only'}), \
         patch.object(app, '_dados_cep_brasil', return_value=DADOS), \
         patch.object(app, '_coordenadas_cep_referencia', return_value=(*GEO, 'brasilapi')), \
         patch.object(app, 'urlopen', side_effect=google):
        resultado = app._calcular_frete_vitrine(EMPRESA, CEP, '303')

    assert any('303' in p for p in chamadas)
    assert any('CEP 20735-080' in p and '303' not in p for p in chamadas)
    assert resultado['ok'] is True and not resultado.get('consultar', False)
    assert resultado['distancia_ida_km'] == 10.1
    assert resultado['valor'] == 34.34
    assert resultado['fonte'] == 'google_routes_cep'
    assert resultado['frete_estimado_cep'] is True
    assert 'Número não confirmado' in resultado['aviso_endereco']


def test_google_encontra_numero_exato_nao_precisa_de_fallback():
    with patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'test-only'}), \
         patch.object(app, '_dados_cep_brasil', return_value=DADOS), \
         patch.object(app, '_coordenadas_cep_referencia') as ref, \
         patch.object(app, 'urlopen', return_value=FakeGoogleResponse(resposta_rota(11200, tipo='street_address'))) as url:
        resultado = app._calcular_frete_vitrine(EMPRESA, CEP, '15')
    assert resultado['tipo'] == 'km'
    assert resultado['frete_estimado_cep'] is False
    assert resultado['fonte'] == 'google_routes'
    ref.assert_not_called()
    assert url.call_count == 1


def test_correspondencia_parcial_proxima_calcula_mas_numero_fica_a_conferir():
    with patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'test-only'}), \
         patch.object(app, '_dados_cep_brasil', return_value=DADOS), \
         patch.object(app, '_coordenadas_cep_referencia', return_value=(*GEO, 'brasilapi')), \
         patch.object(app, 'urlopen', return_value=FakeGoogleResponse(resposta_rota(10200, parcial=True, tipo='route'))) as url:
        resultado = app._calcular_frete_vitrine(EMPRESA, CEP, '303')
    assert resultado['distancia_ida_km'] == 10.2
    assert resultado['frete_estimado_cep'] is True
    assert resultado['fonte'] == 'google_routes'
    assert url.call_count == 1


def test_cep_resulta_em_outro_bairro_fica_pendente_em_vez_de_cobrar_valor_errado():
    with patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'test-only'}), \
         patch.object(app, '_dados_cep_brasil', return_value=DADOS), \
         patch.object(app, '_coordenadas_cep_referencia', return_value=(*GEO, 'brasilapi')), \
         patch.object(app, 'urlopen', return_value=FakeGoogleResponse(resposta_rota(10100, parcial=True, tipo='route', lat=-23.3, lon=-43.8))):
        resultado = app._calcular_frete_vitrine(EMPRESA, CEP, '303')
    assert resultado['consultar'] is True
    assert resultado['valor'] == 0


def test_cep_sem_referencia_independente_nao_e_automaticamente_aprovado():
    with patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'test-only'}), \
         patch.object(app, '_dados_cep_brasil', return_value=DADOS), \
         patch.object(app, '_coordenadas_cep_referencia', return_value=(None, None, 'indisponivel')), \
         patch.object(app, 'urlopen', return_value=FakeGoogleResponse(resposta_rota(10100, parcial=True, tipo='postal_code'))):
        resultado = app._calcular_frete_vitrine(EMPRESA, CEP, '303')
    assert resultado['consultar'] is True


def test_aviso_cliente_e_snapshot_preservados():
    from pathlib import Path
    import inspect
    html = Path('templates/publico/vitrine.html').read_text(encoding='utf-8')
    fonte = inspect.getsource(app.vitrine_publica_reservar)
    assert 'Frete estimado pelo CEP' in html or 'frete estimado pelo CEP' in html
    assert 'frete_estimado_cep' in fonte
    assert 'aviso_endereco' in fonte
    assert 'frete_manual' not in str(inspect.signature(app.vitrine_publica_reservar))
