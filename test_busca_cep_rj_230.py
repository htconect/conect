"""Testes isolados de busca RJ, sem rede nem banco de produção."""
import ast
import json
import logging
import os
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request as UrlRequest
from unittest.mock import patch

# Isola as funções efetivas do app, sem importar o startup e o banco.
mod = ast.parse(Path(__file__).with_name('app.py').read_text())
nomes = {'_ceps_busca_google', '_cep_busca_normalizar_rua', '_cep_busca_normalizar_texto', '_cep_busca_prioridade_faixa', '_ceps_busca_viacep', '_buscar_ceps_rj'}
ns = dict(globals(), logger=logging.getLogger('test'))
exec(compile(ast.Module(body=[n for n in mod.body if isinstance(n, ast.FunctionDef) and n.name in nomes], type_ignores=[]), 'app.py', 'exec'), ns)

class Resposta:
    def __init__(self, data): self.data=data
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,*args): return json.dumps(self.data).encode()

def busca(fake, rua='av das americas', numero='16355'):
    ns['urlopen']=fake
    with patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY':'test','GOOGLE_GEOCODING_API_KEY':''}):
        return ns['_buscar_ceps_rj'](rua, numero)

def test_google_negado_fallback_lista_ordenada():
    chamadas=[]
    def fake(req, timeout):
        chamadas.append(req.full_url)
        if 'googleapis' in req.full_url: return Resposta({'status':'REQUEST_DENIED'})
        return Resposta([{'cep':'22000-001','uf':'RJ','logradouro':'Avenida das Américas','localidade':'Rio de Janeiro','complemento':'até 10000 - lado par'}, {'cep':'22000-002','uf':'RJ','logradouro':'Avenida das Américas','localidade':'Rio de Janeiro','complemento':'de 10001 a 20000 - lado ímpar'}, {'cep':'22000-002','uf':'RJ','logradouro':'Duplicado'}, {'cep':'11000-001','uf':'SP','logradouro':'Outra'}])
    res=busca(fake)
    assert res['ok'] and res['fonte']=='viacep'
    assert [x['cep'] for x in res['resultados']]==['22000002','22000001']
    assert all(not x['numero_confirmado'] for x in res['resultados'])
    assert '/RJ/Rio%20de%20Janeiro/Avenida%20das%20americas/' in chamadas[1]

def test_google_exato_sem_fallback():
    def componente(tipo, valor): return {'types':[tipo],'long_name':valor,'short_name':valor}
    partes=[componente('administrative_area_level_1','RJ'),componente('country','BR'),componente('postal_code','22000-123'),componente('route','Avenida das Américas'),componente('street_number','16355')]
    def fake(req, timeout):
        assert 'googleapis' in req.full_url
        return Resposta({'status':'OK','results':[{'address_components':partes}]})
    res=busca(fake)
    assert res['fonte']=='google' and res['resultados'][0]['numero_confirmado']

def test_cidade_no_mesmo_campo_e_falhas():
    def fake(req, timeout):
        if 'googleapis' in req.full_url: raise TimeoutError()
        assert '/RJ/Niter%C3%B3i/Rua%20Moreira/' in req.full_url
        return Resposta([])
    res=busca(fake,'Rua Moreira, Niterói','12')
    assert res['ok'] and not res['resultados'] and 'Niterói' in res['aviso']
    def falha(*args, **kwargs): raise TimeoutError()
    assert busca(falha)['codigo']=='BUSCA_RJ_INDISPONIVEL'
