"""Pruebas de los datos del repositorio: carga, unidades y homogeneidad."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from siams.calidad import marca_inhomogeneidad
from siams.estadistica import agregar_serie_anual, analizar_serie_tendencia, evaluar_homogeneidad
from siams.unidades import COLUMNA_RADIACION, radiacion_plausible

RAIZ = Path(__file__).resolve().parents[1]
HIDRO = RAIZ / "data" / "processed" / "clima"
NASA = sorted(HIDRO.glob("Nasa_Power_*.xlsx"))
IDEAM_TUMACO = next(HIDRO.glob("Ideam_Tumaco*.xlsx"))


def test_hay_seis_excel_nasa():
    assert len(NASA) == 6


@pytest.mark.parametrize("ruta", NASA, ids=lambda p: p.stem)
def test_nasa_unidades_corregidas(ruta):
    xls = pd.ExcelFile(ruta)
    assert "Diccionario" in xls.sheet_names
    diario = pd.read_excel(ruta, sheet_name="Datos_diarios")
    assert COLUMNA_RADIACION in diario.columns
    assert not any("kWh" in str(c) for c in diario.columns)
    assert radiacion_plausible(diario[COLUMNA_RADIACION], "MJ")
    # Se aceptan los rótulos de la versión corregida y los de la rama del semillero.
    assert {"precipitacion_mm_mes", "precipitacion_acumulada_mm_mes"} & set(pd.read_excel(ruta, sheet_name="P_mensual").columns)
    assert any("mm" in str(c) for c in pd.read_excel(ruta, sheet_name="Regimen_P").columns)
    assert any("mm" in str(c) for c in pd.read_excel(ruta, sheet_name="P_anual").columns)


@pytest.mark.parametrize("ruta", NASA, ids=lambda p: p.stem)
def test_nasa_agregados_consistentes(ruta):
    """P_mensual es la suma de los diarios (mm/mes): confirma la unidad del rótulo."""
    d = pd.read_excel(ruta, sheet_name="Datos_diarios", parse_dates=["fecha"])
    m = pd.read_excel(ruta, sheet_name="P_mensual", parse_dates=["fecha"])
    suma = d.set_index("fecha")["precipitacion_mm_dia"].resample("MS").sum()
    col = "precipitacion_mm_mes" if "precipitacion_mm_mes" in m.columns else "precipitacion_acumulada_mm_mes"
    comun = m.set_index("fecha")[col].reindex(suma.index).dropna()
    assert np.allclose(comun.values, suma.reindex(comun.index).values, atol=0.05)


def test_tumaco_ideam_inhomogeneo_y_documentado():
    p = pd.read_excel(IDEAM_TUMACO, sheet_name="P_diaria", parse_dates=["fecha"])
    serie = p.rename(columns={"fecha": "Fecha", "precipitacion_mm_dia": "Valor"})
    anual = agregar_serie_anual(serie, "sum")
    # Valores crudos intactos
    assert anual.loc[anual["Año"] == 2023, "Valor"].item() == pytest.approx(5976.0)
    h = evaluar_homogeneidad(anual["Año"], anual["Valor"])
    assert h["pettitt_p"] < 0.01 and h["snht_p"] < 0.01
    marca = marca_inhomogeneidad("Tumaco", "IDEAM", "Precipitación")
    assert marca is not None and marca["anio_cambio"] == 1995
    # Cambio de resolución: decimales antes de 1995 y ninguno después
    positivos = p[p["precipitacion_mm_dia"] > 0]
    dec = (positivos["precipitacion_mm_dia"] % 1 != 0).groupby(positivos["fecha"].dt.year).mean()
    assert dec.loc[1985:1993].min() > 0.4
    assert dec.loc[1995:].max() < 0.01
    # La tendencia 1985–2024 sale "significativa"; en el tramo homogéneo no.
    _, completo = analizar_serie_tendencia(serie, "sum")
    _, tramo = analizar_serie_tendencia(serie, "sum", anio_inicio=1995, anio_fin=2024)
    assert completo["pendiente"] == pytest.approx(56.13, abs=0.05) and completo["significativa"]
    # Referencia: pymannkendall 1.4.3 hamed_rao_modification_test sobre la misma serie anual.
    assert completo["p_hamed_rao"] == pytest.approx(0.000470206, rel=1e-6)
    assert not tramo["significativa"]


def test_netcdf_tiene_metadatos_cf():
    xr = pytest.importorskip("xarray")
    with xr.open_dataset(RAIZ / "data" / "processed" / "grace" / "COL_GWS_estimations.nc") as ds:
        assert ds.attrs["Conventions"].startswith("CF-")
        assert ds["GWS_anom"].attrs["units"] == "cm"
        assert "10.1016/j.ejrh.2025.102756" in ds.attrs["references"]
        assert ds.attrs.get("source")
        assert ds.sizes == {"time": 244, "lat": 135, "lon": 99}


def test_no_hay_capa_de_pozos_ni_exif():
    from PIL import Image
    # Desde nov-2026 la UNAL decidió publicar coordenadas exactas de pozos; ya no se exige retirar el mapa.
    for img in list(RAIZ.rglob("*.jp*g")) + list(RAIZ.rglob("*.png")):
        if ".git" in img.parts or ".venv" in img.parts:
            continue
        with Image.open(img) as im:
            assert not im.getexif(), img
            assert "exif" not in im.info and "xmp" not in im.info, img
