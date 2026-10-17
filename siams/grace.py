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

from .catalogo import MESES

def encontrar_archivo_gws():
    """Localiza el NetCDF de anomalías de almacenamiento subterráneo."""
    carpeta_codigo = Path(__file__).resolve().parent.parent
    carpetas = [
        carpeta_codigo / "data" / "processed" / "grace",
        carpeta_codigo,
        carpeta_codigo / "DATOS GWS",
        carpeta_codigo / "datos",
        carpeta_codigo / "datos" / "gws",
        carpeta_codigo / "datos" / "agua_subterranea",
    ]

    for carpeta in carpetas:
        for nombre in ("gws_anom_colombia.nc", "COL_GWS_estimations.nc"):
            ruta = carpeta / nombre
            if ruta.exists() and ruta.is_file():
                return ruta

    for carpeta in carpetas:
        if carpeta.exists():
            coincidencias = sorted(carpeta.glob("*GWS*estimations*.nc"))
            if coincidencias:
                return coincidencias[0]
    return None

ARCHIVO_GWS = encontrar_archivo_gws()

@st.cache_resource(show_spinner=False)
def cargar_dataset_gws(ruta_texto: str):
    """Carga el NetCDF completo en memoria para evitar dejar el archivo abierto."""
    if xr is None:
        raise ImportError("Falta instalar xarray y un motor NetCDF (netCDF4 o h5netcdf).")
    with xr.open_dataset(ruta_texto) as ds:
        return ds.load()

def distancia_haversine_km(lat1, lon1, lat2, lon2):
    """Distancia geodésica aproximada en kilómetros, vectorizada con NumPy."""
    radio = 6371.0088
    lat1r = np.radians(lat1)
    lon1r = np.radians(lon1)
    lat2r = np.radians(lat2)
    lon2r = np.radians(lon2)
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1r) * np.cos(lat2r) * np.sin(dlon / 2.0) ** 2
    return 2.0 * radio * np.arcsin(np.sqrt(a))

@st.cache_data(show_spinner=False)
def extraer_gws_territorio(ruta_texto: str, lat_obj: float, lon_obj: float, radio_max_km: float = 120.0):
    """
    Extrae la serie del píxel válido más cercano.

    No usa simplemente ``method='nearest'`` porque algunos píxeles de borde del
    NetCDF están vacíos. También evita asignar a islas un píxel continental lejano.
    """
    if xr is None or np is None:
        raise ImportError("Faltan dependencias para leer el NetCDF.")

    ds = cargar_dataset_gws(ruta_texto)
    if "GWS_anom" not in ds.data_vars:
        raise KeyError("El NetCDF no contiene la variable GWS_anom.")

    da = ds["GWS_anom"]
    if not {"time", "lat", "lon"}.issubset(set(da.dims)):
        raise ValueError("GWS_anom no tiene las dimensiones esperadas: time, lat y lon.")

    latitudes = np.asarray(ds["lat"].values, dtype=float)
    longitudes = np.asarray(ds["lon"].values, dtype=float)
    lon_obj_norm = float(lon_obj)
    if np.nanmin(longitudes) >= 0 and lon_obj_norm < 0:
        lon_obj_norm = lon_obj_norm % 360

    validos = np.asarray(da.notnull().any(dim="time").values, dtype=bool)
    lat_grid, lon_grid = np.meshgrid(latitudes, longitudes, indexing="ij")
    distancias = distancia_haversine_km(lat_obj, lon_obj_norm, lat_grid, lon_grid)
    distancias = np.where(validos, distancias, np.inf)

    if not np.isfinite(distancias).any():
        return pd.DataFrame(), {"disponible": False, "motivo": "El archivo no contiene píxeles válidos."}

    indice = np.unravel_index(np.nanargmin(distancias), distancias.shape)
    i_lat, i_lon = int(indice[0]), int(indice[1])
    distancia_km = float(distancias[i_lat, i_lon])

    if distancia_km > radio_max_km:
        return pd.DataFrame(), {
            "disponible": False,
            "motivo": (
                f"El píxel válido más cercano está a {distancia_km:.0f} km. "
                "No se asigna porque sería una extrapolación espacial poco representativa."
            ),
            "distancia_km": distancia_km,
        }

    serie = da.isel(lat=i_lat, lon=i_lon)
    df = pd.DataFrame({
        "Fecha": pd.to_datetime(ds["time"].values),
        "GWSa (cm)": np.asarray(serie.values, dtype=float),
    }).dropna(subset=["GWSa (cm)"]).sort_values("Fecha").reset_index(drop=True)

    if df.empty:
        return df, {"disponible": False, "motivo": "La celda seleccionada no contiene observaciones válidas."}

    x_anios = (df["Fecha"] - df["Fecha"].min()).dt.total_seconds() / (365.25 * 24 * 3600)
    pendiente = float(np.polyfit(x_anios, df["GWSa (cm)"], 1)[0]) if len(df) >= 2 else float("nan")

    meta = {
        "disponible": True,
        "lat_pixel": float(latitudes[i_lat]),
        "lon_pixel": float(longitudes[i_lon]),
        "distancia_km": distancia_km,
        "fecha_inicial": df["Fecha"].min(),
        "fecha_final": df["Fecha"].max(),
        "registros": int(len(df)),
        "pendiente_cm_anio": pendiente,
    }
    return df, meta

def climatologia_gws(df: pd.DataFrame) -> pd.DataFrame:
    """Promedio multianual por mes de la GWSa extraída."""
    temporal = df.copy()
    temporal["Mes_num"] = temporal["Fecha"].dt.month
    salida = (
        temporal.groupby("Mes_num", as_index=False)["GWSa (cm)"]
        .mean()
        .sort_values("Mes_num")
    )
    salida["Mes"] = salida["Mes_num"].map(dict(enumerate(MESES, start=1)))
    return salida[["Mes_num", "Mes", "GWSa (cm)"]]

def calcular_ggdi(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Calcula el GRACE Groundwater Drought Index (GGDI) para la serie de una sede.

    Metodología implementada:
    1) climatología mensual de GWSa usando todos los años disponibles;
    2) GSD = GWSa observada - climatología del mismo mes;
    3) GGDI = GSD / desviación estándar de toda la serie GSD.

    El índice es adimensional. Valores positivos indican almacenamiento por encima
    de lo esperado para ese mes y valores negativos indican déficit relativo.
    """
    if np is None:
        raise ImportError("Falta NumPy para calcular GGDI.")
    if df is None or df.empty:
        return pd.DataFrame(), {"disponible": False, "motivo": "No hay datos GWSa."}

    temporal = df[["Fecha", "GWSa (cm)"]].copy()
    temporal["Fecha"] = pd.to_datetime(temporal["Fecha"], errors="coerce")
    temporal["GWSa (cm)"] = pd.to_numeric(temporal["GWSa (cm)"], errors="coerce")
    temporal = temporal.dropna(subset=["Fecha", "GWSa (cm)"]).sort_values("Fecha")

    if temporal.empty or temporal["Fecha"].dt.year.nunique() < 2:
        return pd.DataFrame(), {
            "disponible": False,
            "motivo": "Se requieren al menos dos años para construir una climatología mensual.",
        }

    temporal["Año"] = temporal["Fecha"].dt.year.astype(int)
    temporal["Mes_num"] = temporal["Fecha"].dt.month.astype(int)
    temporal["Mes"] = temporal["Mes_num"].map(dict(enumerate(MESES, start=1)))

    climatologia = (
        temporal.groupby("Mes_num")["GWSa (cm)"]
        .mean()
        .rename("GWSa climatológica (cm)")
    )
    temporal = temporal.join(climatologia, on="Mes_num")

    temporal["GSD (cm)"] = (
        temporal["GWSa (cm)"] - temporal["GWSa climatológica (cm)"]
    )

    sigma_gsd = float(temporal["GSD (cm)"].std(ddof=1))
    if not np.isfinite(sigma_gsd) or sigma_gsd <= 0:
        return pd.DataFrame(), {
            "disponible": False,
            "motivo": "La desviación estándar de GSD es nula o no válida.",
        }

    temporal["GGDI"] = temporal["GSD (cm)"] / sigma_gsd
    temporal["Condición GGDI"] = np.where(
        temporal["GGDI"] < 0,
        "Déficit respecto a lo normal del mes",
        np.where(
            temporal["GGDI"] > 0,
            "Por encima de lo normal del mes",
            "Condición mensual normal",
        ),
    )

    meta = {
        "disponible": True,
        "sigma_gsd_cm": sigma_gsd,
        "registros": int(len(temporal)),
        "anios": int(temporal["Año"].nunique()),
        "fecha_inicial": temporal["Fecha"].min(),
        "fecha_final": temporal["Fecha"].max(),
        "ggdi_min": float(temporal["GGDI"].min()),
        "ggdi_max": float(temporal["GGDI"].max()),
        "porcentaje_deficit": float((temporal["GGDI"] < 0).mean() * 100.0),
    }

    columnas = [
        "Fecha", "Año", "Mes_num", "Mes",
        "GWSa (cm)", "GWSa climatológica (cm)",
        "GSD (cm)", "GGDI", "Condición GGDI",
    ]
    return temporal[columnas].reset_index(drop=True), meta

__all__ = ['encontrar_archivo_gws', 'ARCHIVO_GWS', 'cargar_dataset_gws', 'distancia_haversine_km', 'extraer_gws_territorio', 'climatologia_gws', 'calcular_ggdi']
