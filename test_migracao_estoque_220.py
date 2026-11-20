"""Regressão do erro 500: novas colunas do estoque devem migrar no startup normal."""
import ast
from pathlib import Path


def _migracoes_inicio_critico():
    arvore = ast.parse((Path(__file__).parent / "app.py").read_text(encoding="utf-8"))
    funcao = next(node for node in arvore.body if isinstance(node, ast.FunctionDef) and node.name == "_garantir_colunas_v113_criticas")
    atribuicao = next(node for node in funcao.body if isinstance(node, ast.Assign) and any(isinstance(alvo, ast.Name) and alvo.id == "comandos_pg" for alvo in node.targets))
    return ast.literal_eval(atribuicao.value)


def test_novas_colunas_migradas_no_startup_normal():
    comandos = _migracoes_inicio_critico()
    esperado = {
        "produtos_servicos": "eh_combo",
        "itens_produto_servico_estoque": "tipo",
    }
    for tabela, coluna in esperado.items():
        cmds = [cmd for cmd in comandos if f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS {coluna} " in cmd]
        assert len(cmds) == 1, f"migração crítica ausente para {tabela}.{coluna}"
    assert not any("exigir_recurso_principal" in c for c in comandos), "regra antiga foi descontinuada"
    assert any("eh_combo BOOLEAN NOT NULL DEFAULT false" in c for c in comandos)
    assert any("tipo VARCHAR(20) NOT NULL DEFAULT 'acessorio'" in c for c in comandos)


def test_startup_normal_invoca_migracao_critica_antes_da_manutencao_opcional():
    arvore = ast.parse((Path(__file__).parent / "app.py").read_text(encoding="utf-8"))
    startup = next(node for node in arvore.body if isinstance(node, ast.FunctionDef) and node.name == "startup")
    chamada_critica = [node for node in ast.walk(startup) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_garantir_colunas_v113_criticas"]
    assert chamada_critica
    chamada = chamada_critica[0]
    verificacao_manutencao = next(node for node in ast.walk(startup) if isinstance(node, ast.If) and any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "_startup_manutencao_habilitada" for c in ast.walk(node.test)))
    assert chamada.lineno < verificacao_manutencao.lineno


def test_tabela_multiplos_principais_criada_no_startup_normal():
    codigo = (Path(__file__).parent / "app.py").read_text(encoding="utf-8")
    inicio = codigo.index("def _garantir_colunas_v113_criticas()")
    fim = codigo.index("\ndef ", inicio+4)
    bloco = codigo[inicio:fim]
    assert "CREATE TABLE IF NOT EXISTS combo_produtos_principais" in bloco
    assert "uq_combo_produto_principal" in bloco
