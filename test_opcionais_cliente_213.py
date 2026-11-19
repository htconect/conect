"""Garantias da edição pública de opcionais (v1.0.213)."""
from pathlib import Path
from types import SimpleNamespace
import pytest
import app


def contrato(equipamentos=300, frete=38.34, desconto=0, horas=0, total=None):
    if total is None:
        total=round(equipamentos-desconto+horas+frete,2)
    return SimpleNamespace(valor_equipamentos=equipamentos, valor_frete=frete,
        valor_desconto=desconto, valor_horas_adicionais=horas, valor=total)


@pytest.mark.parametrize('adicionar,retirar,subtotal,total', [
    (80,0,380,418.34),
    (0,80,220,258.34),
    (120,80,340,378.34),
    (0,0,300,338.34),
])
def test_opcional_nunca_recalcula_frete(adicionar, retirar, subtotal, total):
    item=contrato()
    resultado=app._totais_alteracao_opcionais(item, adicionar, retirar)
    assert resultado == (subtotal,total)
    assert item.valor_frete == 38.34
    assert item.valor_desconto == 0


def test_cupom_e_frete_congelados_na_edicao():
    item=contrato(desconto=10)
    assert app._totais_alteracao_opcionais(item,80,0)==(380,408.34)
    assert item.valor_desconto==10
    assert item.valor_frete==38.34


def test_contrato_com_total_divergente_nao_pode_salvar_errado():
    item=contrato(total=290)
    assert app._totais_alteracao_opcionais(item,80,0) is None


def test_remocao_nao_pode_conduzir_subtotal_abaixo_do_desconto():
    item=contrato(equipamentos=300,desconto=270)
    assert app._totais_alteracao_opcionais(item,0,100) is None


def test_pagina_opcionais_revela_frete_e_aviso_processamento():
    fonte=Path('templates/publico/opcionais_contrato.html').read_text()
    assert 'Frete contratado (não muda)' in fonte
    assert 'erro == \'divergencia\'' in fonte
    assert 'salvamentoLento' in fonte
    assert 'Conferir contrato' in fonte


def test_fluxo_de_aceite_sem_aba_em_branco():
    fonte=Path('templates/admin/solicitacao_detalhe.html').read_text()
    assert 'target="_blank" href="{{ link_aceite_whatsapp }}"' not in fonte
    assert 'target="_blank" href="{{ link_contrato_whatsapp }}"' not in fonte
    fonte=Path('templates/admin/painel.html').read_text()
    assert 'target="_blank" rel="noopener noreferrer"\n                         href="/painel/solicitacao/' not in fonte
