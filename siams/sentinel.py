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
            "NDVI": "animacion_NDVI_2025 Leticia.mp4",
            "MNDWI": "animacion_MNDWI_2025 Leticia.mp4",
            "SCL": "animacion_SCL_2025 Leticia.mp4",
        },
    },
    "Arauca": {
        2025: {
            "NDVI": "animacion_NDVI_2025 Arauca.gif",
            "MNDWI": "animacion_MNDWI_2025 Arauca.gif",
            "SCL": "animacion_SCL_2025 Arauca.gif",
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

def _tokens_nombre_sentinel(texto: str) -> list[str]:
    """Tokeniza nombres con espacios, guiones, mayúsculas o tildes."""
    sin_tildes = "".join(
        letra for letra in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(letra)
    )
    return re.findall(r"[a-z0-9]+", sin_tildes)


def buscar_animaciones_sentinel(nombre_territorio: str) -> dict:
    """Busca MP4 o GIF por sede y año; prefiere MP4 si coexisten ambos.

    Admite, por ejemplo, 'animacion_MNDWI_2025 Leticia.mp4' y
    'animacion_mndwi_2025_leticia.gif', sin mezclar sedes.
    """
    carpeta = carpeta_sentinel_territorio(nombre_territorio)
    if not carpeta.is_dir():
        return {}

    encontrados: dict[int, dict[str, Path]] = {}

    # Los nombres registrados tienen prioridad cuando hay varias copias
    # del mismo formato, pero cualquier MP4 prevalece sobre un GIF.
    for anio, indices in SENTINEL_ARCHIVOS_POR_TERRITORIO.get(nombre_territorio, {}).items():
        for tipo, nombre_archivo in indices.items():
            ruta = carpeta / nombre_archivo
            if ruta.is_file():
                encontrados.setdefault(anio, {})[tipo] = ruta

    tokens_sede = _tokens_nombre_sentinel(nombre_territorio)
    for ruta in sorted(carpeta.iterdir(), key=lambda p: p.name.casefold()):
        if not ruta.is_file() or ruta.suffix.casefold() not in (".mp4", ".gif"):
            continue

        tokens = _tokens_nombre_sentinel(ruta.stem)
        # Comprobación explícita de la sede en el nombre para evitar mezclas.
        if not any(tokens[i:i + len(tokens_sede)] == tokens_sede
                   for i in range(len(tokens) - len(tokens_sede) + 1)):
            continue

        tipo = next((t.upper() for t in tokens if t.upper() in SENTINEL_DESCRIPCIONES), None)
        anio_texto = next((t for t in tokens if len(t) == 4 and t.isdigit()
                           and 2000 <= int(t) <= 2100), None)
        if tipo is None or anio_texto is None:
            continue

        anio = int(anio_texto)
        actual = encontrados.setdefault(anio, {}).get(tipo)
        if actual is None or (actual.suffix.casefold() == ".gif" and ruta.suffix.casefold() == ".mp4"):
            encontrados[anio][tipo] = ruta

    return encontrados


def _mostrar_gif_sentinel(ruta: Path, titulo: str, descripcion: str) -> None:
    """Muestra un MP4 en bucle o conserva el visor GIF heredado."""
    if ruta.suffix.casefold() == ".mp4":
        # Silenciado: los navegadores permiten así la reproducción automática.
        st.video(
            str(ruta),
            format="video/mp4",
            autoplay=True,
            loop=True,
            muted=True,
        )
        st.caption(descripcion)
    else:
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
            mime="video/mp4" if ruta.suffix.casefold() == ".mp4" else "image/gif",
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
            f"Aún no se encontraron animaciones MP4 o GIF de Sentinel-2 para **{nombre_territorio}**. "
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

    # Cada video se inserta una sola vez: evita StreamlitDuplicateElementId
    # sin usar key, que no está admitido por st.video en esta versión.
    tab_ndvi, tab_mndwi, tab_scl = st.tabs([
        "🌳 Vegetación · NDVI", "💧 Agua · MNDWI", "🛰️ Agua · SCL"
    ])
    with tab_ndvi:
        _panel_sentinel(nombre_territorio, "NDVI", archivos, anio)
    with tab_mndwi:
        _panel_sentinel(nombre_territorio, "MNDWI", archivos, anio)
    with tab_scl:
        _panel_sentinel(nombre_territorio, "SCL", archivos, anio)

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
            "Los GIF y MP4 son productos visuales generados previamente. La plataforma los presenta, "
            "pero no recalcula los índices ni valida su exactitud espacial a partir de estas animaciones."
        )

    st.caption(
        "Fuente satelital indicada por el proyecto: Sentinel-2. Visualizaciones procesadas "
        "externamente e integradas en SIAMS para exploración académica."
    )

__all__ = ['CARPETA_SENTINEL', 'CARPETAS_SENTINEL_POR_TERRITORIO', 'SENTINEL_ARCHIVOS_POR_TERRITORIO', 'SENTINEL_DESCRIPCIONES', 'carpeta_sentinel_territorio', 'buscar_animaciones_sentinel', '_mostrar_gif_sentinel', '_panel_sentinel', 'mostrar_sentinel_territorio']
