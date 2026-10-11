"""Pruebas de conversión y rangos físicos de unidades."""

import pandas as pd
import pytest

from siams.unidades import (
    MJ_POR_KWH, kwh_a_mj, mj_a_kwh, normalizar_columnas_ideam, normalizar_columnas_nasa,
    radiacion_plausible, unidad_radiacion_probable,
)


def test_conversion_ida_y_vuelta():
    assert MJ_POR_KWH == 3.6
    assert kwh_a_mj(1.0) == pytest.approx(3.6)
    assert mj_a_kwh(18.0) == pytest.approx(5.0)
    assert mj_a_kwh(kwh_a_mj(4.2)) == pytest.approx(4.2)


def test_rango_fisico_radiacion():
    valores_nasa = [12.99, 14.53, 13.40, 25.77]     # Tumaco, MJ/m²/día
    assert radiacion_plausible(valores_nasa, "MJ")
    assert not radiacion_plausible(valores_nasa, "kWh")  # imposibles en kWh/m²/día
    assert radiacion_plausible([4.5, 5.2, 6.1], "kWh")


def test_unidad_probable():
    assert unidad_radiacion_probable([14.2, 16.4, 19.4]) == "MJ/m²/día"
    assert unidad_radiacion_probable([4.1, 5.0, 5.5]) == "kWh/m²/día"


def test_renombres_compatibles_con_excel_viejo_y_nuevo():
    viejo = pd.DataFrame(columns=["mes", "precipitacion_mm_dia"])
    assert list(normalizar_columnas_nasa(viejo, "Regimen_P").columns) == ["mes", "precipitacion_mm_mes"]
    nuevo = pd.DataFrame(columns=["mes", "precipitacion_mm_mes"])
    assert list(normalizar_columnas_nasa(nuevo, "Regimen_P").columns) == ["mes", "precipitacion_mm_mes"]
    diario = pd.DataFrame(columns=["fecha", "precipitacion_mm_dia", "radiacion_solar_kWh_m2_dia"])
    assert list(normalizar_columnas_nasa(diario, "Datos_diarios").columns) == [
        "fecha", "precipitacion_mm_dia", "radiacion_solar_MJ_m2_dia"]
    anual = pd.DataFrame(columns=["fecha", "precipitacion", "anio"])
    assert "precipitacion_mm_anio" in normalizar_columnas_ideam(anual, "P_anual").columns
