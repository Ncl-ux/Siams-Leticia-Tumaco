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

from .utilidades import normalizar_etiqueta, resolver_carpeta_preferida
from .mapbiomas import _mostrar_gif_mapbiomas

CARPETA_SENTINEL = resolver_carpeta_preferida("Sentinel")

CARPETAS_SENTINEL_POR_TERRITORIO = {
    "Arauca": "Arauca",
    "La Paz": "La Paz",
    "Leticia": "Leticia",
    "Medellín": "Medellin",
    "San Andrés": "San Andres",
    "Tumaco": "Tumaco",
}

SENTINEL_ARCHIVOS_POR_TERRITORIO = {
    "Leticia": {
        2025: {
            "NDVI": "animacion_ndvi_2025_leticia.gif",
            "MNDWI": "animacion_mndwi_2025_leticia.gif",
            "SCL": "animacion_scl_2025_leticia.gif",
        },
    },
    "Arauca": {
        2025: {
            "NDVI": "animacion_ndvi_2025_arauca.gif",
            "MNDWI": "animacion_mndwi_2025_arauca.gif",
            "SCL": "animacion_scl_2025_arauca.gif",
        },
    },
}

SENTINEL_DESCRIPCIONES = {
    "NDVI": {
        "titulo": "Evolución de la vegetación · NDVI",
        "subtitulo": "Distribución espacial del índice de vegetación de diferencia normalizada.",
        "explicacion": (
            "El NDVI relaciona la reflectancia del infrarrojo cercano y el rojo. "
            "Los valores elevados suelen asociarse con vegetación fotosintéticamente activa; "
            "valores bajos pueden representar agua, suelo desnudo, áreas construidas u otras superficies."
        ),
        "lectura": "Observa las zonas de mayor y menor actividad vegetal y cómo cambian entre fechas.",
        "color": "#168568",
    },
    "MNDWI": {
        "titulo": "NDVI y detección de agua · MNDWI",
        "subtitulo": "Máscara de agua obtenida a partir de un índice espectral.",
        "explicacion": (
            "El MNDWI utiliza las bandas verde y SWIR para resaltar agua superficial. "
            "La máscara final depende del umbral y del tratamiento de píxeles aplicado "
            "al generar la animación. El cauce señalado se superpone sobre el NDVI."
        ),
        "lectura": "Revisa la continuidad y los cambios aparentes del agua identificada.",
        "color": "#217bb0",
    },
    "SCL": {
        "titulo": "NDVI y agua clasificada · SCL",
        "subtitulo": "Máscara de agua derivada de la clasificación de escenas Sentinel-2.",
        "explicacion": (
            "SCL es una capa de clasificación por píxel del producto Sentinel-2 Level-2A. "
            "La clase 6 corresponde a agua. Se utiliza aquí como un método alternativo "
            "para representar el agua sobre el NDVI."
        ),
        "lectura": "Compara la identificación del cauce con la obtenida mediante MNDWI.",
        "color": "#5968a9",
    },
}

def carpeta_sentinel_territorio(nombre_territorio: str) -> Path:
    """Resuelve Sentinel/<sede> aunque la carpeta tenga diferencias de acentos."""
    nombre_carpeta = CARPETAS_SENTINEL_POR_TERRITORIO.get(nombre_territorio, nombre_territorio)
    directa = CARPETA_SENTINEL / nombre_carpeta
    if directa.is_dir():
        return directa
    if CARPETA_SENTINEL.is_dir():
        nombre_normalizado = normalizar_etiqueta(nombre_carpeta)
        for carpeta in CARPETA_SENTINEL.iterdir():
            if carpeta.is_dir() and normalizar_etiqueta(carpeta.name) == nombre_normalizado:
                return carpeta
    return directa

def buscar_animaciones_sentinel(nombre_territorio: str) -> dict:
    """Obtiene {año: {'NDVI': ruta, 'MNDWI': ruta, 'SCL': ruta}} de la sede.

    Los nombres como 'animacion_MNDWI_2025 Leticia.gif' se reconocen sin
    renombrarlos. No se confunden los GIF de sedes diferentes.
    """
    carpeta = carpeta_sentinel_territorio(nombre_territorio)
    if not carpeta.is_dir():
        return {}

    encontrados = {}
    # Primero se respetan los archivos explícitamente registrados para cada sede.
    for anio, indices in SENTINEL_ARCHIVOS_POR_TERRITORIO.get(nombre_territorio, {}).items():
        for tipo, nombre_archivo in indices.items():
            ruta = carpeta / nombre_archivo
            if ruta.is_file():
                encontrados.setdefault(anio, {})[tipo] = ruta

    # Después se incorporan archivos de otros años y variantes de nombres.
    for ruta in sorted(carpeta.iterdir(), key=lambda p: p.name.casefold()):
        if not ruta.is_file() or ruta.suffix.casefold() != ".gif":
            continue
        partes = normalizar_etiqueta(ruta.stem).split("_")
        tipo = next((p.upper() for p in partes if p.upper() in SENTINEL_DESCRIPCIONES), None)
        anio_texto = next((p for p in partes if p.isdigit() and len(p) == 4 and 2000 <= int(p) <= 2100), None)
        if tipo is None or anio_texto is None:
            continue
        anio = int(anio_texto)
        # Se prioriza la primera coincidencia para no elegir copias arbitrarias.
        encontrados.setdefault(anio, {}).setdefault(tipo, ruta)
    return encontrados

def _mostrar_gif_sentinel(ruta: Path, titulo: str, descripcion: str) -> None:
    """Inserta el GIF tal cual para conservar sus fotogramas y leyendas."""
    _mostrar_gif_mapbiomas(ruta, titulo, descripcion)

def _panel_sentinel(nombre_territorio: str, tipo: str, archivos: dict, anio: int, *, descarga: bool = True) -> None:
    meta = SENTINEL_DESCRIPCIONES[tipo]
    st.markdown(f"#### {meta['titulo']}")
    st.caption(meta["subtitulo"])
    ruta = archivos.get(tipo)
    if ruta is None:
        st.info(f"No se encontró una animación {tipo} para {nombre_territorio} ({anio}).")
        return

    _mostrar_gif_sentinel(
        ruta,
        f"{nombre_territorio} · {tipo} · {anio}",
        f"Animación Sentinel-2 · {nombre_territorio} · {anio} · {tipo}",
    )
    st.markdown(meta["explicacion"])
    st.caption("Lectura recomendada: " + meta["lectura"])
    if descarga:
        st.download_button(
            "⬇️ Descargar animación " + tipo,
            data=ruta.read_bytes(),
            file_name=ruta.name,
            mime="image/gif",
            key=f"sentinel_descarga_{normalizar_etiqueta(nombre_territorio)}_{anio}_{tipo}",
        )

def mostrar_sentinel_territorio(nombre_territorio: str) -> None:
    """Panel autónomo de observación satelital para cada sede SIAMS."""
    carpeta = carpeta_sentinel_territorio(nombre_territorio)
    animaciones = buscar_animaciones_sentinel(nombre_territorio)

    st.markdown(
        dedent(f"""
        <div class="sentinel-banner">
          <div class="sentinel-kicker">SIAMS · OBSERVACIÓN SATELITAL</div>
          <h2>Vegetación y agua superficial en {escape(nombre_territorio)}</h2>
          <p>Explora tres productos visuales complementarios: actividad vegetal (NDVI),
          agua identificada por un índice espectral (MNDWI) y agua clasificada mediante
          Sentinel-2 (SCL). Las animaciones permiten examinar el territorio a lo largo del tiempo.</p>
        </div>
        """).strip(), unsafe_allow_html=True,
    )

    if not animaciones:
        st.info(
            f"Aún no se encontraron GIF de Sentinel-2 para **{nombre_territorio}**. "
            "Cuando los agregues, aparecerán automáticamente aquí."
        )
        st.code(str(carpeta), language=None)
        esperados = SENTINEL_ARCHIVOS_POR_TERRITORIO.get(nombre_territorio, {})
        if esperados:
            nombres = [nombre for grupo in esperados.values() for nombre in grupo.values()]
            st.caption("Archivos esperados: " + ", ".join(nombres))
        return

    anios = sorted(animaciones.keys(), reverse=True)
    c_anio, c_estado = st.columns([1.0, 2.0])
    with c_anio:
        if len(anios) > 1:
            anio = st.selectbox(
                "Año de las animaciones", anios,
                key=f"sentinel_anio_{normalizar_etiqueta(nombre_territorio)}",
            )
        else:
            anio = anios[0]
            st.markdown(f"**Año disponible:** {anio}")
    archivos = animaciones[anio]
    with c_estado:
        disponibles = ", ".join(tipo for tipo in ("NDVI", "MNDWI", "SCL") if tipo in archivos)
        st.caption(f"Productos disponibles: {disponibles}.  Carpeta: Sentinel/{carpeta.name}/")

    columnas = st.columns(3)
    tarjetas = (
        ("NDVI", "Vegetación", "Distribución y variación espacial de la actividad vegetal"),
        ("MNDWI", "Agua · índice", "Agua detectada por contraste entre verde y SWIR"),
        ("SCL", "Agua · clasificación", "Píxeles identificados como agua por la capa SCL"),
    )
    for columna, (tipo, titulo, resumen) in zip(columnas, tarjetas):
        with columna:
            meta = SENTINEL_DESCRIPCIONES[tipo]
            estado = "Disponible" if tipo in archivos else "Sin archivo"
            st.markdown(
                f'<div class="sentinel-method-card" style="border-top:4px solid {meta["color"]};">'
                f'<div class="sentinel-method-title">{titulo}</div>'
                f'<div class="sentinel-method-tag">{tipo} · {estado}</div>'
                f'<p>{resumen}</p></div>',
                unsafe_allow_html=True,
            )

    tab_ndvi, tab_mndwi, tab_scl, tab_comparacion = st.tabs([
        "🌳 Vegetación · NDVI", "💧 Agua · MNDWI", "🛰️ Agua · SCL", "🔎 Comparar métodos"
    ])
    with tab_ndvi:
        _panel_sentinel(nombre_territorio, "NDVI", archivos, anio)
    with tab_mndwi:
        _panel_sentinel(nombre_territorio, "MNDWI", archivos, anio)
    with tab_scl:
        _panel_sentinel(nombre_territorio, "SCL", archivos, anio)

    with tab_comparacion:
        st.markdown("### Comparación visual de la detección del agua")
        st.write(
            "MNDWI y SCL representan dos procedimientos de identificación de agua. "
            "Obsérvalos juntos para localizar diferencias aparentes en la continuidad "
            "del cauce o en píxeles de su entorno."
        )
        c_mndwi, c_scl = st.columns(2, gap="medium")
        for columna, tipo, titulo in (
            (c_mndwi, "MNDWI", "MNDWI · índice espectral"),
            (c_scl, "SCL", "SCL · clasificación de escena"),
        ):
            with columna:
                st.markdown(f"#### {titulo}")
                ruta = archivos.get(tipo)
                if ruta is None:
                    st.info(f"No se encontró el GIF de {tipo} para {anio}.")
                else:
                    _mostrar_gif_sentinel(ruta, titulo, f"{tipo} · {nombre_territorio} · {anio}")
        st.markdown(
            "**Interpretación:** las discrepancias visuales pueden relacionarse con el "
            "umbral usado para el MNDWI, la clasificación SCL, las sombras, los bordes "
            "del agua y otros efectos de adquisición o procesamiento."
        )
        st.warning(
            "Esta comparación es visual. Los GIF pueden reproducirse sin sincronización exacta "
            "entre fotogramas. Para calcular coincidencias, áreas o diferencias de píxeles "
            "se necesitan las máscaras originales georreferenciadas y las fechas correspondientes."
        )

    with st.expander("📖 Metodología e interpretación de los índices", expanded=False):
        st.markdown(
            "**NDVI:** `(NIR − Rojo) / (NIR + Rojo)`. El intervalo teórico es de −1 a +1. "
            "Si una animación muestra de 0 a 1, su escala puede haber sido recortada o normalizada "
            "durante la visualización."
        )
        st.markdown(
            "**MNDWI:** `(Verde − SWIR) / (Verde + SWIR)`. Identifica candidatos a agua "
            "mediante un criterio espectral y un umbral definido en el procesamiento."
        )
        st.markdown(
            "**SCL:** capa Scene Classification del producto Sentinel-2 Level-2A; "
            "la clase 6 representa agua. Es una clasificación, no una medición directa del cauce."
        )
        st.caption(
            "Los GIF son productos visuales generados previamente. La plataforma los presenta, "
            "pero no recalcula los índices ni valida su exactitud espacial a partir del GIF."
        )

    st.caption(
        "Fuente satelital indicada por el proyecto: Sentinel-2. Visualizaciones procesadas "
        "externamente e integradas en SIAMS para exploración académica."
    )

__all__ = ['CARPETA_SENTINEL', 'CARPETAS_SENTINEL_POR_TERRITORIO', 'SENTINEL_ARCHIVOS_POR_TERRITORIO', 'SENTINEL_DESCRIPCIONES', 'carpeta_sentinel_territorio', 'buscar_animaciones_sentinel', '_mostrar_gif_sentinel', '_panel_sentinel', 'mostrar_sentinel_territorio']
