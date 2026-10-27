"""Verifica que a rota de aceite permite períodos sem recalcular a retirada."""
import ast
from pathlib import Path
source = Path(__file__).with_name('app.py').read_text(encoding='utf-8')
tree = ast.parse(source)
fn = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == 'aceitar_contrato')
assert any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'reserva_periodo' for t in n.targets) for n in ast.walk(fn))
assert any(isinstance(n, ast.If) and isinstance(n.test, ast.UnaryOp) and isinstance(n.test.op, ast.Not) and isinstance(n.test.operand, ast.Name) and n.test.operand.id == 'reserva_periodo' for n in ast.walk(fn))
print('OK: caminho de aceite por período habilitado')
