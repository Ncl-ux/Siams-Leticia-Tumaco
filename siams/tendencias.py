# Archivo reorganizado a partir de SIAMS V39.
# No modificar la lógica científica aquí sin pruebas y revisión metodológica.
from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from html import escape
import math
import unicodedata
import base64
import subprocess
import tempfile
import re

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    import numpy as np
    import xarray as xr
except ImportError:
    np = None
    xr = None

from .utilidades import _fechas_desde_dataframe, normalizar_etiqueta

VARIABLES_TENDENCIA = {
    "Precipitación": {
        "unidad": "mm",
        "agregacion": "sum",
        "aliases": [
            "precipitacion_mm_dia", "precipitacion", "precipitation",
            "prectotcorr", "prectot", "rainfall",
        ],
    },
    "Temperatura media": {
        "unidad": "°C",
        "agregacion": "mean",
        "aliases": ["temperatura_media_c", "temperatura_media", "t2m", "temperature_mean"],
    },
    "Temperatura máxima": {
        "unidad": "°C",
        "agregacion": "mean",
        "aliases": ["temperatura_maxima_c", "temperatura_maxima", "t2m_max", "t2mmax", "temperature_max"],
    },
    "Temperatura mínima": {
        "unidad": "°C",
        "agregacion": "mean",
        "aliases": ["temperatura_minima_c", "temperatura_minima", "t2m_min", "t2mmin", "temperature_min"],
    },
    "Humedad relativa": {
        "unidad": "%",
        "agregacion": "mean",
        "aliases": ["humedad_relativa_pct", "humedad_relativa", "rh2m", "relative_humidity"],
    },
    "Viento a 2 m": {
        "unidad": "m/s",
        "agregacion": "mean",
        "aliases": ["viento_2m_m_s", "viento_2m", "ws2m", "wind_speed_2m", "wind_speed"],
    },
    "Presión superficial": {
        "unidad": "kPa",
        "agregacion": "mean",
        "aliases": ["presion_superficie_kpa", "presion_superficie", "ps", "surface_pressure"],
    },
    "Radiación solar": {
        "unidad": "kWh/m²/día",
        "agregacion": "mean",
        "aliases": [
            "radiacion_solar_kwh_m2_dia", "radiacion_solar", "allsky_sfc_sw_dwn",
            "solar_radiation", "radiation",
        ],
    },
}

def _buscar_columna_variable(df: pd.DataFrame, aliases) -> str | None:
    """Encuentra una variable usando coincidencia exacta normalizada y luego parcial."""
    columnas = [(c, normalizar_etiqueta(c)) for c in df.columns]
    aliases_norm = [normalizar_etiqueta(a) for a in aliases]

    # Primero coincidencia exacta para evitar confundir T2M con T2M_MAX/T2M_MIN.
    for alias in aliases_norm:
        for original, norm in columnas:
            if norm == alias:
                return original

    # Después coincidencia contenida para nombres descriptivos más largos.
    for alias in aliases_norm:
        if len(alias) < 4:
            continue
        for original, norm in columnas:
            if alias in norm:
                return original
    return None

@st.cache_data(show_spinner=False)
def extraer_series_historicas_excel(ruta_texto: str):
    """
    Busca automáticamente series históricas dentro de un Excel procesado.

    Se ignoran hojas de climatología/regímenes porque sus 12 meses NO constituyen
    una serie temporal apropiada para Mann-Kendall. Se priorizan hojas con fechas
    reales o con columnas YEAR/MO/DY.
    """
    ruta = Path(ruta_texto)
    if not ruta.exists():
        return {}

    resultados = {}
    xls = pd.ExcelFile(ruta)
    excluir = ("regimen", "climatologia", "indicador", "control", "fuente", "resumen")

    for hoja in xls.sheet_names:
        hoja_norm = normalizar_etiqueta(hoja)
        if any(token in hoja_norm for token in excluir):
            continue
        try:
            df = pd.read_excel(ruta, sheet_name=hoja)
        except Exception:
            continue
        if df.empty or len(df.columns) < 2:
            continue

        fechas = _fechas_desde_dataframe(df)
        if fechas is None:
            continue
        fechas = pd.Series(fechas, index=df.index)
        validas = fechas.notna()
        if validas.sum() < 20:
            continue
        if fechas[validas].dt.year.nunique() < 3:
            continue

        for nombre, cfg in VARIABLES_TENDENCIA.items():
            columna = _buscar_columna_variable(df, cfg["aliases"])
            if columna is None:
                continue
            valores = pd.to_numeric(df[columna], errors="coerce")
            serie = pd.DataFrame({"Fecha": fechas, "Valor": valores}).dropna()
            serie = serie.sort_values("Fecha").drop_duplicates(subset=["Fecha"], keep="last")
            if len(serie) < 20 or serie["Fecha"].dt.year.nunique() < 3:
                continue

            actual = resultados.get(nombre)
            if actual is None or len(serie) > len(actual["serie"]):
                resultados[nombre] = {
                    "serie": serie.reset_index(drop=True),
                    "unidad": cfg["unidad"],
                    "agregacion": cfg["agregacion"],
                    "hoja": hoja,
                }
    return resultados

def agregar_serie_anual(serie: pd.DataFrame, agregacion: str) -> pd.DataFrame:
    """Agrega una serie a escala anual y elimina años claramente incompletos."""
    df = serie[["Fecha", "Valor"]].copy().dropna()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha", "Valor"])
    if df.empty:
        return pd.DataFrame(columns=["Año", "Valor", "N"])

    df["Año"] = df["Fecha"].dt.year
    conteos = df.groupby("Año")["Valor"].count()
    if conteos.empty:
        return pd.DataFrame(columns=["Año", "Valor", "N"])

    # El número típico de observaciones por año permite trabajar tanto con datos
    # diarios (~365) como mensuales (~12) sin fijar una frecuencia a mano.
    positivos = conteos[conteos > 0]
    esperado = float(positivos.median()) if not positivos.empty else 1.0
    umbral = max(1.0, 0.75 * esperado)
    anios_validos = conteos[conteos >= umbral].index
    df = df[df["Año"].isin(anios_validos)]

    if agregacion == "sum":
        valores = df.groupby("Año")["Valor"].sum(min_count=1)
    else:
        valores = df.groupby("Año")["Valor"].mean()
    n = df.groupby("Año")["Valor"].count()

    salida = pd.DataFrame({"Año": valores.index.astype(int), "Valor": valores.values, "N": n.values})
    return salida.dropna(subset=["Valor"]).sort_values("Año").reset_index(drop=True)

def mann_kendall(valores, alpha: float = 0.05) -> dict:
    """Prueba Mann-Kendall bilateral con corrección por empates, sin dependencias extra."""
    y = np.asarray(valores, dtype=float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < 5:
        raise ValueError("Mann-Kendall requiere al menos 5 observaciones válidas.")

    s = 0
    for i in range(n - 1):
        s += int(np.sign(y[i + 1:] - y[i]).sum())

    _, conteos = np.unique(y, return_counts=True)
    empates = conteos[conteos > 1]
    var_s = (
        n * (n - 1) * (2 * n + 5)
        - np.sum(empates * (empates - 1) * (2 * empates + 5))
    ) / 18.0

    if var_s <= 0:
        z = 0.0
    elif s > 0:
        z = (s - 1) / math.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s)
    else:
        z = 0.0

    # erfc entrega directamente la probabilidad bilateral de una normal estándar.
    p = math.erfc(abs(z) / math.sqrt(2.0))
    tau = s / (0.5 * n * (n - 1))
    significativa = p < alpha

    if significativa and tau > 0:
        tendencia = "Creciente significativa"
    elif significativa and tau < 0:
        tendencia = "Decreciente significativa"
    else:
        tendencia = "Sin tendencia significativa"

    return {
        "n": n,
        "S": float(s),
        "var_S": float(var_s),
        "Z": float(z),
        "p": float(p),
        "tau": float(tau),
        "significativa": bool(significativa),
        "tendencia": tendencia,
        "alpha": float(alpha),
    }

def pendiente_sen(anios, valores) -> dict:
    """Pendiente de Sen y ordenada robusta para una serie anual."""
    x = np.asarray(anios, dtype=float)
    y = np.asarray(valores, dtype=float)
    mascara = np.isfinite(x) & np.isfinite(y)
    x, y = x[mascara], y[mascara]
    if len(y) < 2:
        return {"pendiente": float("nan"), "intercepto": float("nan")}

    pendientes = []
    for i in range(len(y) - 1):
        dx = x[i + 1:] - x[i]
        validos = dx != 0
        if validos.any():
            pendientes.extend(((y[i + 1:][validos] - y[i]) / dx[validos]).tolist())

    if not pendientes:
        return {"pendiente": float("nan"), "intercepto": float("nan")}
    pendiente = float(np.median(pendientes))
    intercepto = float(np.median(y - pendiente * x))
    return {"pendiente": pendiente, "intercepto": intercepto}

def analizar_serie_tendencia(serie: pd.DataFrame, agregacion: str, alpha: float = 0.05):
    anual = agregar_serie_anual(serie, agregacion)
    if len(anual) < 5:
        return anual, None
    mk = mann_kendall(anual["Valor"].values, alpha=alpha)
    sen = pendiente_sen(anual["Año"].values, anual["Valor"].values)
    resultado = {**mk, **sen}
    return anual, resultado

__all__ = ['VARIABLES_TENDENCIA', '_buscar_columna_variable', 'extraer_series_historicas_excel', 'agregar_serie_anual', 'mann_kendall', 'pendiente_sen', 'analizar_serie_tendencia']
