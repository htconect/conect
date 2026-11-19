"""Regressões da navegação para WhatsApp e do loading global (1.0.215)."""
from pathlib import Path
import re
import shutil
import subprocess
import pytest

ROOT = Path(__file__).parent
ADMIN = (ROOT / "templates/base.html").read_text(encoding="utf-8")
PUBLIC = (ROOT / "templates/publico/base_cliente.html").read_text(encoding="utf-8")
VITRINE = (ROOT / "templates/publico/vitrine.html").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def _script_contendo(html, texto):
    for bloco in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, re.DOTALL):
        if texto in bloco:
            return bloco
    raise AssertionError(f"Script com {texto!r} não encontrado")


def test_links_nao_abrem_overlay_global():
    script = _script_contendo(ADMIN, "window.mostrarCarregando = mostrarCarregando")
    assert 'document.addEventListener("click"' not in script
    assert 'mostrarCarregando(link.dataset.loadingTitle' not in script
    assert 'document.addEventListener("submit"' in script


def test_whatsapp_permanece_redirecionamento_no_backend():
    for rota in ["/whatsapp\")", "/whatsapp-contrato\")", "/whatsapp-opcionais\")"]:
        assert rota in APP
    assert 'f"https://wa.me/{telefone}?text={quote(texto)}"' in APP


def test_retorno_iOS_e_timeout_admin():
    script = _script_contendo(ADMIN, "window.mostrarCarregando = mostrarCarregando")
    assert 'window.addEventListener("focus"' in script
    assert 'window.addEventListener("pagehide"' in script
    assert 'document.addEventListener("visibilitychange"' in script
    assert '15000' in script
    assert 'destino.toLowerCase() !== "_self"' in script


def test_retorno_iOS_e_timeout_cliente():
    script = _script_contendo(PUBLIC, "window.mostrarCarregando=function")
    assert "window.addEventListener('focus'" in script
    assert "window.addEventListener('pagehide'" in script
    assert "document.addEventListener('visibilitychange'" in script
    assert '15000' in script
    assert 'loadingStatusUrl' in script


def test_compartilhar_vitrine_nao_abre_aba_em_branco():
    script = _script_contendo(VITRINE, "abaWhatsApp") if "abaWhatsApp" in VITRINE else VITRINE
    assert "window.open('about:blank'" not in script
    assert 'window.location.assign(whatsapp)' in script


def test_javascript_global_tem_sintaxe_valida():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js não disponível')
    for texto, alvo in [(ADMIN, "window.mostrarCarregando = mostrarCarregando"), (PUBLIC, "window.mostrarCarregando=function")]:
        script = _script_contendo(texto, alvo)
        proc = subprocess.run([node, '--check'], input=script, text=True, capture_output=True, check=False)
        assert proc.returncode == 0, proc.stderr
