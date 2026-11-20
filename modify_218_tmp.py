from pathlib import Path
p=Path('/mnt/data/finance_issue_check')
app=p/'app.py'
s=app.read_text(encoding='utf8')
s=s.replace('from datetime import datetime, date, time, timedelta, timezone','from datetime import datetime, date, time, timedelta, timezone\nfrom zoneinfo import ZoneInfo',1)
needle='def parse_valor_banco(valor) -> float:\n'
repl='''def hoje_financeiro_brasil() -> date:
    """Data de referência operacional no fuso da empresa (RJ/Brasil)."""
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date()


def resumo_lancamentos_futuros_banco(registros, hoje: date) -> dict:
    """Mostra importações pós-hoje sem transformá-las em saldo já realizado.

    Recebe (data, valor). As datas permanecem as datas originais do extrato.
    """
    futuros = [(dia, float(valor or 0)) for dia, valor in registros if dia and dia > hoje]
    return {
        "quantidade": len(futuros),
        "entradas": round(sum(valor for _, valor in futuros if valor > 0), 2),
        "saidas": round(sum(-valor for _, valor in futuros if valor < 0), 2),
        "liquido": round(sum(valor for _, valor in futuros), 2),
        "primeira_data": min((dia for dia, _ in futuros), default=None),
        "ultima_data": max((dia for dia, _ in futuros), default=None),
    }


'''+needle
assert needle in s
s=s.replace(needle,repl,1)
start=s.index('@app.get("/painel/financeiro", response_class=HTMLResponse)')
end=s.index('@app.post("/painel/financeiro', start)
part=s[start:end]
assert part.count('hoje = date.today()') >= 2,part.count('hoje = date.today()')
part=part.replace('hoje = date.today()','hoje = hoje_financeiro_brasil()',2)
needle='''    saldo_banco = saldo_real_conta(conta)
    saldo_todos = sum(saldo_real_conta(c) for c in contas if c.ativa)
'''
assert needle in part
insert=needle+'''
    # Movimentos importados com data futura são visíveis no Financeiro, mas
    # não devem alterar o saldo disponível do Banco Principal antes da data.
    # O saldo acima é acumulado por ano civil; manter o mesmo limite aqui.
    futuros_banco_q = db.query(LancamentoBanco.data, LancamentoBanco.valor).filter(
        LancamentoBanco.empresa_id == empresa.id,
        LancamentoBanco.data > hoje,
        LancamentoBanco.data <= date(hoje.year, 12, 31),
    )
    if conta:
        futuros_banco_q = futuros_banco_q.filter(LancamentoBanco.conta_id == conta.id)
    resumo_banco_futuros = resumo_lancamentos_futuros_banco(futuros_banco_q.all(), hoje)
    saldo_banco_com_futuros = round(saldo_banco + resumo_banco_futuros["liquido"], 2)
'''
part=part.replace(needle,insert,1)
needle='''        "saldo_previsto": saldo_previsto, "saldo_banco": saldo_banco, "saldo_todos": saldo_todos,
'''
assert needle in part
part=part.replace(needle,needle+'''        "resumo_banco_futuros": resumo_banco_futuros, "saldo_banco_com_futuros": saldo_banco_com_futuros,
''',1)
s=s[:start]+part+s[end:]
app.write_text(s,encoding='utf8')

p2=p/'templates/admin/financeiro.html'
t=p2.read_text(encoding='utf8')
needle='''        <div><small>{{ conta.nome if conta else 'Banco selecionado' }}</small><b>R$ {{ saldo_banco|moeda_br }}</b><em>Saldo do banco selecionado para conferência</em></div>
'''
assert needle in t
t=t.replace(needle,'''        <div><small>{{ conta.nome if conta else 'Banco selecionado' }} — até hoje</small><b>R$ {{ saldo_banco|moeda_br }}</b><em>Movimentos registrados até {{ hoje.strftime('%d/%m/%Y') }} (ano atual)</em></div>
''',1)
needle='''      <div class="indicador-card indicador-banco indicador-banco-total">
'''
assert needle in t
t=t.replace(needle,'''      {% if resumo_banco_futuros.quantidade %}
      <div class="indicador-card indicador-banco-futuro">
        <span class="indicador-icone"><i class="bi bi-calendar-event" aria-hidden="true"></i></span>
        <div>
          <small>Com lançamentos futuros do extrato</small>
          <b>R$ {{ saldo_banco_com_futuros|moeda_br }}</b>
          <em>{{ resumo_banco_futuros.quantidade }} lançamento(s) após hoje, até {{ resumo_banco_futuros.ultima_data.strftime('%d/%m/%Y') }}. Projeção, não saldo disponível.</em>
        </div>
      </div>
      {% endif %}
'''+needle,1)
needle='''  <div class="financeiro-acoes-faixa">
'''
assert needle in t
t=t.replace(needle,'''  {% if resumo_banco_futuros.quantidade %}
  <div class="financeiro-alerta" role="status">
    <i class="bi bi-info-circle" aria-hidden="true"></i>
    <b>Atenção às datas do extrato:</b>
    {{ resumo_banco_futuros.quantidade }} lançamento(s) do {{ conta.nome if conta else 'banco' }}
    estão datados depois de hoje ({{ hoje.strftime('%d/%m/%Y') }}), entre
    {{ resumo_banco_futuros.primeira_data.strftime('%d/%m') }} e
    {{ resumo_banco_futuros.ultima_data.strftime('%d/%m') }}.
    Entradas R$ {{ resumo_banco_futuros.entradas|moeda_br }};
    saídas R$ {{ resumo_banco_futuros.saidas|moeda_br }}.
    Eles aparecem na lista e nos totais mensais, mas não no saldo disponível até a data bancária informada.
    Confira se a data {{ resumo_banco_futuros.primeira_data.strftime('%d/%m') }} é a data efetiva ou a data futura indicada pelo banco.
  </div>
  {% endif %}
'''+needle,1)
needle='''          <tr class="{{ 'linha-vinculada' if l.pagamento or l.organiza_lancamento_id or vinculos_por_banco.get(l.id) or vinculos_titulo_por_banco.get(l.id) or vinculos_organiza_por_banco.get(l.id) else '' }}">
            <td>{{ l.data.strftime('%d/%m') }}</td>
'''
assert needle in t
repl='''          <tr class="{{ 'linha-vinculada' if l.pagamento or l.organiza_lancamento_id or vinculos_por_banco.get(l.id) or vinculos_titulo_por_banco.get(l.id) or vinculos_organiza_por_banco.get(l.id) else '' }}"{% if l.data > hoje %} title="Data futura no extrato; não entra no saldo até hoje"{% endif %}>
            <td>{{ l.data.strftime('%d/%m') }}{% if l.data > hoje %} <small title="Data futura no extrato" style="display:block;font-size:0.72em;white-space:nowrap;">Previsto</small>{% endif %}</td>
'''
t=t.replace(needle,repl,1)
p2.write_text(t,encoding='utf8')

p3=p/'config.py'
s3=p3.read_text(encoding='utf8'); assert 'APP_VERSION = "1.0.217"' in s3
p3.write_text(s3.replace('APP_VERSION = "1.0.217"','APP_VERSION = "1.0.218"',1),encoding='utf8')

(p/'ALTERACAO_FINANCEIRO_DATAS_BANCO_1.0.218.md').write_text('''# Conect 1.0.218 – datas futuras no Banco Principal

## Diagnóstico
O importador de CSV/XLSX mantém a data informada na coluna Data do extrato. Em 20/11/2026, movimentos datados de 23/11/2026 ficam fora do indicador de saldo bancário **até hoje**, por causa do filtro `LancamentoBanco.data <= hoje`. Eles já participam dos totais mensais de novembro, porque estes consideram o mês completo.

## Alterações
- No resumo financeiro, o saldo do banco fica explicitamente rotulado como **até hoje**.
- Um segundo indicador aparece quando existem lançamentos de data futura importados: **Com lançamentos futuros do extrato**. Ele mostra o saldo do banco calculado incluindo essas importações, e sinaliza que é **projeção, não saldo disponível**.
- Um alerta informa o número de movimentos futuros, o período e totais de entradas/saídas.
- A tabela do banco marca cada data futura como **Previsto**.
- A data de referência do Financeiro passa a usar `America/Sao_Paulo`, inclusive no corte de saldo. Não modifica datas gravadas.
- A projeção considera o ano civil atual, pois o saldo existente também é calculado somente a partir de 1º de janeiro, sem saldo inicial.

## Preservações
- Nenhum registro bancário é alterado ou excluído.
- A importação e a prevenção de duplicidades não mudam.
- O saldo disponível até hoje não incorpora transações futuras.
- O balanço mensal, contas a pagar, a receber e conciliações mantêm a lógica anterior.

## Conferência importante
Se o extrato bancário **realmente informa 23/11**, o Conect não deve converter essa data automaticamente para 20/11. Se essa for uma data errada no arquivo original, investigue a origem antes de reimportar; a identificação de duplicidades considera a data, de modo que uma importação corrigida pode gerar movimentos duplicados se os registros anteriores não forem tratados adequadamente.
''',encoding='utf8')

(p/'test_financeiro_datas_banco_218.py').write_text('''"""Cobertura da transparência sobre datas futuras do Banco Principal."""
from datetime import date
from pathlib import Path
import inspect
import app


def test_futuros_sao_separados_do_saldo_ate_hoje():
    resumo = app.resumo_lancamentos_futuros_banco([
        (date(2026, 11, 19), 150.0),
        (date(2026, 11, 20), 200.0),
        (date(2026, 11, 23), 300.0),
        (date(2026, 11, 23), -45.25),
        (date(2026, 11, 24), -10.0),
    ], date(2026, 11, 20))
    assert resumo == {
        "quantidade": 3,
        "entradas": 300.0,
        "saidas": 55.25,
        "liquido": 244.75,
        "primeira_data": date(2026, 11, 23),
        "ultima_data": date(2026, 11, 24),
    }


def test_sem_futuros_nao_mostra_valor_projetado():
    resumo = app.resumo_lancamentos_futuros_banco([
        (date(2026, 11, 19), 50),
        (date(2026, 11, 20), 0),
    ], date(2026, 11, 20))
    assert resumo["quantidade"] == 0
    assert resumo["liquido"] == 0
    assert resumo["primeira_data"] is None


def test_extrato_nao_troca_data_de_origem():
    assert app.parse_data_banco('23/11/2026') == date(2026, 11, 23)
    assert 'data=r["data"]' in inspect.getsource(app.financeiro_importar_extrato)


def test_o_saldo_disponivel_ainda_exclui_futuros():
    fonte = inspect.getsource(app.financeiro)
    assert 'LancamentoBanco.data <= corte_banco' in fonte
    assert 'LancamentoBanco.data > hoje' in fonte
    assert 'saldo_banco_com_futuros' in fonte
    assert 'LancamentoBanco.data <= mes_cards_fim' in fonte


def test_template_distingue_saldo_futuro_de_saldo_disponivel():
    html = Path('templates/admin/financeiro.html').read_text(encoding='utf-8')
    assert 'até hoje' in html
    assert 'Com lançamentos futuros do extrato' in html
    assert 'Projeção, não saldo disponível' in html
    assert '>Previsto</small>' in html
''', encoding='utf8')
print('ok modifications')
