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

from .catalogo import ESTADO_COMPONENTES, METADATOS_MAPAS, TERRITORIOS

def clase_estado(estado: str) -> str:
    return {
        "Completo": "status-completo",
        "En proceso": "status-proceso",
        "Pendiente": "status-pendiente",
        "Sin datos": "status-nodatos",
    }.get(estado, "status-pendiente")

def mostrar_semaforo(nombre_territorio: str) -> None:
    tarjetas = []
    for componente, estado, nota in ESTADO_COMPONENTES[nombre_territorio]:
        tarjetas.append(
            f"""<div class="status-card">
            <h4>{componente}</h4>
            <span class="status-pill {clase_estado(estado)}">{estado}</span>
            <div>{nota}</div>
            </div>"""
        )
    html = '<div class="status-grid">' + ''.join(tarjetas) + '</div>'
    st.markdown(html, unsafe_allow_html=True)

def resumen_estados(nombre_territorio: str) -> dict:
    estados = [fila[1] for fila in ESTADO_COMPONENTES[nombre_territorio]]
    return {estado: estados.count(estado) for estado in set(estados)}

def mostrar_ficha_mapa(nombre_territorio: str, clave: str) -> None:
    meta = METADATOS_MAPAS.get(nombre_territorio, {}).get(clave)
    if not meta:
        return
    html = f"""
    <div class="metadata-box">
        <strong>Producto:</strong> {meta['producto']}<br>
        <strong>Entidad:</strong> {meta['entidad']}<br>
        <strong>Alcance espacial:</strong> {meta['alcance']}<br>
        <strong>Referencia temporal:</strong> {meta['actualidad']}<br>
        <strong>Limitación:</strong> {meta['limitacion']}
    </div>
    """
    st.markdown(dedent(html).strip(), unsafe_allow_html=True)

def interpretacion_leticia(df: pd.DataFrame) -> str:
    p = "Precipitación mensual (mm)"
    t = "Temperatura media (°C)"
    hr = "Humedad relativa (%)"
    mes_pmax = df.loc[df[p].idxmax()]
    mes_pmin = df.loc[df[p].idxmin()]
    amplitud_t = df[t].max() - df[t].min()
    hr_media = df[hr].mean()
    return (
        f"El régimen de Leticia alcanza su mayor precipitación mensual en <strong>{mes_pmax['Mes']}</strong> "
        f"({mes_pmax[p]:.1f} mm) y el menor valor en <strong>{mes_pmin['Mes']}</strong> "
        f"({mes_pmin[p]:.1f} mm). La temperatura media mensual presenta una amplitud cercana a "
        f"{amplitud_t:.1f} °C y la humedad media mensual es aproximadamente {hr_media:.1f} %. "
        "NASA POWER se conserva como fuente climática principal debido a la limitada continuidad de las series IDEAM consultadas."
    )

def interpretacion_nasa(nombre_territorio: str, df: pd.DataFrame) -> str:
    p = "Precipitación mensual (mm)"
    t = "Temperatura media (°C)"
    hr = "Humedad relativa (%)"
    mes_pmax = df.loc[df[p].idxmax()]
    mes_pmin = df.loc[df[p].idxmin()]
    amplitud_t = df[t].max() - df[t].min()
    hr_media = df[hr].mean()
    total_p = df[p].sum()
    return (
        f"En <strong>{nombre_territorio}</strong>, el régimen mensual alcanza su mayor precipitación "
        f"en <strong>{mes_pmax['Mes']}</strong> ({mes_pmax[p]:.1f} mm) y el menor valor en "
        f"<strong>{mes_pmin['Mes']}</strong> ({mes_pmin[p]:.1f} mm). "
        f"El acumulado climatológico anual es aproximadamente {total_p:.1f} mm. "
        f"La temperatura media mensual presenta una amplitud cercana a {amplitud_t:.1f} °C "
        f"y la humedad relativa media mensual es aproximadamente {hr_media:.1f} %. "
        "NASA POWER se utiliza como fuente climática continua dentro de esta versión del prototipo."
    )

def interpretacion_ideam_nasa(nombre_territorio: str, df: pd.DataFrame, control: pd.DataFrame) -> str:
    p_i = "Precipitación IDEAM (mm)"
    p_n = "Precipitación NASA (mm)"
    mes_pmax = df.loc[df[p_i].idxmax()]
    mes_pmin = df.loc[df[p_i].idxmin()]
    total_i = df[p_i].sum()
    total_n = df[p_n].sum()
    diferencia = (total_n / total_i - 1) * 100 if total_i else float("nan")
    fila = control.loc[control["Variable"].astype(str).eq("precipitacion")]
    comp = float(fila.iloc[0]["Completitud [%]"]) if not fila.empty else float("nan")

    if nombre_territorio == "Arauca":
        nota = (
            "En Arauca, la temperatura media IDEAM es derivada de Tmax y Tmin y la humedad media "
            "usa una mínima inferida a partir del archivo entregado; esta última debe mantenerse "
            "con advertencia hasta validar el metadato IDEAM."
        )
    else:
        nota = (
            "En Tumaco, NASA POWER funciona como complemento; para humedad se conserva como "
            "referencia continua cuando la observación IDEAM es parcial."
        )

    signo = "mayor" if diferencia > 0 else "menor"
    return (
        f"La precipitación IDEAM presenta su máximo mensual en <strong>{mes_pmax['Mes']}</strong> "
        f"({mes_pmax[p_i]:.1f} mm) y el mínimo en <strong>{mes_pmin['Mes']}</strong> "
        f"({mes_pmin[p_i]:.1f} mm). La serie IDEAM usada tiene {comp:.2f} % de completitud. "
        f"El acumulado climatológico NASA POWER es {abs(diferencia):.1f} % {signo} que el IDEAM. "
        + nota
    )

def interpretacion_tumaco(df: pd.DataFrame, control: pd.DataFrame) -> str:
    return interpretacion_ideam_nasa("Tumaco", df, control)

from pathlib import Path

def archivo_disponible(ruta) -> str:
    return "Disponible" if ruta is not None and Path(ruta).exists() else "No encontrado"

def territorio_actual(nombre: str) -> dict:
    return TERRITORIOS[nombre]

def mostrar_encabezado(titulo: str, subtitulo: str) -> None:
    html = f"""
    <div class="hero">
        <div class="eyebrow">Semillero SIAMS</div>
        <h1>{titulo}</h1>
        <p>{subtitulo}</p>
    </div>
    """
    st.markdown(dedent(html).strip(), unsafe_allow_html=True)

def mostrar_tarjeta(titulo: str, texto: str, icono: str = "💧") -> None:
    html = f"""
    <div class="card">
        <h3>{icono} {titulo}</h3>
        <p>{texto}</p>
    </div>
    """
    st.markdown(dedent(html).strip(), unsafe_allow_html=True)

__all__ = ['clase_estado', 'mostrar_semaforo', 'resumen_estados', 'mostrar_ficha_mapa', 'interpretacion_leticia', 'interpretacion_nasa', 'interpretacion_ideam_nasa', 'interpretacion_tumaco', 'archivo_disponible', 'territorio_actual', 'mostrar_encabezado', 'mostrar_tarjeta']
