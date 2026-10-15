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

from .utilidades import CARPETA_PROYECTO, buscar_archivo_exacto, resolver_carpeta_preferida
from .mapas_datos import CARPETA_MAPAS, CARPETA_MAPAS_QGIS

CARPETA_GIFS = resolver_carpeta_preferida("Animaciones_SWOT", "Gif")

GIFS_SWOT_POR_TERRITORIO = {
    "Leticia": [
        {
            "titulo": "Río Amazonas · variación temporal del ancho",
            "archivo": "swot_leticia_amazonas_ancho.gif",
            "descripcion": "Animación temporal del ancho observado por SWOT en reaches seleccionados del río Amazonas.",
        },
    ],
    "Tumaco": [
        {
            "titulo": "Río Rosario · variación temporal del ancho",
            "archivo": "swot_tumaco_rosario_ancho.gif",
            "descripcion": "Animación temporal del ancho observado por SWOT en reaches seleccionados del río Rosario.",
        },
        {
            "titulo": "Río Mira · variación temporal del ancho",
            "archivo": "swot_tumaco_mira_ancho.gif",
            "descripcion": "Animación temporal del ancho observado por SWOT en reaches seleccionados del río Mira.",
        },
    ],
    "Medellín": [
        {
            "titulo": "Río Medellín · variación temporal del ancho",
            "archivo": "swot_medellin_medellin_ancho.gif",
            "descripcion": "Animación temporal del ancho observado por SWOT en reaches seleccionados del río Medellín.",
        },
    ],
    "Arauca": [
        {
            "titulo": "Río Arauca · variación temporal del ancho",
            "archivo": "swot_arauca_arauca_ancho.gif",
            "descripcion": "Animación temporal del ancho observado por SWOT en reaches seleccionados del río Arauca.",
        },
    ],
}

GIFS_SWOT_ANTIGUOS = {'swot_leticia_amazonas_ancho.gif': 'R_o_Amazonas_Leticia_SWOT_Ancho.gif', 'swot_medellin_medellin_ancho.gif': 'R_o_Medell_n_Medell_n_SWOT_Ancho.gif', 'swot_tumaco_mira_ancho.gif': 'R_o_Mira_Tumaco_SWOT_Ancho.gif', 'swot_tumaco_rosario_ancho.gif': 'R_o_Rosario_Tumaco_SWOT_Ancho.gif', 'swot_arauca_arauca_ancho.gif': 'Rio_Arauca_SWOT_Profesional.gif'}

def buscar_gif_swot(nombre_archivo: str):
    """Selecciona la animación SWOT exacta de río y sede, sin confusiones."""
    return buscar_archivo_exacto(CARPETA_GIFS, nombre_archivo,
                                GIFS_SWOT_ANTIGUOS.get(nombre_archivo, ''))

def mostrar_gifs_swot(nombre_territorio: str) -> None:
    """Muestra las animaciones SWOT configuradas para el territorio activo."""
    configuracion = GIFS_SWOT_POR_TERRITORIO.get(nombre_territorio, [])
    if not configuracion:
        return

    st.markdown(
        '<div class="section-title">Dinámica fluvial observada por SWOT</div>',
        unsafe_allow_html=True,
    )
    st.write(
        "Estas animaciones resumen la variación temporal del ancho del cauce en los "
        "reaches seleccionados. La geometría del río es esquemática; los valores numéricos "
        "mostrados en cada fecha corresponden a las observaciones procesadas."
    )

    # Si hay más de un río para el mismo territorio (por ejemplo Tumaco), se usan
    # pestañas para mantener la página compacta y facilitar la comparación.
    if len(configuracion) > 1:
        pestanas = st.tabs([item["titulo"].split(" · ")[0] for item in configuracion])
        pares = zip(pestanas, configuracion)
    else:
        pares = [(None, configuracion[0])]

    for pestana, item in pares:
        contenedor = pestana if pestana is not None else st.container()
        with contenedor:
            ruta = buscar_gif_swot(item["archivo"])
            if ruta is None:
                st.warning(
                    f"No se encontró `{item['archivo']}` dentro de la carpeta `Animaciones_SWOT`."
                )
                st.caption(f"Ruta esperada: {CARPETA_GIFS / item['archivo']}")
                continue

            st.markdown(f"### {item['titulo']}")
            st.image(
                str(ruta),
                caption=f"{item['descripcion']} · Fuente: HydroWeb / SWOT",
                use_container_width=True,
            )
            st.caption(f"Archivo: {CARPETA_GIFS.name}/{ruta.name}")

    st.markdown(
        dedent("""
        <div class="soft-box">
            <strong>Lectura del producto:</strong> el GIF permite seguir la evolución temporal
            del ancho medido por SWOT para cada reach seleccionado. Se utiliza como recurso
            visual de exploración y no sustituye la descarga ni el análisis de la serie numérica original.
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

CARPETA_TARJETAS_SWOT = resolver_carpeta_preferida("Tarjetas_SWOT", "Tarjeta Tecnica Swot")

TARJETAS_SWOT_POR_TERRITORIO = {
    "Leticia": [
        {
            "rio": "Río Amazonas",
            "archivos": {
                "WSE": "01_WSE_Leticia_SWOT.png",
                "Ancho": "02_Ancho_Leticia_SWOT.png",
                "Área": "03_Area_Leticia_SWOT.png",
                "Pendiente": "04_Pendiente_Leticia_SWOT.png",
            },
        },
    ],
    "Tumaco": [
        {
            "rio": "Río Mira",
            "archivos": {
                "WSE": "01_WSE_Tumaco_SWOT.png",
                "Ancho": "02_Ancho_Tumaco_SWOT.png",
                "Área": "03_Area_Tumaco_SWOT.png",
                "Pendiente": "04_Pendiente_Tumaco_SWOT.png",
            },
        },
        {
            "rio": "Río Rosario",
            "archivos": {
                "WSE": "01_WSE_Tumaco_SWOT Rosario.png",
                "Ancho": "02_Ancho_Tumaco_SWOT Rosario.png",
                "Área": "03_Area_Tumaco_SWOT Rosario.png",
                "Pendiente": "04_Pendiente_Tumaco_SWOT Rosario.png",
            },
        },
    ],
    "Medellín": [
        {
            "rio": "Río Medellín",
            "archivos": {
                "WSE": "01_WSE_Medellin_SWOT.png",
                "Ancho": "02_Ancho_Medellin_SWOT.png",
                "Área": "03_Area_Medellin_SWOT.png",
                "Pendiente": "04_Pendiente_Medellin_SWOT.png",
            },
        },
    ],
    "Arauca": [
        {
            "rio": "Río Arauca",
            "archivos": {
                "WSE": "01_WSE_Arauca_SWOT.png",
                "Ancho": "02_Ancho_Arauca_SWOT.png",
                "Área": "03_Area_Arauca_SWOT.png",
                "Pendiente": "04_Pendiente_Arauca_SWOT.png",
            },
        },
    ],
}

TARJETAS_SWOT_NOMBRES_NUEVOS = {'01_WSE_Arauca_SWOT.png': 'swot_arauca_arauca_wse.png', '01_WSE_Leticia_SWOT.png': 'swot_leticia_amazonas_wse.png', '01_WSE_Medellin_SWOT.png': 'swot_medellin_medellin_wse.png', '01_WSE_Tumaco_SWOT Rosario.png': 'swot_tumaco_rosario_wse.png', '01_WSE_Tumaco_SWOT.png': 'swot_tumaco_mira_wse.png', '02_Ancho_Arauca_SWOT.png': 'swot_arauca_arauca_ancho.png', '02_Ancho_Leticia_SWOT.png': 'swot_leticia_amazonas_ancho.png', '02_Ancho_Medellin_SWOT.png': 'swot_medellin_medellin_ancho.png', '02_Ancho_Tumaco_SWOT Rosario.png': 'swot_tumaco_rosario_ancho.png', '02_Ancho_Tumaco_SWOT.png': 'swot_tumaco_mira_ancho.png', '03_Area_Arauca_SWOT.png': 'swot_arauca_arauca_area.png', '03_Area_Leticia_SWOT.png': 'swot_leticia_amazonas_area.png', '03_Area_Medellin_SWOT.png': 'swot_medellin_medellin_area.png', '03_Area_Tumaco_SWOT Rosario.png': 'swot_tumaco_rosario_area.png', '03_Area_Tumaco_SWOT.png': 'swot_tumaco_mira_area.png', '04_Pendiente_Arauca_SWOT.png': 'swot_arauca_arauca_pendiente.png', '04_Pendiente_Leticia_SWOT.png': 'swot_leticia_amazonas_pendiente.png', '04_Pendiente_Medellin_SWOT.png': 'swot_medellin_medellin_pendiente.png', '04_Pendiente_Tumaco_SWOT Rosario.png': 'swot_tumaco_rosario_pendiente.png', '04_Pendiente_Tumaco_SWOT.png': 'swot_tumaco_mira_pendiente.png'}

def buscar_tarjeta_swot(nombre_archivo: str):
    """Acepta nombres originales de tarjetas y la convención nueva, sin mezclar ríos."""
    return buscar_archivo_exacto(CARPETA_TARJETAS_SWOT, nombre_archivo,
                                TARJETAS_SWOT_NOMBRES_NUEVOS.get(nombre_archivo, ''))

def _mostrar_tarjetas_rio_swot(nombre_territorio: str, cfg_rio: dict) -> None:
    """Muestra las cuatro tarjetas de un río sin alargar verticalmente la página."""
    nombres_variables = list(cfg_rio["archivos"].keys())
    pestanas = st.tabs(nombres_variables)

    descripciones = {
        "WSE": "Elevación de la superficie del agua (Water Surface Elevation).",
        "Ancho": "Ancho del cauce estimado por SWOT para los reaches seleccionados.",
        "Área": "Área superficial del agua asociada a los reaches seleccionados.",
        "Pendiente": "Pendiente longitudinal de la superficie del agua reportada por SWOT.",
    }

    for pestana, variable in zip(pestanas, nombres_variables):
        with pestana:
            nombre_archivo = cfg_rio["archivos"][variable]
            ruta = buscar_tarjeta_swot(nombre_archivo)
            if ruta is None:
                st.warning(
                    f"No se encontró `{nombre_archivo}` dentro de `Tarjetas_SWOT`."
                )
                st.caption(f"Ruta esperada: {CARPETA_TARJETAS_SWOT / nombre_archivo}")
                continue

            st.image(
                str(ruta),
                caption=(
                    f"{cfg_rio['rio']} · {descripciones.get(variable, variable)} "
                    "Fuente: HydroWeb / SWOT"
                ),
                use_container_width=True,
            )
            st.caption(f"Archivo: {CARPETA_TARJETAS_SWOT.name}/{ruta.name}")

def mostrar_tarjetas_swot(nombre_territorio: str) -> None:
    """Muestra las tarjetas técnicas SWOT disponibles para el territorio activo."""
    rios = TARJETAS_SWOT_POR_TERRITORIO.get(nombre_territorio, [])
    if not rios:
        return

    st.markdown(
        '<div class="section-title">Fichas técnicas de variables SWOT</div>',
        unsafe_allow_html=True,
    )
    st.write(
        "Consulta las fichas de **WSE, ancho, área y pendiente** construidas para los "
        "reaches seleccionados. Cada ficha resume el comportamiento de la variable y "
        "sirve como complemento de la animación temporal del ancho."
    )

    if len(rios) > 1:
        # Tumaco tiene dos sistemas fluviales: Mira y Rosario.
        tabs_rios = st.tabs([cfg["rio"] for cfg in rios])
        for tab_rio, cfg_rio in zip(tabs_rios, rios):
            with tab_rio:
                _mostrar_tarjetas_rio_swot(nombre_territorio, cfg_rio)
    else:
        st.markdown(f"### {rios[0]['rio']}")
        _mostrar_tarjetas_rio_swot(nombre_territorio, rios[0])

    st.markdown(
        dedent("""
        <div class="soft-box">
            <strong>Cómo leer estas fichas:</strong> WSE representa la elevación de la superficie
            del agua; ancho y área describen la geometría superficial observada; y pendiente
            representa el gradiente longitudinal de la superficie del agua. Los productos se
            presentan por reach y deben interpretarse con los indicadores de calidad de SWOT.
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

CARPETAS_BUSQUEDA_MAPAS = []

for _carpeta in (
    CARPETA_MAPAS,
    CARPETA_MAPAS_QGIS,
    CARPETA_PROYECTO,
):
    if _carpeta not in CARPETAS_BUSQUEDA_MAPAS:
        CARPETAS_BUSQUEDA_MAPAS.append(_carpeta)

EXTENSIONES_IMAGEN = (".png", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG", ".WEBP")

EXTENSIONES_MAPA = EXTENSIONES_IMAGEN + (".pdf", ".PDF")

__all__ = ['CARPETA_GIFS', 'GIFS_SWOT_POR_TERRITORIO', 'GIFS_SWOT_ANTIGUOS', 'buscar_gif_swot', 'mostrar_gifs_swot', 'CARPETA_TARJETAS_SWOT', 'TARJETAS_SWOT_POR_TERRITORIO', 'TARJETAS_SWOT_NOMBRES_NUEVOS', 'buscar_tarjeta_swot', '_mostrar_tarjetas_rio_swot', 'mostrar_tarjetas_swot', 'CARPETAS_BUSQUEDA_MAPAS', 'EXTENSIONES_IMAGEN', 'EXTENSIONES_MAPA']
