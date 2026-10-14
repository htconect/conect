"""Testes locais sem acesso à internet para compartilhamento, CEP e frete."""
import asyncio
import json
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import urlparse, parse_qs
import app

EMPRESA=SimpleNamespace(id=1, slug='karaokerj',ativa=True,vitrine_ativa=True,frete_tipo='km',frete_cep_origem='21031700',frete_valor_km=1.5)
DADOS=lambda cep:{'cidade':'Rio de Janeiro','estado':'RJ','logradouro':'Rua','bairro':'Freguesia'} if cep in ('21031700','21911280') else {}

def _db():
    db=Mock()
    db.query.return_value.filter_by.return_value.first.return_value=EMPRESA
    return db

class Req:
    def __init__(self,body=b''):
        self._body=body
        self.headers={'content-length':str(len(body))}
        self.base_url='https://conect.humiat.com.br/'
    async def body(self):return self._body

class HttpResp:
    def __init__(self,obj): self.obj=obj
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,max_bytes=None):return json.dumps(self.obj).encode()

def test_busca_cep_por_endereco():
    dados=[{'cep':'21911-280','logradouro':'Rua General Edgardino Pinta','bairro':'Freguesia','localidade':'Rio de Janeiro','uf':'RJ'}]
    with patch.object(app,'urlopen',return_value=HttpResp(dados)) as fake:
        result=app.vitrine_buscar_cep_endereco('karaokerj',Req(),uf='RJ',cidade='Rio de Janeiro',rua='General Edgardino',db=_db())
    assert result['ok'] and result['resultados'][0]['cep']=='21911280'
    assert 'viacep.com.br' in fake.call_args.args[0].full_url

def test_endereco_curto_nao_consulta_servico():
    with patch.object(app,'urlopen') as fake:
        result=app.vitrine_buscar_cep_endereco('karaokerj',Req(),uf='RJ',cidade='Rio de Janeiro',rua='Ru',db=_db())
    assert result.status_code==400
    fake.assert_not_called()

def test_compartilhamento_selecoes_nao_dados_pessoais():
    registro={
      'data_evento':(date.today()+timedelta(days=10)).isoformat(),
      'tipo_evento':'residencial','cep':'21911280','numero':'135',
      'cupom':'ABC10','hora':'16:00','retirada_mesmo_dia':True,'horas':1,
      'produtos':[{'id':5,'q':2,'opcionais':[{'id':9,'q':1}]}],
      'whatsapp':'21999999999','nome':'Fulano', 'cpf':'12345678909',
    }
    req=Req(json.dumps(registro).encode())
    db=_db()
    resposta=asyncio.run(app.vitrine_gerar_link_compartilhamento('karaokerj',req,db=db))
    assert resposta['ok']
    assert '/s/' in urlparse(resposta['url']).path
    original=json.loads(db.add.call_args.args[0].pedido_json)
    assert original['produtos']==registro['produtos']
    assert original['cupom']=='ABC10' and original['hora']=='16:00'
    assert 'whatsapp' not in original and 'nome' not in original and 'cpf' not in original

def test_frete_zero_nao_confirma_sem_rota():
    with patch.object(app,'_dados_cep_brasil',side_effect=DADOS),\
         patch.object(app,'_coordenadas_cep',return_value=(-22.8,-43.2,'origem')),\
         patch.object(app,'_coordenadas_cep_numero',return_value=(-22.8,-43.2,'destino')),\
         patch.object(app,'_trecho_rodoviario',return_value=(0,3,'osrm')),\
         patch.object(app,'_coordenadas_cep_referencia',return_value=(None,None,'erro')):
        resultado=app._calcular_frete_vitrine(EMPRESA,'21911-280','135')
    assert resultado['ok'] is False and 'distância' in resultado['erro']

def test_frete_zero_recupera_referencia_postal():
    with patch.object(app,'_dados_cep_brasil',side_effect=DADOS),\
         patch.object(app,'_coordenadas_cep',return_value=(-22.8,-43.2,'origem')),\
         patch.object(app,'_coordenadas_cep_numero',return_value=(-22.8,-43.2,'destino')),\
         patch.object(app,'_trecho_rodoviario',side_effect=[(0,3,'osrm'),(15.1,31,'osrm')]),\
         patch.object(app,'_coordenadas_cep_referencia',side_effect=[(-22.84,-43.25,'postal'),(-22.79,-43.17,'postal')]):
        resultado=app._calcular_frete_vitrine(EMPRESA,'21911-280','135')
    assert resultado['ok'] and resultado['distancia_ida_km']==15.1
    assert resultado['quantidade_km']==30.2

if __name__=='__main__':
    for k,v in sorted(globals().copy().items()):
        if k.startswith('test_') and callable(v):
            v(); print('OK',k)
