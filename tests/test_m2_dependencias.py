"""M2: comprueba que SIAMS declara versiones exactas y dispone de un lock."""
from pathlib import Path
import re

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVOS = (
    "requirements.txt",
    "requirements_hidrogeoquimica.txt",
    "requirements-dev.txt",
    "requirements-lock.txt",
)
PATRON = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[A-Za-z0-9_,.-]+\])?==([0-9][A-Za-z0-9.!+_-]*)(?:\s*;\s*.+)?$"
)


def _dependencias(nombre):
    ruta = RAIZ / nombre
    assert ruta.is_file(), f"Falta el archivo M2 {nombre}"
    resultado = {}
    for numero, linea in enumerate(ruta.read_text(encoding="utf-8-sig").splitlines(), 1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        m = PATRON.fullmatch(linea)
        assert m is not None, f"{nombre}:{numero}: requisito sin versión exacta: {linea}"
        paquete, version = m.groups()
        clave = re.sub(r"[-_.]+", "-", paquete).lower()
        assert clave not in resultado, f"Duplicado en {nombre}: {paquete}"
        resultado[clave] = version
    assert resultado, f"{nombre}: lista vacía"
    return resultado


def test_m2_todos_los_requisitos_tienen_version_exacta():
    for archivo in ARCHIVOS:
        _dependencias(archivo)


def test_m2_lock_coincide_con_dependencias_directas():
    lock = _dependencias("requirements-lock.txt")
    for nombre in ARCHIVOS[:-1]:
        for paquete, version in _dependencias(nombre).items():
            assert lock.get(paquete) == version, f"{paquete}: {nombre} difiere de lock"


def test_m2_dependencias_antes_omitidas_y_pdf():
    contenido = (RAIZ / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "streamlit[pdf]==" in contenido
    deps = _dependencias("requirements.txt")
    assert "pillow" in deps
    assert "pypdfium2" in deps
    for paquete in ("streamlit", "pandas", "plotly", "numpy", "openpyxl", "xarray", "netcdf4", "pymupdf"):
        assert paquete in deps
