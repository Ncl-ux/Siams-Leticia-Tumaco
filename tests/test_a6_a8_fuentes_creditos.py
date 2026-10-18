"""Pruebas de integración de A6/A8, sin acceso a datos científicos."""
import ast
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RUTA_MODULO = RAIZ / "siams" / "fuentes_creditos.py"


def _modulo():
    especificacion = importlib.util.spec_from_file_location("fuentes_creditos_test", RUTA_MODULO)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def test_a6_a8_tabla_fuentes_cubre_modulos_clave():
    modulo = _modulo()
    filas = modulo.leer_tabla_csv(modulo.RUTA_PROCEDENCIA, modulo.COLUMNAS_PROCEDENCIA)
    assert len(filas) >= 12
    secciones = [f["Sección de SIAMS"] for f in filas]
    assert len(secciones) == len(set(secciones))
    for clave in ("Clima", "Landsat", "Sentinel-2", "Hidrogeoquímica", "Agua subterránea (GRACE)"):
        assert clave in secciones


def test_a6_a8_identidad_y_autores_no_inventados():
    modulo = _modulo()
    assert modulo.NOMBRE_OFICIAL_SIAMS == "Semillero de Investigación de Aguas y Modelación Subterránea (SIAMS)"
    autores = modulo.leer_tabla_csv(modulo.RUTA_AUTORES, modulo.COLUMNAS_AUTORES)
    assert all(autor["Nombre"] and autor["Rol"] and autor["Afiliación"] for autor in autores)
    assert not any(autor["Nombre"].casefold() == "por confirmar" for autor in autores)


def test_a6_a8_app_integrado_y_compila():
    texto = (RAIZ / "app.py").read_text(encoding="utf-8-sig")
    ast.parse(texto)
    assert "# SIAMS_A6_A8_FUENTES_CREDITOS" in texto
    assert "from siams.fuentes_creditos import" in texto
    assert "with tab_creditos:" in texto
    assert "mostrar_fuentes_y_creditos()" in texto
    assert "mostrar_creditos_institucionales()" in texto


def test_a6_a8_instalador_es_idempotente():
    ruta = RAIZ / "scripts" / "instalar_fuentes_creditos_siams.py"
    spec = importlib.util.spec_from_file_location("siams_instalador_a6a8", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    texto = (RAIZ / "app.py").read_text(encoding="utf-8-sig")
    assert modulo.integrar(texto) == texto
