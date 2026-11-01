"""Pruebas de siams/estadistica.py (tendencia y homogeneidad)."""

import numpy as np
import pandas as pd
import pytest

from siams.estadistica import (
    agregar_serie_anual, analizar_serie_tendencia, evaluar_homogeneidad,
    mann_kendall, mann_kendall_hamed_rao, pendiente_sen, prueba_pettitt, prueba_snht,
    fraccion_con_decimales,
)


def test_serie_estrictamente_creciente():
    r = mann_kendall([1, 2, 3, 4, 5, 6, 7, 8])
    assert r["S"] == 28 and r["significativa"]          # S = n(n-1)/2
    assert r["tau"] == pytest.approx(1.0)
    assert r["tendencia"] == "Creciente significativa"


def test_serie_decreciente_y_constante():
    assert mann_kendall([8, 7, 6, 5, 4, 3, 2, 1])["tendencia"] == "Decreciente significativa"
    r = mann_kendall([5, 5, 5, 5, 5, 5])
    assert r["S"] == 0 and not r["significativa"]


def test_mann_kendall_valores_de_referencia():
    # Valores calculados con pymannkendall 1.4.3 (original_test) para esta serie.
    y = [10, 12, 9, 14, 13, 15, 18, 16, 20, 19, 22, 21]
    r = mann_kendall(y)
    assert r["S"] == 54
    assert r["var_S"] == pytest.approx(212.6667, abs=1e-3)
    assert r["Z"] == pytest.approx(3.634345, abs=1e-6)
    assert r["p"] == pytest.approx(0.00027869, abs=1e-7)
    assert pendiente_sen(range(len(y)), y)["pendiente"] == pytest.approx(1.126984, abs=1e-6)


def test_mann_kendall_pocos_datos():
    with pytest.raises(ValueError):
        mann_kendall([1, 2, 3])


def test_pendiente_sen_recta_exacta():
    anios = np.arange(2000, 2010)
    r = pendiente_sen(anios, 3.0 * anios - 100)
    assert r["pendiente"] == pytest.approx(3.0)
    assert r["intercepto"] == pytest.approx(-100.0)


def test_hamed_rao_coincide_con_original_sin_autocorrelacion():
    rng = np.random.default_rng(1)
    y = rng.normal(size=40)
    a = mann_kendall(y)
    b = mann_kendall_hamed_rao(y)
    assert b["S"] == a["S"]
    assert b["factor_n_n_efectivo"] >= 0


def test_hamed_rao_infla_varianza_con_persistencia():
    rng = np.random.default_rng(7)
    e = rng.normal(size=60)
    y = np.empty(60)
    y[0] = e[0]
    for i in range(1, 60):          # AR(1) fuerte
        y[i] = 0.85 * y[i - 1] + e[i]
    b = mann_kendall_hamed_rao(y)
    assert b["factor_n_n_efectivo"] > 1.0
    assert b["p"] >= mann_kendall(y)["p"]


def test_pettitt_y_snht_detectan_salto():
    y = np.r_[np.full(15, 1500.0), np.full(15, 3500.0)] + np.tile([0, 50, -50], 10)
    anios = np.arange(1985, 2015)
    p = prueba_pettitt(y)
    s = prueba_snht(y, simulaciones=500)
    assert p["significativa"] and s["significativa"]
    assert p["indice"] == 14 and s["indice"] == 14
    h = evaluar_homogeneidad(anios, y)
    assert h["anio_cambio"] == 2000
    assert h["dictamen"] == "Probable inhomogeneidad"


def test_serie_homogenea_sin_cambio():
    rng = np.random.default_rng(3)
    y = rng.normal(2000, 200, size=30)
    h = evaluar_homogeneidad(np.arange(1990, 2020), y)
    assert h["pettitt_p"] > 0.05


def test_snht_reproducible():
    y = np.r_[np.zeros(10), np.ones(10)] + np.linspace(0, 0.1, 20)
    assert prueba_snht(y)["p"] == prueba_snht(y)["p"]


def test_agregar_serie_anual_descarta_anios_incompletos():
    fechas = pd.date_range("2000-01-01", "2002-12-31", freq="D")
    serie = pd.DataFrame({"Fecha": fechas, "Valor": 1.0})
    serie = serie[~((serie["Fecha"].dt.year == 2002) & (serie["Fecha"].dt.month > 3))]  # 2002 con 3 meses
    anual = agregar_serie_anual(serie, "sum")
    assert list(anual["Año"]) == [2000, 2001]
    assert anual.loc[anual["Año"] == 2000, "Valor"].item() == 366  # bisiesto
    media = agregar_serie_anual(serie, "mean")
    assert (media["Valor"] == 1.0).all()


def test_analizar_serie_tendencia_subperiodo():
    fechas = pd.date_range("1985-01-01", "2014-12-31", freq="D")
    valor = np.where(fechas.year < 1995, 4.0, 9.0)       # salto sin tendencia dentro de cada tramo
    serie = pd.DataFrame({"Fecha": fechas, "Valor": valor})
    _, completo = analizar_serie_tendencia(serie, "sum")
    anual, tramo = analizar_serie_tendencia(serie, "sum", anio_inicio=1995)
    assert completo["significativa"]                      # el salto parece tendencia...
    assert not tramo["significativa"]                     # ...pero en el tramo homogéneo no la hay
    assert anual["Año"].min() == 1995
    assert "p_hamed_rao" in tramo


def test_fraccion_con_decimales():
    assert fraccion_con_decimales([0, 1.5, 2.0, 3.25]) == pytest.approx(2 / 3)
    assert fraccion_con_decimales([1, 2, 3]) == 0.0
