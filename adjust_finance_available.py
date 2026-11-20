from pathlib import Path
p=Path('/mnt/data/finance_issue_check/app.py')
s=p.read_text(encoding='utf-8')
start=s.index('def resumo_lancamentos_futuros_banco(')
end=s.index('\ndef parse_valor_banco',start)
s=s[:start]+'''def proximo_dia_util_bancario(referencia: date) -> date:
    """Próximo dia útil da semana; não confunde extrato com data de pagamento agendado.

    A data contábil do arquivo continua intacta. O fallback atende, por exemplo,
    ao extrato de 20/11/2026 que registra movimentos efetivos em 23/11/2026.
    """
    candidato = referencia + timedelta(days=1)
    while candidato.weekday() >= 5:
        candidato += timedelta(days=1)
    return candidato


def filtro_banco_efetivado(ate_data: date):
    """Inclui importações do extrato efetivo com data do próximo dia útil.

    A importação do Banco Principal é de movimentos do extrato, não de
    pagamentos agendados. Para evitar antecipações arbitrárias, a tolerância é
    limitada ao próximo dia útil e a importações feitas até a data de corte.
    """
    limite = proximo_dia_util_bancario(ate_data)
    return or_(
        LancamentoBanco.data <= ate_data,
        and_(
            LancamentoBanco.origem_importacao.isnot(None),
            LancamentoBanco.data > ate_data,
            LancamentoBanco.data <= limite,
            func.date(LancamentoBanco.criado_em) <= ate_data.isoformat(),
        ),
    )


def resumo_banco_data_contabil_adiantada(registros, hoje: date) -> dict:
    """Informa os itens de extrato incluídos no saldo antes da data contábil."""
    limite = proximo_dia_util_bancario(hoje)
    antecipados = [(dia, float(valor or 0)) for dia, valor in registros if dia and hoje < dia <= limite]
    return {
        'quantidade': len(antecipados),
        'entradas': round(sum(v for _, v in antecipados if v > 0), 2),
        'saidas': round(sum(-v for _, v in antecipados if v < 0), 2),
        'liquido': round(sum(v for _, v in antecipados), 2),
        'primeira_data': min((dia for dia, _ in antecipados), default=None),
        'ultima_data': max((dia for dia, _ in antecipados), default=None),
    }

''' + s[end:]
s=s.replace('''            LancamentoBanco.data <= corte_banco,
        ).group_by(LancamentoBanco.conta_id).all()''','''            filtro_banco_efetivado(corte_banco),
        ).group_by(LancamentoBanco.conta_id).all()''',1)
start=s.index('    # Movimentos importados com data futura são visíveis no Financeiro, mas')
end=s.index('    # Relatório mensal por semana calculado em memória',start)
s=s[:start]+'''    # Quando o extrato do Banco Principal já trouxe movimentos realizados,
    # a data contábil do próximo dia útil NÃO impede seu reflexo no saldo.
    # Permanecem fora movimentos manuais futuros e datas posteriores ao próximo
    # dia útil (que poderiam ser agendamentos).
    limite_data_bancaria = proximo_dia_util_bancario(hoje)
    contabilizados_antecipadamente_q = db.query(
        LancamentoBanco.data, LancamentoBanco.valor,
    ).filter(
        LancamentoBanco.empresa_id == empresa.id,
        LancamentoBanco.origem_importacao.isnot(None),
        LancamentoBanco.data > hoje,
        LancamentoBanco.data <= limite_data_bancaria,
        func.date(LancamentoBanco.criado_em) <= hoje.isoformat(),
    )
    if conta:
        contabilizados_antecipadamente_q = contabilizados_antecipadamente_q.filter(
            LancamentoBanco.conta_id == conta.id)
    resumo_banco_antecipado = resumo_banco_data_contabil_adiantada(
        contabilizados_antecipadamente_q.all(), hoje)

''' + s[end:]
s=s.replace('''        "resumo_banco_futuros": resumo_banco_futuros, "saldo_banco_com_futuros": saldo_banco_com_futuros,''','''        "resumo_banco_antecipado": resumo_banco_antecipado,
        "limite_data_bancaria": limite_data_bancaria,''')
s=s.replace('''    hoje = date.today()
    ate_data = ate_data or hoje
''','''    hoje = hoje_financeiro_brasil()
    ate_data = ate_data or hoje
''',1)
s=s.replace('''            LancamentoBanco.data <= corte_banco,
        ).scalar() or 0)''','''            filtro_banco_efetivado(corte_banco),
        ).scalar() or 0)''',1)
p.write_text(s,encoding='utf-8')
p=Path('/mnt/data/finance_issue_check/templates/admin/financeiro.html'); t=p.read_text(encoding='utf-8')
t=t.replace("{{ conta.nome if conta else 'Banco selecionado' }} — até hoje", "{{ conta.nome if conta else 'Banco selecionado' }} — saldo até hoje")
t=t.replace('Movimentos registrados até {{ hoje.strftime(\'%d/%m/%Y\') }} (ano atual)', 'Movimentos efetivos importados + movimentos anteriores a {{ hoje.strftime(\'%d/%m/%Y\') }}')
start=t.index('      {% if resumo_banco_futuros.quantidade %}')
end=t.index('      <div class="indicador-card indicador-banco indicador-banco-total">', start)
t=t[:start]+t[end:]
start=t.index('  {% if resumo_banco_futuros.quantidade %}')
end=t.index('  <div class="financeiro-acoes-faixa">',start)
t=t[:start]+'''  {% if resumo_banco_antecipado.quantidade %}
  <div class="financeiro-alerta" role="status">
    <i class="bi bi-check-circle" aria-hidden="true"></i>
    <b>Extrato já considerado no saldo:</b>
    {{ resumo_banco_antecipado.quantidade }} movimento(s) importado(s)
    com data contábil de {{ resumo_banco_antecipado.primeira_data.strftime('%d/%m/%Y') }}
    {% if resumo_banco_antecipado.ultima_data != resumo_banco_antecipado.primeira_data %}até {{ resumo_banco_antecipado.ultima_data.strftime('%d/%m/%Y') }}{% endif %}
    estão incluídos no saldo atual porque constam no extrato efetivo.
    Entradas R$ {{ resumo_banco_antecipado.entradas|moeda_br }};
    saídas R$ {{ resumo_banco_antecipado.saidas|moeda_br }}.
    A data original do banco foi mantida para conciliação. Pagamentos agendados não devem ser importados como extrato efetivo.
  </div>
  {% endif %}
''' + t[end:]
t=t.replace('''<tr class="{{ 'linha-vinculada' if l.pagamento or l.organiza_lancamento_id or vinculos_por_banco.get(l.id) or vinculos_titulo_por_banco.get(l.id) or vinculos_organiza_por_banco.get(l.id) else '' }}"{% if l.data > hoje %} title="Data futura no extrato; não entra no saldo até hoje"{% endif %}>''','''<tr class="{{ 'linha-vinculada' if l.pagamento or l.organiza_lancamento_id or vinculos_por_banco.get(l.id) or vinculos_titulo_por_banco.get(l.id) or vinculos_organiza_por_banco.get(l.id) else '' }}"{% if l.data > hoje %} title="Data contábil do banco posterior à data atual"{% endif %}>''')
t=t.replace('''<td>{{ l.data.strftime('%d/%m') }}{% if l.data > hoje %} <small title="Data futura no extrato" style="display:block;font-size:0.72em;white-space:nowrap;">Previsto</small>{% endif %}</td>''','''<td>{{ l.data.strftime('%d/%m') }}{% if l.data > hoje %}
              {% if l.origem_importacao and l.data <= limite_data_bancaria and l.criado_em and l.criado_em.date() <= hoje %}
              <small title="Movimento importado já incluído no saldo; data contábil posterior" style="display:block;font-size:0.72em;white-space:nowrap;">Extrato efetivo</small>
              {% else %}
              <small title="Data futura: não contabilizada no saldo disponível" style="display:block;font-size:0.72em;white-space:nowrap;">Data futura</small>
              {% endif %}{% endif %}</td>''')
p.write_text(t,encoding='utf-8')
print('adjusted')
