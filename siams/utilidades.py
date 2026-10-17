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



def normalizar_etiqueta(texto) -> str:
    """Normaliza nombres de columnas sin depender de tildes, espacios o símbolos."""
    base = unicodedata.normalize("NFKD", str(texto))
    base = "".join(c for c in base if not unicodedata.combining(c)).casefold()
    salida = []
    for c in base:
        salida.append(c if c.isalnum() else "_")
    return "_".join(parte for parte in "".join(salida).split("_") if parte)

def resolver_carpeta_preferida(*nombres: str) -> Path:
    """Carpeta principal con normalización de espacios, tildes y mayúsculas."""
    base = Path(__file__).resolve().parent.parent
    for nombre in nombres:
        ruta = base / nombre
        if ruta.is_dir():
            return ruta
    if base.is_dir():
        carpetas = {normalizar_etiqueta(p.name): p for p in base.iterdir() if p.is_dir()}
        for nombre in nombres:
            encontrada = carpetas.get(normalizar_etiqueta(nombre))
            if encontrada is not None:
                return encontrada
    return base / nombres[0]

def resolver_subcarpeta(carpeta_padre: Path, nombre: str) -> Path:
    """Reconoce subcarpetas 'La_Paz', 'LA PAZ' o 'la_paz' sin equivocarse de sede."""
    directa = carpeta_padre / nombre
    if directa.is_dir():
        return directa
    if carpeta_padre.is_dir():
        objetivo = normalizar_etiqueta(nombre)
        for ruta in sorted(carpeta_padre.iterdir(), key=lambda p: p.name.casefold()):
            if ruta.is_dir() and normalizar_etiqueta(ruta.name) == objetivo:
                return ruta
    return directa

def buscar_archivo_exacto(carpeta: Path, *nombres: str) -> Path | None:
    """Resuelve SOLO nombres completos indicados; impide confundir sedes/niveles/ríos."""
    if not carpeta.is_dir():
        return None
    disponibles = {
        normalizar_etiqueta(p.name): p for p in carpeta.iterdir()
        if p.is_file()
    }
    for nombre in nombres:
        if not nombre:
            continue
        ruta = carpeta / nombre
        if ruta.is_file():
            return ruta
        hallada = disponibles.get(normalizar_etiqueta(nombre))
        if hallada is not None:
            return hallada
    return None

def buscar_excel_climatico(territorio: str, fuente: str) -> Path | None:
    """Reconoce NASA POWER e IDEAM con nombres nuevos o antiguos sin mezclar fuentes."""
    nombres_sede = {
        'Leticia': 'leticia', 'Tumaco': 'tumaco', 'Arauca': 'arauca',
        'Medellín': 'medellin', 'San Andrés': 'san_andres', 'La Paz': 'la_paz',
    }
    slug = nombres_sede.get(territorio, normalizar_etiqueta(territorio))
    origenes = [CARPETA_DATOS_HIDRO, CARPETA_PROYECTO / "data/processed/clima", CARPETA_PROYECTO]
    origenes += [CARPETA_PROYECTO / p for p in ('Analisis Hidro', 'Datos_Climaticos')]
    if fuente == 'nasa':
        alternativas = [f'nasa_power_{slug}.xlsx', f'nasa_power_{slug}_final.xlsx',
                        f'nasa_power_{slug}_final (3).xlsx',
                        f'nasa_power_{slug}_final (1).xlsx']
        if slug == 'la_paz':
            alternativas += ['NASA_POWER_LAPAZ_FINAL.xlsx']
        if slug == 'medellin':
            alternativas += ['NASA_POWER_MEDELLÍN_FINAL.xlsx']
    else:
        alternativas = [f'analisis_hidrometeorologico_{slug}.xlsx',
                        f'analisis_hidrometeorologico_{slug} (2).xlsx',
                        f'ideam_{slug}.xlsx']
    revisadas = set()
    for carpeta in origenes:
        if carpeta in revisadas or not carpeta.is_dir():
            continue
        revisadas.add(carpeta)
        ruta = buscar_archivo_exacto(carpeta, *alternativas)
        if ruta is not None:
            return ruta
        # Variantes finales (2) o nombres antiguos: coincidencia de sede y fuente completas.
        for archivo in sorted(carpeta.glob('*.xlsx')):
            nombre = normalizar_etiqueta(archivo.stem)
            nombre = re.sub(r'_\d+$', '', nombre) if nombre.endswith(('_1','_2','_3','_4')) else nombre
            if fuente == 'nasa':
                prefijo = 'nasa_power_'
                if not nombre.startswith(prefijo):
                    continue
                resto = nombre[len(prefijo):]
                if slug == 'la_paz':
                    correcto = resto in {'la_paz', 'la_paz_final', 'lapaz_final', 'lapaz'}
                else:
                    correcto = resto in {slug, slug+'_final'}
            else:
                correcto = nombre in {f'analisis_hidrometeorologico_{slug}', f'ideam_{slug}'}
            if correcto:
                return archivo
    return None

def _fechas_desde_dataframe(df: pd.DataFrame):
    """Busca fecha directa o columnas YEAR/MO/DY en una hoja de cálculo."""
    mapa = {normalizar_etiqueta(c): c for c in df.columns}

    for alias in ("fecha", "date", "datetime", "time"):
        if alias in mapa:
            serie = df[mapa[alias]]
            if pd.api.types.is_numeric_dtype(serie):
                numeros = pd.to_numeric(serie, errors="coerce")
                mediana = numeros.dropna().median() if numeros.notna().any() else float("nan")
                if pd.notna(mediana) and 20000 <= mediana <= 60000:
                    return pd.Timestamp("1899-12-30") + pd.to_timedelta(numeros, unit="D")
            return pd.to_datetime(serie, errors="coerce")

    year_col = next((mapa[a] for a in ("year", "ano", "anio") if a in mapa), None)
    month_col = next((mapa[a] for a in ("mo", "month", "mes") if a in mapa), None)
    day_col = next((mapa[a] for a in ("dy", "day", "dia") if a in mapa), None)

    if year_col is not None and month_col is not None:
        anio = pd.to_numeric(df[year_col], errors="coerce")
        mes = pd.to_numeric(df[month_col], errors="coerce")
        dia = pd.to_numeric(df[day_col], errors="coerce") if day_col is not None else 1
        return pd.to_datetime(
            {"year": anio, "month": mes, "day": dia},
            errors="coerce",
        )
    return None

CARPETA_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_DATOS_HIDRO = resolver_carpeta_preferida("data/processed/clima", "Datos_Climaticos", "Analisis Hidro")

__all__ = ['normalizar_etiqueta', 'resolver_carpeta_preferida', 'resolver_subcarpeta', 'buscar_archivo_exacto', 'buscar_excel_climatico', '_fechas_desde_dataframe', 'CARPETA_PROYECTO', 'CARPETA_DATOS_HIDRO']
