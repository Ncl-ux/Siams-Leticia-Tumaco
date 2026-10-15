"""Pruebas de regresión para el SIAMS modular con archivos temporales."""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

# Las pruebas funcionales corren en CI (que instala requirements.txt).
# Al ejecutar este test sin Streamlit, se omiten estas pruebas, pero las
# comprobaciones de sintaxis/estructura continúan en test_estructura.py.
pytest.importorskip("streamlit", reason="Instala las dependencias con requirements.txt")


@pytest.mark.parametrize("nombre", [
    "cartografia", "catalogo", "clima", "componentes", "estados", "estilos",
    "grace", "inicio", "landsat", "mapas_datos", "mapbiomas", "sentinel",
    "swot", "tendencias", "utilidades",
])
def test_importar_modulo(nombre):
    modulo = importlib.import_module(f"siams.{nombre}")
    assert modulo is not None


def test_territorios_y_datos_basicos():
    from siams.catalogo import TERRITORIOS, ESTADO_COMPONENTES
    esperado = {"Bogotá", "Leticia", "Tumaco", "Medellín", "San Andrés", "Arauca", "La Paz"}
    assert set(TERRITORIOS) == esperado
    assert set(ESTADO_COMPONENTES) == esperado
    for sede, registro in TERRITORIOS.items():
        assert -90 <= float(registro["lat"]) <= 90, sede
        assert -180 <= float(registro["lon"]) <= 180, sede


@pytest.mark.parametrize("entrada,esperado", [
    ("Medellín", "medellin"),
    ("LA PAZ", "la_paz"),
    ("San Andrés Costa", "san_andres_costa"),
])
def test_normalizar_etiqueta(entrada, esperado):
    from siams.utilidades import normalizar_etiqueta
    assert normalizar_etiqueta(entrada) == esperado


@pytest.mark.parametrize("sede,fuente,nombre", [
    ("Tumaco", "nasa", "nasa_power_tumaco.xlsx"),
    ("Tumaco", "ideam", "analisis_hidrometeorologico_tumaco.xlsx"),
    ("Arauca", "ideam", "ideam_arauca.xlsx"),
    ("Leticia", "nasa", "nasa_power_leticia.xlsx"),
    ("Medellín", "nasa", "nasa_power_medellin.xlsx"),
    ("San Andrés", "nasa", "nasa_power_san_andres.xlsx"),
    ("La Paz", "nasa", "nasa_power_la_paz.xlsx"),
])
def test_busqueda_archivos_climaticos(tmp_path, monkeypatch, sede, fuente, nombre):
    from siams import utilidades
    carpeta = tmp_path / "Datos_Climaticos"
    carpeta.mkdir()
    archivo = carpeta / nombre
    archivo.write_bytes(b"archivo de prueba")
    monkeypatch.setattr(utilidades, "CARPETA_PROYECTO", tmp_path)
    monkeypatch.setattr(utilidades, "CARPETA_DATOS_HIDRO", carpeta)
    assert utilidades.buscar_excel_climatico(sede, fuente) == archivo
    assert utilidades.buscar_excel_climatico("Bogotá", fuente) is None


def test_fuentes_climaticas_no_se_confunden(tmp_path, monkeypatch):
    from siams import utilidades
    carpeta = tmp_path / "Datos_Climaticos"
    carpeta.mkdir()
    (carpeta / "nasa_power_tumaco.xlsx").touch()
    monkeypatch.setattr(utilidades, "CARPETA_PROYECTO", tmp_path)
    monkeypatch.setattr(utilidades, "CARPETA_DATOS_HIDRO", carpeta)
    assert utilidades.buscar_excel_climatico("Tumaco", "ideam") is None
    assert utilidades.buscar_excel_climatico("Arauca", "nasa") is None


def test_swot_rosario_y_mira_separados(tmp_path, monkeypatch):
    from siams import swot
    mira = tmp_path / "swot_tumaco_mira_ancho.gif"
    rosario = tmp_path / "swot_tumaco_rosario_ancho.gif"
    mira.touch()
    rosario.touch()
    monkeypatch.setattr(swot, "CARPETA_GIFS", tmp_path)
    assert swot.buscar_gif_swot(mira.name) == mira
    assert swot.buscar_gif_swot(rosario.name) == rosario


def test_mapbiomas_gifs_por_nivel(tmp_path, monkeypatch):
    from siams import mapbiomas
    carpeta_sede = tmp_path / "Arauca"
    carpeta_sede.mkdir()
    gifs = mapbiomas.MAPBIOMAS_GIFS_POR_TERRITORIO["Arauca"]
    rutas = {}
    for tipo, nombre in gifs.items():
        ruta = carpeta_sede / nombre
        ruta.touch()
        rutas[tipo] = ruta
    monkeypatch.setattr(mapbiomas, "CARPETA_COBERTURAS", tmp_path)
    assert len(set(gifs.values())) == 3
    for tipo, nombre in gifs.items():
        assert mapbiomas.buscar_gif_mapbiomas("Arauca", nombre) == rutas[tipo]


def test_mapbiomas_isla_y_costa_separados(tmp_path, monkeypatch):
    from siams import mapbiomas
    carpeta_sede = tmp_path / "San_Andres"
    carpeta_sede.mkdir()
    (carpeta_sede / "mapbiomas_serie_temporal_cobertura_1985-2024_sa.csv").touch()
    (carpeta_sede / "mapbiomas_serie_temporal_cobertura_1985-2024_sac.csv").touch()
    monkeypatch.setattr(mapbiomas, "CARPETA_COBERTURAS", tmp_path)
    sa = mapbiomas.encontrar_csv_coberturas("San Andrés", "SA")
    sac = mapbiomas.encontrar_csv_coberturas("San Andrés", "SAC")
    assert len(sa["serie"]) == 1
    assert len(sac["serie"]) == 1
    assert sa["serie"][0] != sac["serie"][0]


def test_landsat_inventario(tmp_path, monkeypatch):
    from siams import landsat
    sede = tmp_path / "Tumaco"
    sede.mkdir()
    (sede / "Areas_coberturas_por_fecha.csv").touch()
    (sede / "Control_escenas.csv").touch()
    (sede / "GIF_Landsat_Tumaco_2024.gif").touch()
    monkeypatch.setattr(landsat, "CARPETA_LANDSAT", tmp_path)
    inv = landsat.inventario_landsat("Tumaco")
    assert inv["carpeta"] == sede
    assert len(inv["gifs"]) == 1
    assert inv["areas"] and inv["control"]
    assert landsat.anio_gif_landsat(inv["gifs"][0]) == 2024


def test_sentinel_indices(tmp_path, monkeypatch):
    from siams import sentinel
    sede = tmp_path / "Leticia"
    sede.mkdir()
    for nombre in ("animacion_ndvi_2025_leticia.gif", "animacion_mndwi_2025_leticia.gif", "animacion_scl_2025_leticia.gif"):
        (sede / nombre).touch()
    monkeypatch.setattr(sentinel, "CARPETA_SENTINEL", tmp_path)
    encontrado = sentinel.buscar_animaciones_sentinel("Leticia")
    assert 2025 in encontrado
    assert set(encontrado[2025]) == {"NDVI", "MNDWI", "SCL"}
