"""Movimentos de extrato do Banco Principal já efetivados com data contábil de segunda-feira."""
from datetime import date, datetime
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import app
from models import Base, ContaFinanceira, LancamentoBanco


def test_proximo_dia_util_novembro_20_2026():
    assert app.proximo_dia_util_bancario(date(2026, 11, 20)) == date(2026, 11, 23)
    assert app.proximo_dia_util_bancario(date(2026, 11, 21)) == date(2026, 11, 23)
    assert app.proximo_dia_util_bancario(date(2026, 11, 23)) == date(2026, 11, 24)


def test_regra_banco_nao_antecipar_lancamentos_nao_efetivados():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        banco = ContaFinanceira(empresa_id=1, nome='Banco Principal', tipo='banco', ativa=True)
        session.add(banco)
        session.flush()
        registros = [
            (date(2026, 11, 19), 100, None, datetime(2026, 11, 19)),
            (date(2026, 11, 20), 200, None, datetime(2026, 11, 20)),
            (date(2026, 11, 23), 300, 'extrato_20.csv', datetime(2026, 11, 20)),
            (date(2026, 11, 23), -50, 'extrato_20.csv', datetime(2026, 11, 20)),
            (date(2026, 11, 23), 700, None, datetime(2026, 11, 20)),  # manual futuro
            (date(2026, 11, 24), 900, 'extrato.csv', datetime(2026, 11, 20)),  # longe demais
            (date(2026, 11, 23), 150, 'extrato_23.csv', datetime(2026, 11, 23)),  # ainda não importado
            (date(2026, 11, 23), 40, 'extrato_tarde.csv', datetime(2026, 11, 21, 0, 30)),  # 20/11 21:30 BRT
        ]
        for i, (dia, valor, origem, criado_em) in enumerate(registros):
            session.add(LancamentoBanco(
                empresa_id=1, conta_id=banco.id, data=dia, historico=f'Movimento {i}',
                valor=valor, origem_importacao=origem, criado_em=criado_em))
        session.commit()
        saldo = sum(session.scalars(select(LancamentoBanco.valor).where(
            LancamentoBanco.empresa_id == 1,
            app.filtro_banco_efetivado(date(2026, 11, 20)),
        )).all())
        assert saldo == 590


def test_dados_do_extrato_preservados():
    assert app.parse_data_banco('23/11/2026') == date(2026, 11, 23)
    resumo = app.resumo_banco_data_contabil_adiantada([
        (date(2026, 11, 23), 300),
        (date(2026, 11, 23), -50),
    ], date(2026, 11, 20))
    assert resumo['quantidade'] == 2
    assert resumo['liquido'] == 250
    assert 'data=r["data"]' in __import__('inspect').getsource(app.financeiro_importar_extrato)


def test_apresentacao_nao_marca_importado_real_como_projecao():
    fonte = Path('templates/admin/financeiro.html').read_text(encoding='utf-8')
    assert 'Extrato já considerado no saldo' in fonte
    assert 'Extrato efetivo' in fonte
    assert 'Projeção, não saldo disponível' not in fonte
    assert 'resumo_banco_futuros' not in fonte
