"""Garantias: cliente não define frete, e rota parcial precisa conferir CEP."""
import inspect
import os
from unittest.mock import patch
from types import SimpleNamespace

import app
from test_google_routes_184 import FakeGoogleResponse


def rota_parcial(lat, lon, distancia=10100, tipo='route'):
    return {"routes": [{"distanceMeters": distancia, "legs": [{"endLocation": {"latLng": {"latitude": lat, "longitude": lon}}}]}],
            "geocodingResults": {"origin": {"placeId": "origem"},
                                "destination": {"placeId": "destino", "partialMatch": True, "type": [tipo]}}}


def test_rota_parcial_perto_de_cep_validado_aceita_quilometragem_google():
    data = rota_parcial(-22.902, -43.28)
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-only"}), \
         patch.object(app, "urlopen", return_value=FakeGoogleResponse(data)) as chamada, \
         patch.object(app, "_coordenadas_cep_referencia", return_value=(-22.901, -43.279, "brasilapi")):
        km = app._calcular_rota_google_km("Loja, Rio RJ", "Rua Destino, 10, Rio RJ",
                                         cep_destino_validado="20735080")
    assert km == 10.1
    mask = chamada.call_args.args[0].get_header('X-goog-fieldmask')
    assert 'routes.legs.endLocation' in mask
    assert 'geocodingResults.destination.type' in mask


def test_rota_parcial_distante_do_cep_nunca_gera_cobranca():
    data = rota_parcial(-23.05, -43.45)
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-only"}), \
         patch.object(app, "urlopen", return_value=FakeGoogleResponse(data)), \
         patch.object(app, "_coordenadas_cep_referencia", return_value=(-22.901, -43.279, "brasilapi")):
        assert app._calcular_rota_google_km("Loja RJ", "Destino RJ", cep_destino_validado="20735080") is None


def test_rota_parcial_sem_referencia_postal_fica_pendente():
    data = rota_parcial(-22.902, -43.28)
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-only"}), \
         patch.object(app, "urlopen", return_value=FakeGoogleResponse(data)), \
         patch.object(app, "_coordenadas_cep_referencia", return_value=(None, None, "indisponivel")):
        assert app._calcular_rota_google_km("Loja RJ", "Destino RJ", cep_destino_validado="20735080") is None


def test_rota_parcial_sem_tipo_de_endereco_nao_e_aprovada():
    data = rota_parcial(-22.902, -43.28, tipo='locality')
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-only"}), \
         patch.object(app, "urlopen", return_value=FakeGoogleResponse(data)), \
         patch.object(app, "_coordenadas_cep_referencia") as referencia:
        assert app._calcular_rota_google_km("Loja RJ", "Destino RJ", cep_destino_validado="20735080") is None
    referencia.assert_not_called()


def test_rota_parcial_com_origem_duvidosa_e_bloqueada():
    data = rota_parcial(-22.902, -43.28)
    data['geocodingResults']['origin']['partialMatch'] = True
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-only"}), \
         patch.object(app, "urlopen", return_value=FakeGoogleResponse(data)), \
         patch.object(app, "_coordenadas_cep_referencia") as referencia:
        assert app._calcular_rota_google_km("Loja RJ", "Destino RJ", cep_destino_validado="20735080") is None
    referencia.assert_not_called()


def test_vitrine_sem_autorizacao_cliente_alterar_frete_por_post():
    html = open('templates/publico/vitrine.html', encoding='utf-8').read()
    fonte = inspect.getsource(app.vitrine_publica_reservar)
    assert 'name="frete_manual"' not in html
    assert 'Informar valor do frete' not in html
    assert 'manual_cliente' not in fonte
    assert 'frete_manual' not in str(inspect.signature(app.vitrine_publica_reservar))
    assert 'frete = _frete_reutilizado(' in fonte
    assert 'frete_pendente' in fonte
    assert 'Enviar pedido para aprovar frete' in html
    assert 'return freteOk&&' in html  # Permite encaminhar sem concluir contrato
    assert '_aplicar_frete_manual_cliente' not in inspect.getsource(app)


def test_aprovacao_manual_so_pelo_painel_e_valor_positivo():
    fonte = inspect.getsource(app.vitrine_aprovar_frete)
    assert 'empresa_logada' in fonte
    assert 'quantia <= 0' in fonte
    assert 'aprovado_manualmente' in fonte


def test_google_rota_parcial_integrada_ao_calculo_por_km():
    dados_cep = {'logradouro': 'Rua Silva Rabelo', 'bairro': 'Méier', 'cidade': 'Rio de Janeiro', 'estado': 'RJ'}
    empresa = SimpleNamespace(id=1, frete_tipo='km', frete_cep_origem='20725000',
                              frete_endereco_origem='Rua Exemplo, 10, Méier, Rio de Janeiro, RJ', frete_valor_km=1.7)
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-only"}), \
         patch.object(app, '_dados_cep_brasil', return_value=dados_cep), \
         patch.object(app, '_calcular_rota_google_km', return_value=10.1) as calcular:
        resultado = app._calcular_frete_vitrine(empresa, '20735080', '80')
    assert resultado['tipo'] == 'km'
    assert resultado['distancia_ida_km'] == 10.1
    assert resultado['valor'] == 34.34
    assert calcular.call_args.kwargs['cep_destino_validado'] == '20735080'
