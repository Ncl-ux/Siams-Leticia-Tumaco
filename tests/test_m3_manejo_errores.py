"""M3: los errores no pueden desaparecer mediante except: pass.

Estas pruebas inspeccionan la estructura del código y no necesitan datos reales.
"""
from __future__ import annotations

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVOS = (
    "app.py",
    "siams/inicio.py",
    "siams/clima.py",
    "siams/hidrogeoquimica_datos.py",
    "siams/cartografia.py",
)


def test_m3_no_hay_except_pass_en_archivos_intervenidos():
    encontrados = []
    for nombre in ARCHIVOS:
        tree = ast.parse((RAIZ / nombre).read_text(encoding="utf-8"))
        for nodo in ast.walk(tree):
            if isinstance(nodo, ast.ExceptHandler) and any(
                isinstance(sentencia, ast.Pass) for sentencia in nodo.body
            ):
                encontrados.append(f"{nombre}:{nodo.lineno}")
    assert not encontrados, "Errores ignorados con pass: " + ", ".join(encontrados)


def test_m3_registro_y_avisos_visibles():
    fuentes = {
        nombre: (RAIZ / nombre).read_text(encoding="utf-8")
        for nombre in ARCHIVOS
    }
    for nombre, contenido in fuentes.items():
        assert "logging.getLogger(__name__)" in contenido, nombre
        assert "logger.exception(" in contenido or "logger.warning(" in contenido, nombre
    for nombre in ("app.py", "siams/clima.py", "siams/inicio.py"):
        assert "st.warning(" in fuentes[nombre], nombre
    assert '"Carbonatos no calculables"' in fuentes["siams/hidrogeoquimica_datos.py"]
    assert '"Balance iónico no calculable"' in fuentes["siams/hidrogeoquimica_datos.py"]
    assert "fallo_visor_nativo" in fuentes["siams/cartografia.py"]
    assert "st.caption(" in fuentes["siams/cartografia.py"]
