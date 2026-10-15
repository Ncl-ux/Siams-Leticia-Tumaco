"""Comprobaciones independientes del despliegue, sin leer datos reales."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PAQUETE = RAIZ / "siams"
MODULOS = {
    "cartografia", "catalogo", "clima", "componentes", "estados",
    "estilos", "grace", "inicio", "landsat", "mapas_datos",
    "mapbiomas", "sentinel", "swot", "tendencias", "utilidades",
}


def test_archivo_principal_y_paquete_existen():
    assert (RAIZ / "app.py").is_file()
    assert (PAQUETE / "__init__.py").is_file()
    assert {p.stem for p in PAQUETE.glob("*.py")} >= MODULOS | {"__init__"}


@pytest.mark.parametrize("archivo", [RAIZ / "app.py", *sorted(PAQUETE.glob("*.py"))], ids=lambda p: p.name)
def test_archivos_python_tienen_sintaxis_valida(archivo: Path):
    compile(archivo.read_text(encoding="utf-8-sig"), str(archivo), "exec")


def test_importaciones_relativas_solo_apuntan_a_modulos_existentes():
    """Detecta importaciones erróneas como `from .siams.catalogo import ...`."""
    for archivo in PAQUETE.glob("*.py"):
        tree = ast.parse(archivo.read_text(encoding="utf-8-sig"))
        for nodo in ast.walk(tree):
            if not isinstance(nodo, ast.ImportFrom) or nodo.level == 0:
                continue
            assert nodo.level == 1, f"Importación relativa inesperada en {archivo.name}"
            if nodo.module:
                primero = nodo.module.split(".")[0]
                assert primero in MODULOS, f"Importación no localizada en {archivo.name}: {nodo.module}"


def test_app_importa_modulos_del_paquete():
    arbol = ast.parse((RAIZ / "app.py").read_text(encoding="utf-8-sig"))
    modulos_importados = {
        nodo.module.split(".")[1]
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.ImportFrom) and nodo.level == 0
        and nodo.module and nodo.module.startswith("siams.")
    }
    assert MODULOS.issubset(modulos_importados), f"Módulos sin importación: {MODULOS - modulos_importados}"
