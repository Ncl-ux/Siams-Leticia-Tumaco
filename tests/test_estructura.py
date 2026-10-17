
"""Comprobaciones independientes del despliegue, sin leer datos reales."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PAQUETE = RAIZ / "siams"

# Módulos principales que app.py debe importar directamente.
MODULOS = {
    "cartografia",
    "catalogo",
    "clima",
    "componentes",
    "estados",
    "estilos",
    "grace",
    "inicio",
    "landsat",
    "mapas_datos",
    "mapbiomas",
    "sentinel",
    "swot",
    "tendencias",
    "utilidades",
}


def test_archivo_principal_y_paquete_existen():
    """Verifica que existan app.py y los módulos principales."""
    assert (RAIZ / "app.py").is_file()
    assert (PAQUETE / "__init__.py").is_file()

    modulos_existentes = {
        archivo.stem for archivo in PAQUETE.glob("*.py")
    }

    assert modulos_existentes >= MODULOS | {"__init__"}


@pytest.mark.parametrize(
    "archivo",
    [RAIZ / "app.py", *sorted(PAQUETE.glob("*.py"))],
    ids=lambda p: p.name,
)
def test_archivos_python_tienen_sintaxis_valida(archivo: Path):
    """Comprueba la sintaxis de todos los módulos Python."""
    compile(
        archivo.read_text(encoding="utf-8-sig"),
        str(archivo),
        "exec",
    )


def test_importaciones_relativas_solo_apuntan_a_modulos_existentes():
    """Verifica que las importaciones relativas tengan un archivo real."""
    for archivo in PAQUETE.glob("*.py"):
        tree = ast.parse(
            archivo.read_text(encoding="utf-8-sig")
        )

        for nodo in ast.walk(tree):
            if not isinstance(nodo, ast.ImportFrom):
                continue

            if nodo.level == 0:
                continue

            assert nodo.level == 1, (
                f"Importación relativa inesperada en {archivo.name}"
            )

            if nodo.module:
                ruta_modulo = PAQUETE.joinpath(
                    *nodo.module.split(".")
                )

                existe_modulo = ruta_modulo.with_suffix(".py").is_file()
                existe_paquete = (
                    ruta_modulo / "__init__.py"
                ).is_file()

                assert existe_modulo or existe_paquete, (
                    f"Importación no localizada en "
                    f"{archivo.name}: {nodo.module}"
                )


def test_app_importa_modulos_del_paquete():
    """Verifica que app.py importe los módulos principales de SIAMS."""
    arbol = ast.parse(
        (RAIZ / "app.py").read_text(encoding="utf-8-sig")
    )

    modulos_importados = {
        nodo.module.split(".")[1]
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.ImportFrom)
        and nodo.level == 0
        and nodo.module
        and nodo.module.startswith("siams.")
    }

    faltantes = MODULOS - modulos_importados

    assert not faltantes, (
        f"Módulos principales sin importación: {faltantes}"
    )
