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
from .utilidades import CARPETA_DATOS_HIDRO, CARPETA_PROYECTO, buscar_excel_climatico, normalizar_etiqueta
from .grace import ARCHIVO_GWS, extraer_gws_territorio
from .tendencias import extraer_series_historicas_excel

def series_tendencia_territorio(nombre_territorio: str, info_territorio: dict):
    """Reúne todas las series históricas reales disponibles para el territorio."""
    disponibles = {}

    # 1) NASA POWER: conserva la serie histórica diaria en los Excel procesados.
    archivo_clima = archivo_nasa_territorio(nombre_territorio)
    if archivo_clima is not None and Path(archivo_clima).exists():
        try:
            clima = extraer_series_historicas_excel(str(archivo_clima))
            for variable, paquete in clima.items():
                disponibles[variable] = {
                    **paquete,
                    "fuente": "NASA POWER",
                    "archivo": Path(archivo_clima).name,
                }
        except Exception:
            pass

    # 2) IDEAM: se intenta priorizar cuando el Excel conserva series históricas completas.
    # El archivo compacto de Arauca puede no incluir hojas diarias; en ese caso NASA se mantiene.
    archivo_ideam = ARCHIVOS_IDEAM.get(nombre_territorio)
    if archivo_ideam is not None and Path(archivo_ideam).exists():
        try:
            ideam = extraer_series_historicas_excel(str(archivo_ideam))
            for variable in (
                "Precipitación", "Temperatura media", "Temperatura máxima",
                "Temperatura mínima", "Humedad relativa"
            ):
                if variable in ideam:
                    disponibles[variable] = {
                        **ideam[variable],
                        "fuente": "IDEAM",
                        "archivo": Path(archivo_ideam).name,
                    }
        except Exception:
            pass

    # 3) GWSa GRACE/GLDAS.
    if ARCHIVO_GWS is not None and xr is not None and np is not None:
        try:
            df_gws, meta = extraer_gws_territorio(
                str(ARCHIVO_GWS), info_territorio["lat"], info_territorio["lon"]
            )
            if meta.get("disponible", False) and not df_gws.empty:
                disponibles["GWSa"] = {
                    "serie": df_gws.rename(columns={"GWSa (cm)": "Valor"})[["Fecha", "Valor"]],
                    "unidad": "cm",
                    "agregacion": "mean",
                    "fuente": "GRACE/GRACE-FO + GLDAS",
                    "archivo": Path(ARCHIVO_GWS).name,
                    "hoja": "NetCDF",
                }
        except Exception:
            pass

    return disponibles

def encontrar_archivo_excel(prefijos, nombres_preferidos, subcarpetas):
    """Busca primero en Analisis Hidro y después en las ubicaciones anteriores."""
    carpetas = []
    for carpeta in (
        CARPETA_DATOS_HIDRO,
        CARPETA_PROYECTO,
        *(CARPETA_PROYECTO / sub for sub in subcarpetas),
    ):
        if carpeta.is_dir() and carpeta not in carpetas:
            carpetas.append(carpeta)

    # Los nombres completos tienen prioridad sobre copias con (1), (2), etc.
    # Se ignoran tildes y mayúsculas, sin modificar los archivos originales.
    for carpeta in carpetas:
        archivos = sorted(
            (archivo for archivo in carpeta.iterdir()
             if archivo.is_file() and archivo.suffix.casefold() == ".xlsx"
             and not archivo.name.startswith("~$")),
            key=lambda archivo: archivo.name.casefold(),
        )
        for nombre in nombres_preferidos:
            objetivo = normalizar_etiqueta(nombre)
            for archivo in archivos:
                if normalizar_etiqueta(archivo.name) == objetivo:
                    return archivo
        for prefijo in prefijos:
            objetivo = normalizar_etiqueta(prefijo)
            for archivo in archivos:
                stem = normalizar_etiqueta(archivo.stem)
                if stem == objetivo or stem.startswith(objetivo + "_"):
                    return archivo
    return None

def encontrar_archivo_clima_leticia():
    """Localiza NASA POWER de Leticia en la carpeta de análisis hidrológico."""
    return encontrar_archivo_excel(
        prefijos=["NASA_POWER_LETICIA"],
        nombres_preferidos=[
            "NASA_POWER_LETICIA_FINAL.xlsx",
            "NASA_POWER_LETICIA_FINAL (3).xlsx",
            "nasa_power_leticia.xlsx",
        ],
        subcarpetas=["DATOS CLIMA", "datos", "datos/leticia", "datos/leticia/clima"],
    )

ARCHIVO_CLIMA_LETICIA = encontrar_archivo_clima_leticia()

def convertir_fecha_excel(valor):
    """Convierte fechas de texto, datetime o serial real de Excel."""
    if valor is None or pd.isna(valor):
        return None

    if isinstance(valor, pd.Timestamp):
        return valor

    # Los seriales de Excel suelen estar entre 20.000 y 60.000 para fechas modernas.
    if pd.api.types.is_number(valor):
        numero = float(valor)
        if 20000 <= numero <= 60000:
            return pd.Timestamp("1899-12-30") + pd.to_timedelta(numero, unit="D")

    fecha = pd.to_datetime(valor, errors="coerce")
    if pd.notna(fecha):
        return pd.Timestamp(fecha)
    return None

@st.cache_data(show_spinner=False)
def cargar_clima_leticia(ruta_texto: str):
    """Lee los regímenes mensuales y los indicadores del Excel procesado."""
    ruta = Path(ruta_texto)

    p = pd.read_excel(ruta, sheet_name="Regimen_P")
    t = pd.read_excel(ruta, sheet_name="Regimen_T")
    hr = pd.read_excel(ruta, sheet_name="Regimen_HR")
    clim = pd.read_excel(ruta, sheet_name="Climatologia_mensual")
    indicadores_df = pd.read_excel(ruta, sheet_name="Indicadores")

    # Regimen_P contiene el total mensual climatológico, aunque la columna
    # conserve el nombre original de la variable diaria.
    p = p.rename(columns={"precipitacion_mm_dia": "Precipitación mensual (mm)"})
    t = t.rename(columns={
        "temperatura_media_C": "Temperatura media (°C)",
        "temperatura_maxima_C": "Temperatura máxima (°C)",
        "temperatura_minima_C": "Temperatura mínima (°C)",
    })
    hr = hr.rename(columns={"humedad_relativa_pct": "Humedad relativa (%)"})

    otras = clim[[
        "mes",
        "viento_2m_m_s",
        "presion_superficie_kPa",
        "radiacion_solar_kWh_m2_dia",
    ]].rename(columns={
        "viento_2m_m_s": "Viento a 2 m (m/s)",
        "presion_superficie_kPa": "Presión superficial (kPa)",
        "radiacion_solar_kWh_m2_dia": "Radiación solar (kWh/m²/día)",
    })

    df = p.merge(t, on="mes", how="inner")
    df = df.merge(hr, on="mes", how="inner")
    df = df.merge(otras, on="mes", how="inner")
    df = df.sort_values("mes").reset_index(drop=True)
    df["Mes"] = df["mes"].map(dict(enumerate(MESES, start=1)))
    df = df.drop(columns="mes")

    columnas = [
        "Mes",
        "Precipitación mensual (mm)",
        "Temperatura media (°C)",
        "Temperatura máxima (°C)",
        "Temperatura mínima (°C)",
        "Humedad relativa (%)",
        "Viento a 2 m (m/s)",
        "Presión superficial (kPa)",
        "Radiación solar (kWh/m²/día)",
    ]
    df = df[columnas]

    indicadores = dict(
        zip(indicadores_df["Indicador"].astype(str), indicadores_df["Valor"])
    )

    for clave in ("Fecha inicial", "Fecha final"):
        if clave in indicadores:
            indicadores[clave] = convertir_fecha_excel(indicadores[clave])

    return df, indicadores

ARCHIVO_NASA_TUMACO = encontrar_archivo_excel(
    prefijos=["NASA_POWER_TUMACO"],
    nombres_preferidos=[
        "NASA_POWER_TUMACO_FINAL.xlsx",
        "NASA_POWER_TUMACO_FINAL (3).xlsx",
        "nasa_power_tumaco.xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA",
        "datos",
        "datos/tumaco",
        "datos/tumaco/clima",
    ],
)

ARCHIVO_IDEAM_TUMACO = encontrar_archivo_excel(
    prefijos=["ANALISIS_HIDROMETEOROLOGICO_Tumaco", "ANALISIS_HIDROMETEOROLOGICO_TUMACO"],
    nombres_preferidos=[
        "ANALISIS_HIDROMETEOROLOGICO_Tumaco.xlsx",
        "ANALISIS_HIDROMETEOROLOGICO_Tumaco (2).xlsx",
        "ideam_tumaco.xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA",
        "datos",
        "datos/tumaco",
        "datos/tumaco/clima",
    ],
)

ARCHIVO_IDEAM_ARAUCA = encontrar_archivo_excel(
    prefijos=["ANALISIS_HIDROMETEOROLOGICO_Arauca", "ANALISIS_HIDROMETEOROLOGICO_ARAUCA"],
    nombres_preferidos=[
        "ANALISIS_HIDROMETEOROLOGICO_Arauca.xlsx",
        "ANALISIS_HIDROMETEOROLOGICO_ARAUCA.xlsx",
        "ideam_arauca.xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA",
        "datos",
        "datos/arauca",
        "datos/arauca/clima",
    ],
)

ARCHIVO_CLIMA_MEDELLIN = encontrar_archivo_excel(
    prefijos=[
        "NASA_POWER_MEDELLÍN",
        "NASA_POWER_MEDELLIN",
        "NASA_POWER_Medellín",
        "NASA_POWER_Medellin",
    ],
    nombres_preferidos=[
        "NASA_POWER_MEDELLÍN_FINAL.xlsx",
        "NASA_POWER_MEDELLIN_FINAL.xlsx",
        "nasa_power_medellin.xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA",
        "datos",
        "datos/medellin",
        "datos/medellin/clima",
        "datos/medellín",
        "datos/medellín/clima",
    ],
)

ARCHIVO_CLIMA_SAN_ANDRES = encontrar_archivo_excel(
    prefijos=[
        "NASA_POWER_SAN_ANDRES",
        "NASA_POWER_SAN ANDRES",
        "NASA_POWER_SAN_ANDRÉS",
    ],
    nombres_preferidos=[
        "NASA_POWER_SAN_ANDRES_FINAL.xlsx",
        "NASA_POWER_SAN_ANDRÉS_FINAL.xlsx",
        "nasa_power_san_andres.xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA",
        "datos",
        "datos/san_andres",
        "datos/san_andres/clima",
        "datos/san andres",
        "datos/san andres/clima",
    ],
)

ARCHIVO_CLIMA_ARAUCA = encontrar_archivo_excel(
    prefijos=["NASA_POWER_ARAUCA"],
    nombres_preferidos=[
        "NASA_POWER_ARAUCA_FINAL.xlsx",
        "NASA_POWER_ARAUCA_FINAL (1).xlsx",
        "nasa_power_arauca.xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA", "datos", "datos/arauca", "datos/arauca/clima",
    ],
)

ARCHIVO_CLIMA_LA_PAZ = encontrar_archivo_excel(
    prefijos=["NASA_POWER_LA_PAZ", "NASA_POWER_LAPAZ", "NASA_POWER_LA PAZ"],
    nombres_preferidos=[
        "NASA_POWER_LA_PAZ_FINAL.xlsx",
        "NASA_POWER_LAPAZ_FINAL.xlsx",
        "nasa_power_la_paz.xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA", "datos", "datos/la_paz", "datos/la_paz/clima",
        "datos/la paz", "datos/la paz/clima",
    ],
)

ARCHIVOS_CLIMA_NASA = {
    "Bogotá": None,
    "Leticia": ARCHIVO_CLIMA_LETICIA,
    "Medellín": ARCHIVO_CLIMA_MEDELLIN,
    "San Andrés": ARCHIVO_CLIMA_SAN_ANDRES,
    "Arauca": ARCHIVO_CLIMA_ARAUCA,
    "La Paz": ARCHIVO_CLIMA_LA_PAZ,
}

ARCHIVOS_NASA = ARCHIVOS_CLIMA_NASA

ARCHIVOS_IDEAM = {
    "Tumaco": ARCHIVO_IDEAM_TUMACO,
    "Arauca": ARCHIVO_IDEAM_ARAUCA,
}

ARCHIVO_CLIMA_LETICIA = buscar_excel_climatico('Leticia', 'nasa')

ARCHIVO_NASA_TUMACO = buscar_excel_climatico('Tumaco', 'nasa')

ARCHIVO_IDEAM_TUMACO = buscar_excel_climatico('Tumaco', 'ideam')

ARCHIVO_IDEAM_ARAUCA = buscar_excel_climatico('Arauca', 'ideam')

ARCHIVO_CLIMA_MEDELLIN = buscar_excel_climatico('Medellín', 'nasa')

ARCHIVO_CLIMA_SAN_ANDRES = buscar_excel_climatico('San Andrés', 'nasa')

ARCHIVO_CLIMA_ARAUCA = buscar_excel_climatico('Arauca', 'nasa')

ARCHIVO_CLIMA_LA_PAZ = buscar_excel_climatico('La Paz', 'nasa')

ARCHIVOS_CLIMA_NASA.update({
    'Leticia': ARCHIVO_CLIMA_LETICIA,
    'Medellín': ARCHIVO_CLIMA_MEDELLIN,
    'San Andrés': ARCHIVO_CLIMA_SAN_ANDRES,
    'Arauca': ARCHIVO_CLIMA_ARAUCA,
    'La Paz': ARCHIVO_CLIMA_LA_PAZ,
})

ARCHIVOS_NASA = ARCHIVOS_CLIMA_NASA

ARCHIVOS_IDEAM.update({'Tumaco': ARCHIVO_IDEAM_TUMACO, 'Arauca': ARCHIVO_IDEAM_ARAUCA})

def archivo_nasa_territorio(nombre_territorio: str):
    """Devuelve el Excel NASA POWER asociado a cada territorio."""
    if nombre_territorio == "Tumaco":
        return ARCHIVO_NASA_TUMACO
    return ARCHIVOS_CLIMA_NASA.get(nombre_territorio)

@st.cache_data(show_spinner=False)
def cargar_nasa_tumaco(ruta_texto: str):
    """Lee la climatología mensual y los indicadores NASA POWER de Tumaco."""
    ruta = Path(ruta_texto)

    p = pd.read_excel(ruta, sheet_name="Regimen_P").rename(
        columns={"precipitacion_mm_dia": "Precipitación NASA (mm)"}
    )
    t = pd.read_excel(ruta, sheet_name="Regimen_T").rename(columns={
        "temperatura_media_C": "Temperatura media NASA (°C)",
        "temperatura_maxima_C": "Temperatura máxima NASA (°C)",
        "temperatura_minima_C": "Temperatura mínima NASA (°C)",
    })
    hr = pd.read_excel(ruta, sheet_name="Regimen_HR").rename(
        columns={"humedad_relativa_pct": "Humedad NASA (%)"}
    )
    clim = pd.read_excel(ruta, sheet_name="Climatologia_mensual")
    indicadores_df = pd.read_excel(ruta, sheet_name="Indicadores")

    otras = clim[[
        "mes",
        "viento_2m_m_s",
        "presion_superficie_kPa",
        "radiacion_solar_kWh_m2_dia",
    ]].rename(columns={
        "viento_2m_m_s": "Viento a 2 m NASA (m/s)",
        "presion_superficie_kPa": "Presión NASA (kPa)",
        "radiacion_solar_kWh_m2_dia": "Radiación NASA (kWh/m²/día)",
    })

    df = p.merge(t, on="mes", how="inner")
    df = df.merge(hr, on="mes", how="inner")
    df = df.merge(otras, on="mes", how="inner")
    df = df.sort_values("mes").reset_index(drop=True)
    df["Mes"] = df["mes"].map(dict(enumerate(MESES, start=1)))
    df = df.drop(columns="mes")

    indicadores = dict(zip(
        indicadores_df["Indicador"].astype(str),
        indicadores_df["Valor"],
    ))
    for clave in ("Fecha inicial", "Fecha final"):
        if clave in indicadores:
            indicadores[clave] = convertir_fecha_excel(indicadores[clave])

    return df, indicadores

@st.cache_data(show_spinner=False)
def cargar_ideam_tumaco(ruta_texto: str):
    """Lee climatología, fuentes y control de calidad del archivo IDEAM de Tumaco."""
    ruta = Path(ruta_texto)

    clim = pd.read_excel(ruta, sheet_name="Climatologia").rename(columns={
        "Precipitacion_media_mensual": "Precipitación IDEAM (mm)",
        "Temperatura_media": "Temperatura media IDEAM (°C)",
        "Temperatura_maxima": "Temperatura máxima IDEAM (°C)",
        "Temperatura_minima": "Temperatura mínima IDEAM (°C)",
        "Humedad_relativa": "Humedad IDEAM (%)",
    })
    clim = clim[[
        "mes",
        "Mes",
        "Precipitación IDEAM (mm)",
        "Temperatura media IDEAM (°C)",
        "Temperatura máxima IDEAM (°C)",
        "Temperatura mínima IDEAM (°C)",
        "Humedad IDEAM (%)",
    ]].sort_values("mes").reset_index(drop=True)
    clim["Mes"] = clim["mes"].map(dict(enumerate(MESES, start=1)))
    clim = clim.drop(columns="mes")

    indicadores_df = pd.read_excel(ruta, sheet_name="Indicadores")
    control = pd.read_excel(ruta, sheet_name="Control_faltantes")
    fuentes = pd.read_excel(ruta, sheet_name="Fuentes")

    indicadores = dict(zip(
        indicadores_df["Indicador"].astype(str),
        indicadores_df["Valor"],
    ))
    for clave in ("Fecha inicial global", "Fecha final global"):
        if clave in indicadores:
            indicadores[clave] = convertir_fecha_excel(indicadores[clave])

    for columna in ("Fecha inicial", "Fecha final"):
        if columna in control.columns:
            control[columna] = control[columna].apply(convertir_fecha_excel)
    for columna in ("Fecha_inicial", "Fecha_final"):
        if columna in fuentes.columns:
            fuentes[columna] = fuentes[columna].apply(convertir_fecha_excel)

    return clim, indicadores, control, fuentes

def decisiones_climaticas_ideam(control: pd.DataFrame, nombre_territorio: str) -> pd.DataFrame:
    """Decisión de uso por variable para territorios con IDEAM + NASA POWER."""
    completitud = {}
    if control is not None and not control.empty:
        for _, fila in control.iterrows():
            completitud[str(fila.get("Variable", ""))] = fila.get("Completitud [%]")

    def pct(clave):
        valor = completitud.get(clave)
        return f"{float(valor):.2f} %" if pd.notna(valor) else "—"

    if nombre_territorio == "Arauca":
        fuente_principal = [
            "IDEAM",
            "IDEAM derivada",
            "IDEAM",
            "IDEAM",
            "IDEAM con advertencia",
            "NASA POWER",
            "NASA POWER",
            "NASA POWER",
        ]
        uso_otra = [
            "NASA POWER para comparación; no reemplaza la lluvia observada",
            "NASA POWER como contraste continuo; Tmedia IDEAM = (Tmax + Tmin) / 2",
            "NASA POWER como comparación",
            "NASA POWER como comparación",
            "NASA POWER como contraste; validar la HR mínima inferida antes de publicación definitiva",
            "IDEAM no disponible en el archivo procesado",
            "IDEAM no disponible en el archivo procesado",
            "IDEAM no disponible en el archivo procesado",
        ]
    else:
        fuente_principal = [
            "IDEAM",
            "IDEAM",
            "IDEAM con cautela",
            "IDEAM con cautela",
            "NASA POWER + contraste IDEAM",
            "NASA POWER",
            "NASA POWER",
            "NASA POWER",
        ]
        uso_otra = [
            "NASA POWER para comparación; no reemplaza la lluvia observada",
            "NASA POWER como serie continua complementaria",
            "NASA POWER como apoyo por faltantes IDEAM",
            "NASA POWER como apoyo por faltantes IDEAM",
            "IDEAM como observación local parcial",
            "Sin contraste IDEAM en el archivo",
            "Sin contraste IDEAM en el archivo",
            "Sin contraste IDEAM en el archivo",
        ]

    return pd.DataFrame({
        "Variable": [
            "Precipitación", "Temperatura media", "Temperatura máxima",
            "Temperatura mínima", "Humedad relativa", "Viento", "Presión", "Radiación",
        ],
        "Completitud IDEAM": [
            pct("precipitacion"), pct("temperatura_media"), pct("temperatura_maxima"),
            pct("temperatura_minima"), pct("humedad_relativa"),
            "No disponible", "No disponible", "No disponible",
        ],
        "Fuente principal": fuente_principal,
        "Uso de la otra fuente": uso_otra,
    })

def decisiones_climaticas_tumaco(control: pd.DataFrame) -> pd.DataFrame:
    return decisiones_climaticas_ideam(control, "Tumaco")

def periodo_texto(inicio, fin):
    if hasattr(inicio, "strftime") and hasattr(fin, "strftime"):
        return f"{inicio:%Y-%m-%d} a {fin:%Y-%m-%d}"
    return "—"

def clima_prototipo(info: dict) -> pd.DataFrame:
    """Respaldo para territorios que todavía no tienen Excel procesado."""
    return pd.DataFrame({
        "Mes": MESES,
        "Precipitación mensual (mm)": info["precipitacion"],
        "Temperatura media (°C)": info["temperatura"],
        "Humedad relativa (%)": info["humedad"],
    })

__all__ = ['series_tendencia_territorio', 'encontrar_archivo_excel', 'encontrar_archivo_clima_leticia', 'ARCHIVO_CLIMA_LETICIA', 'convertir_fecha_excel', 'cargar_clima_leticia', 'ARCHIVO_NASA_TUMACO', 'ARCHIVO_IDEAM_TUMACO', 'ARCHIVO_IDEAM_ARAUCA', 'ARCHIVO_CLIMA_MEDELLIN', 'ARCHIVO_CLIMA_SAN_ANDRES', 'ARCHIVO_CLIMA_ARAUCA', 'ARCHIVO_CLIMA_LA_PAZ', 'ARCHIVOS_CLIMA_NASA', 'ARCHIVOS_NASA', 'ARCHIVOS_IDEAM', 'archivo_nasa_territorio', 'cargar_nasa_tumaco', 'cargar_ideam_tumaco', 'decisiones_climaticas_ideam', 'decisiones_climaticas_tumaco', 'periodo_texto', 'clima_prototipo']
