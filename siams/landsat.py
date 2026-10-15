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

from .utilidades import CARPETA_PROYECTO, normalizar_etiqueta

CARPETA_LANDSAT = CARPETA_PROYECTO / "Landsat"

COLORES_LANDSAT = {
    "Agua": "#2b83ba",
    "Bosque": "#1a9850",
    "Pastos / vegetación baja": "#91cf60",
    "Agricultura / mosaico": "#fee08b",
    "Urbano / construido": "#d73027",
    "Suelo desnudo": "#b15928",
    "Humedal / zona húmeda": "#74add1",
}

def carpeta_landsat_sede(nombre_territorio: str):
    """Encuentra la subcarpeta Landsat independientemente de acentos/espacios."""
    if not CARPETA_LANDSAT.is_dir():
        return None
    objetivo = normalizar_etiqueta(nombre_territorio)
    for carpeta in sorted(CARPETA_LANDSAT.iterdir(), key=lambda p: p.name.casefold()):
        if carpeta.is_dir() and normalizar_etiqueta(carpeta.name) == objetivo:
            return carpeta
    return None

def inventario_landsat(nombre_territorio: str) -> dict:
    """Devuelve todos los GIF disponibles y los CSV existentes para una sede."""
    carpeta = carpeta_landsat_sede(nombre_territorio)
    if carpeta is None:
        return {"carpeta": None, "gifs": [], "areas": None, "control": None}
    archivos = [p for p in carpeta.iterdir() if p.is_file()]
    gifs = sorted(
        [p for p in archivos if p.suffix.casefold() == ".gif"
         and normalizar_etiqueta(p.stem).startswith("gif_landsat")],
        key=lambda p: p.name.casefold(),
    )
    def csv_buscar(nombre):
        return next((p for p in archivos if p.name.casefold() == nombre.casefold()), None)
    return {
        "carpeta": carpeta,
        "gifs": gifs,
        "areas": csv_buscar("Areas_coberturas_por_fecha.csv"),
        "control": csv_buscar("Control_escenas.csv"),
    }

def anio_gif_landsat(ruta: Path):
    coincidencias = re.findall(r"(?<!\d)(?:19\d{2}|20\d{2})(?!\d)", ruta.stem)
    return int(coincidencias[-1]) if coincidencias else None

@st.cache_data(show_spinner=False)
def leer_csv_landsat(ruta: str, actualizado: int) -> pd.DataFrame:
    """Acepta CSV UTF-8, BOM o separador de punto y coma; recarga si cambia."""
    try:
        return pd.read_csv(ruta, encoding="utf-8-sig", sep=None, engine="python")
    except UnicodeDecodeError:
        return pd.read_csv(ruta, encoding="latin-1", sep=None, engine="python")

def _leer_landsat_si_existe(ruta):
    if ruta is None or not ruta.exists():
        return None
    try:
        return leer_csv_landsat(str(ruta), ruta.stat().st_mtime_ns)
    except Exception as error:
        st.warning(f"No se pudo leer `{ruta.name}`: {error}")
        return None

def _tabla_areas_landsat(datos: pd.DataFrame):
    """Extrae fecha y clases en hectáreas sin asumir columnas ajenas a la clasificación."""
    if datos is None or datos.empty:
        return pd.DataFrame(), []
    columnas = {normalizar_etiqueta(c): c for c in datos.columns}
    columna_fecha = next((columnas[c] for c in ("fecha", "date", "datetime") if c in columnas), None)
    if columna_fecha is None:
        return pd.DataFrame(), []
    df = datos.copy()
    df["Fecha"] = pd.to_datetime(df[columna_fecha], errors="coerce")
    clases = []
    for original in COLORES_LANDSAT:
        c = columnas.get(normalizar_etiqueta(original))
        if c is not None:
            df[original] = pd.to_numeric(df[c], errors="coerce")
            clases.append(original)
    if not clases:
        return pd.DataFrame(), []
    df = df.dropna(subset=["Fecha"]).sort_values("Fecha").reset_index(drop=True)
    df["Área clasificada (ha)"] = df[clases].clip(lower=0).sum(axis=1)
    return df, clases

@st.cache_data(show_spinner=False, max_entries=12)
def preparar_gif_landsat_lento(
    ruta_texto: str,
    fecha_modificacion_ns: int,
    ancho_maximo_px: int,
    duracion_ms: int,
) -> tuple[bytes, int]:
    """Redimensiona y ralentiza un GIF sin alterar el archivo original.

    El mtime se incluye en la clave de caché para actualizar la vista previa
    cuando el usuario reemplaza el GIF en su carpeta de Landsat.
    """
    from io import BytesIO
    from PIL import Image, ImageSequence

    fotogramas = []
    with Image.open(ruta_texto) as gif_origen:
        for fotograma in ImageSequence.Iterator(gif_origen):
            imagen = fotograma.convert("RGB")
            # No ampliamos archivos pequeños: solo reducimos los demasiado grandes.
            if imagen.width > ancho_maximo_px:
                alto = max(1, round(imagen.height * ancho_maximo_px / imagen.width))
                imagen = imagen.resize(
                    (ancho_maximo_px, alto), Image.Resampling.LANCZOS
                )
            # Paleta por fotograma para preservar colores de clase y texto.
            fotogramas.append(
                imagen.quantize(
                    colors=192,
                    method=Image.Quantize.MEDIANCUT,
                    dither=Image.Dither.NONE,
                )
            )

    if not fotogramas:
        raise ValueError("El archivo GIF no contiene fotogramas legibles.")

    salida = BytesIO()
    fotogramas[0].save(
        salida,
        format="GIF",
        save_all=True,
        append_images=fotogramas[1:],
        duration=duracion_ms,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return salida.getvalue(), len(fotogramas)

def mostrar_landsat_territorio(nombre_territorio: str) -> None:
    """Panel Landsat para animación, áreas estimadas y trazabilidad de escenas."""
    inv = inventario_landsat(nombre_territorio)
    st.markdown("### 🛰️ Landsat · evolución por fechas disponibles")
    st.write(
        "Animaciones con observaciones Landsat de fechas reales: cada fotograma "
        "muestra una clasificación espectral preliminar en el entorno seleccionado. "
        "La animación omite fechas sin observaciones aprovechables."
    )
    if not inv["gifs"]:
        st.info(
            f"Todavía no hay GIF Landsat de {nombre_territorio} en `Landsat/{nombre_territorio}`. "
            "Agrega el GIF y los dos CSV exportados desde Colab a esa carpeta."
        )
        return

    archivos_gif = inv["gifs"]
    if len(archivos_gif) > 1:
        ruta_gif = st.selectbox(
            "Año de observación",
            archivos_gif,
            format_func=lambda p: f"{anio_gif_landsat(p) or 'Sin año'} · {p.name}",
            key=f"landsat_gif_{normalizar_etiqueta(nombre_territorio)}",
        )
    else:
        ruta_gif = archivos_gif[0]
    anio = anio_gif_landsat(ruta_gif)
    st.caption(
        f"Sede: {nombre_territorio} · Año: {anio if anio else 'no especificado'} · "
        "Fuente: Landsat Collection 2 Level 2 · Resolución nominal: 30 m"
    )
    if len(archivos_gif) > 1:
        st.info(
            "Hay varios GIF en la carpeta. Los CSV con nombres genéricos pueden "
            "corresponder a un único año; antes de compararlos, comprueba sus fechas."
        )

    df_areas_original = _leer_landsat_si_existe(inv["areas"])
    df_control = _leer_landsat_si_existe(inv["control"])
    df_areas, clases = _tabla_areas_landsat(df_areas_original)

    # Un CSV compartido no debe mostrarse como si perteneciera a otro GIF/año.
    if anio is not None and not df_areas.empty:
        presentes = df_areas["Fecha"].dt.year.dropna().unique().tolist()
        if anio not in presentes:
            st.warning(
                f"El archivo de áreas no contiene fechas de {anio}. "
                "Se ocultan las estadísticas para evitar mezclar años."
            )
            df_areas = pd.DataFrame()
            clases = []
        else:
            df_areas = df_areas.loc[df_areas["Fecha"].dt.year.eq(anio)].copy()

    if df_control is not None and not df_control.empty:
        cols = {normalizar_etiqueta(c): c for c in df_control.columns}
        col_fecha = cols.get("fecha")
        if col_fecha is not None and anio is not None:
            fechas_ctl = pd.to_datetime(df_control[col_fecha], errors="coerce")
            df_control = df_control.loc[fechas_ctl.dt.year.eq(anio)].copy()

    vistas = st.tabs(["🎞️ Animación", "📈 Series de coberturas", "🔎 Calidad y descargas"])
    with vistas[0]:
        st.markdown(f"#### {nombre_territorio} · animación Landsat {anio or ''}")
        # Estos controles sí modifican el tamaño de salida y el tiempo real
        # de cada frame; st.image del GIF original no permitiría ralentizarlo.
        control_tamano, control_velocidad = st.columns(2)
        with control_tamano:
            ancho_gif = st.select_slider(
                "Tamaño de la animación",
                options=[280, 320, 360, 400, 440],
                value=360,
                format_func=lambda n: f"{n} px",
                key=f"landsat_tamano_{normalizar_etiqueta(nombre_territorio)}",
            )
        with control_velocidad:
            segundos_frame = st.slider(
                "Tiempo por fecha (segundos)",
                min_value=1.0,
                max_value=5.0,
                value=2.5,
                step=0.5,
                key=f"landsat_duracion_{normalizar_etiqueta(nombre_territorio)}",
            )

        gif_ajustado = None
        try:
            with st.spinner("Preparando animación Landsat a la velocidad seleccionada…"):
                gif_ajustado, cantidad_frames = preparar_gif_landsat_lento(
                    str(ruta_gif),
                    ruta_gif.stat().st_mtime_ns,
                    int(ancho_gif),
                    int(segundos_frame * 1000),
                )
        except Exception as error:
            st.warning(f"No se pudo ajustar el GIF: {error}. Se muestra el original.")

        # Ancho físico fijo en píxeles: no ocupa toda la pantalla en escritorio.
        _, columna_gif, _ = st.columns([1, 2, 1])
        with columna_gif:
            st.image(
                gif_ajustado if gif_ajustado is not None else str(ruta_gif),
                width=int(ancho_gif),
            )
        if gif_ajustado is not None:
            st.caption(
                f"Vista previa: {cantidad_frames} fotogramas originales; "
                f"{segundos_frame:g} segundos por fecha. "
                "Puedes descargar esta versión más lenta sin modificar tu GIF original."
            )
        st.caption(
            "Los colores representan clases estimadas por reglas espectrales y no una "
            "clasificación oficial de uso del suelo. El radio del buffer y las fechas "
            "deben consultarse en el GIF y en el registro de escenas."
        )
        boton_lento, boton_original = st.columns(2)
        with boton_lento:
            if gif_ajustado is not None:
                st.download_button(
                    "⬇️ Descargar GIF lento y compacto",
                    data=gif_ajustado,
                    file_name=f"{ruta_gif.stem}_lento_{segundos_frame:g}s.gif",
                    mime="image/gif",
                    key=f"landsat_desc_lento_{normalizar_etiqueta(nombre_territorio)}",
                    use_container_width=True,
                )
        with boton_original:
            st.download_button(
                "⬇️ Descargar GIF original",
                data=ruta_gif.read_bytes(),
                file_name=ruta_gif.name,
                mime="image/gif",
                key=f"landsat_desc_gif_{normalizar_etiqueta(nombre_territorio)}_{ruta_gif.name}",
                use_container_width=True,
            )
        st.markdown("**Leyenda de clases estimadas**")
        etiquetas = " ".join(
            f'<span style="display:inline-block;margin:0.15rem 0.45rem 0.3rem 0;'
            f'border:1px solid rgba(125,125,125,.25);border-radius:8px;padding:5px 8px;">'
            f'<span style="display:inline-block;background:{color};width:11px;height:11px;'
            f'border-radius:2px;margin-right:7px;"></span>{escape(nombre)}</span>'
            for nombre, color in COLORES_LANDSAT.items()
        )
        st.markdown(etiquetas, unsafe_allow_html=True)

    with vistas[1]:
        if df_areas.empty:
            st.info("No hay un CSV de áreas compatible con el año seleccionado.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Fechas con áreas clasificadas", len(df_areas))
            c2.metric("Categorías representadas", len(clases))
            c3.metric("Área clasificada en última fecha", f"{df_areas['Área clasificada (ha)'].iloc[-1]:,.1f} ha")
            modalidad = st.radio(
                "Cómo representar las coberturas",
                ["Superficie estimada (ha)", "Participación dentro del área clasificada (%)"],
                horizontal=True,
                key=f"landsat_modo_{normalizar_etiqueta(nombre_territorio)}",
            )
            largos = df_areas.melt(id_vars=["Fecha", "Área clasificada (ha)"],
                                   value_vars=clases, var_name="Cobertura", value_name="Superficie (ha)")
            if modalidad.startswith("Participación"):
                largos["Valor"] = (
                    100 * largos["Superficie (ha)"] /
                    largos["Área clasificada (ha)"].where(largos["Área clasificada (ha)"].gt(0))
                )
                y, unidad = "Valor", "% del área clasificada"
            else:
                y, unidad = "Superficie (ha)", "Superficie estimada (ha)"
            fig = px.line(
                largos, x="Fecha", y=y, color="Cobertura", markers=True,
                color_discrete_map=COLORES_LANDSAT,
                labels={"Fecha": "Fecha de observación", y: unidad},
            )
            fig.update_layout(
                height=470, margin=dict(l=10, r=10, t=25, b=5),
                legend_title_text="Cobertura", hovermode="x unified",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True,
                            key=f"landsat_serie_{normalizar_etiqueta(nombre_territorio)}")
            st.caption(
                "Superficies estimadas según píxeles clasificados a 30 m (ha). "
                "El área despejada puede variar entre fechas: una disminución observada "
                "no equivale necesariamente a pérdida real de cobertura. "
                "Los porcentajes se calculan respecto del área clasificada en cada fecha."
            )
            with st.expander("Ver tabla de coberturas por fecha"):
                st.dataframe(df_areas[["Fecha"] + clases + ["Área clasificada (ha)"]],
                             hide_index=True, use_container_width=True)
            if inv["areas"]:
                st.download_button(
                    "⬇️ Descargar áreas originales (CSV)", inv["areas"].read_bytes(),
                    file_name=inv["areas"].name, mime="text/csv",
                    key=f"landsat_areas_{normalizar_etiqueta(nombre_territorio)}",
                )

    with vistas[2]:
        st.markdown("#### Control de escenas y trazabilidad")
        if df_control is None or df_control.empty:
            st.info("No hay registros de control para el año seleccionado.")
        else:
            cols = {normalizar_etiqueta(c): c for c in df_control.columns}
            estado_col = cols.get("estado")
            if estado_col:
                aceptadas = df_control[estado_col].astype(str).str.casefold().str.contains("aceptad", na=False).sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("Escenas examinadas", len(df_control))
                c2.metric("Escenas aceptadas", int(aceptadas))
                c3.metric("Escenas descartadas", int(len(df_control)-aceptadas))
            fraccion_col = cols.get("fraccion_util")
            if fraccion_col:
                fraccion = pd.to_numeric(df_control[fraccion_col], errors="coerce")
                st.caption(
                    "Fracción útil: proporción aproximada del buffer con píxeles "
                    "aprovechables en cada escena; no es el porcentaje de nubosidad del catálogo."
                )
                df_control = df_control.copy()
                df_control["Cobertura útil (%)"] = (fraccion * 100).round(1)
            st.dataframe(df_control, hide_index=True, use_container_width=True)
            if inv["control"]:
                st.download_button(
                    "⬇️ Descargar control original (CSV)", inv["control"].read_bytes(),
                    file_name=inv["control"].name, mime="text/csv",
                    key=f"landsat_control_{normalizar_etiqueta(nombre_territorio)}",
                )

        with st.expander("Ficha técnica y consideraciones metodológicas"):
            st.markdown(
                "**Fuente:** imágenes Landsat Collection 2, Level 2 (reflectancia superficial).  "
                "**Resolución espacial nominal:** 30 m.  "
                "**Intervalo temporal:** escenas efectivamente disponibles del año indicado.  "
                "**Procesamiento:** filtro de nubosidad, máscara QA_PIXEL e índices "
                "espectrales (NDVI, NDWI, NDBI, BSI), con reglas heurísticas.  "
                "**Área de estudio:** buffer definido al generar los fotogramas en Colab. "
                "La animación no permite cambiar ese buffer desde Streamlit."
            )
            st.warning(
                "Producto exploratorio sin validación independiente de exactitud. "
                "Las clases agricultura, urbano y humedal pueden confundirse "
                "espectralmente; no usar para cuantificar transformación real "
                "del suelo sin verificación de campo o datos de referencia."
            )

__all__ = ['CARPETA_LANDSAT', 'COLORES_LANDSAT', 'carpeta_landsat_sede', 'inventario_landsat', 'anio_gif_landsat', 'leer_csv_landsat', '_leer_landsat_si_existe', '_tabla_areas_landsat', 'preparar_gif_landsat_lento', 'mostrar_landsat_territorio']
