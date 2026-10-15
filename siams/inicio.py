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

from .catalogo import TERRITORIOS, UNAL_SEDES
from .utilidades import normalizar_etiqueta, resolver_carpeta_preferida, resolver_subcarpeta
from .mapas_datos import MAPAS_POR_TERRITORIO, MAPAS_UBICACION_QGIS
from .swot import GIFS_SWOT_POR_TERRITORIO, TARJETAS_SWOT_POR_TERRITORIO, buscar_gif_swot, buscar_tarjeta_swot
from .clima import ARCHIVOS_CLIMA_NASA, ARCHIVOS_IDEAM, archivo_nasa_territorio, cargar_clima_leticia, cargar_ideam_tumaco
from .cartografia import buscar_mapa
from .mapbiomas import CARPETA_COBERTURAS, COBERTURAS_POR_TERRITORIO, encontrar_csv_coberturas
from .landsat import inventario_landsat
from .sentinel import buscar_animaciones_sentinel

def obtener_hallazgos_clave(nombre_territorio: str):
    """Genera hallazgos breves para mostrar en la ficha territorial."""
    hallazgos = []

    try:
        archivo_ideam = ARCHIVOS_IDEAM.get(nombre_territorio)
        if archivo_ideam is not None:
            df_i, _, _, _ = cargar_ideam_tumaco(str(archivo_ideam))
            if "Precipitación IDEAM (mm)" in df_i.columns:
                fila = df_i.loc[df_i["Precipitación IDEAM (mm)"].idxmax()]
                hallazgos.append(
                    f"Mes más lluvioso: {fila['Mes']} "
                    f"({fila['Precipitación IDEAM (mm)']:.1f} mm, IDEAM)."
                )
            if "Temperatura media IDEAM (°C)" in df_i.columns:
                hallazgos.append(
                    f"Temperatura media mensual aproximada: "
                    f"{df_i['Temperatura media IDEAM (°C)'].mean():.1f} °C."
                )
        else:
            archivo = ARCHIVOS_CLIMA_NASA.get(nombre_territorio)
            if archivo is not None:
                df_n, _ = cargar_clima_leticia(str(archivo))
                p = "Precipitación mensual (mm)"
                t = "Temperatura media (°C)"
                if p in df_n.columns:
                    fila = df_n.loc[df_n[p].idxmax()]
                    hallazgos.append(
                        f"Mes más lluvioso: {fila['Mes']} ({fila[p]:.1f} mm, NASA POWER)."
                    )
                if t in df_n.columns:
                    hallazgos.append(
                        f"Temperatura media mensual aproximada: {df_n[t].mean():.1f} °C."
                    )
    except Exception:
        pass

    particularidades = {
        "Bogotá": "Piloto cartográfico multiescala con navegación desde Colombia hasta la Ciudad Universitaria.",
        "Leticia": "Alta humedad y fuerte relación con el sistema fluvial amazónico.",
        "Tumaco": "Interacción permanente entre sistemas fluviales, estuarinos y marino-costeros.",
        "Medellín": "Contexto urbano-andino con quebradas, fuertes pendientes y amenaza por inundación.",
        "San Andrés": "La disponibilidad de agua dulce está estrechamente ligada a la lluvia y los acuíferos.",
        "Arauca": "IDEAM aporta observación terrestre y NASA POWER permite contraste climático continuo.",
        "La Paz": "NASA POWER se usa como fuente climática única en esta versión del prototipo.",
    }
    hallazgos.append(particularidades.get(nombre_territorio, ""))

    return [h for h in hallazgos if h][:3]

def mostrar_mapa_sedes_unal() -> None:
    """Mapa nacional de sedes UNAL con los territorios priorizados por SIAMS."""
    df = UNAL_SEDES.copy()

    colores = {
        "Territorio integrado en SIAMS": "#20a67a",
        "Otra sede UNAL (contexto)": "#7c8a87",
    }

    fig = px.scatter_map(
        df,
        lat="lat",
        lon="lon",
        hover_name="Sede",
        hover_data={
            "Ciudad": True,
            "Estado": True,
            "Descripcion": True,
            "lat": False,
            "lon": False,
            "Tamano": False,
        },
        color="Estado",
        color_discrete_map=colores,
        size="Tamano",
        size_max=15,
        zoom=3.65,
        center={"lat": 4.8, "lon": -75.6},
        height=620,
    )

    fig.update_layout(
        map_style="carto-positron",
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            title="Leyenda",
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="rgba(0,0,0,0.10)",
            borderwidth=1,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    fig.update_traces(marker=dict(opacity=0.90))

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "scrollZoom": True,
        },
    )

    html = """
    <div class="soft-box">
        <strong>¿Qué significan los colores?</strong><br>
        🟢 <strong>Verde:</strong> territorios que ya están integrados en el prototipo SIAMS
        (Bogotá, Leticia, Tumaco, Medellín, San Andrés, Arauca y La Paz).<br>
        ⚪ <strong>Gris:</strong> otras sedes de la Universidad Nacional que se muestran
        únicamente como contexto institucional y todavía no tienen un módulo territorial
        desarrollado dentro de esta versión del prototipo.
    </div>
    """
    st.markdown(dedent(html).strip(), unsafe_allow_html=True)

def tabla_disponibilidad(nombre_territorio: str) -> pd.DataFrame:
    if nombre_territorio == "Bogotá":
        return pd.DataFrame({
            "Variable": [
                "Precipitación", "Temperatura", "Humedad relativa",
                "Viento", "Presión", "Radiación", "Calidad del agua",
            ],
            "Estado": ["Pendiente"] * 7,
            "Uso actual": [
                "No integrado en esta fase",
                "No integrado en esta fase",
                "No integrado en esta fase",
                "No integrado en esta fase",
                "No integrado en esta fase",
                "No integrado en esta fase",
                "No integrado en esta fase",
            ],
        })

    if nombre_territorio == "Arauca":
        return pd.DataFrame({
            "Variable": [
                "Precipitación", "Temperatura media", "Temperatura máxima",
                "Temperatura mínima", "Humedad relativa", "Viento", "Presión", "Radiación",
            ],
            "IDEAM": [
                "96.47 %", "97.80 % (derivada)", "98.54 %", "98.28 %",
                "97.26 % (con advertencia)", "No disponible", "No disponible", "No disponible",
            ],
            "NASA POWER": ["Disponible"] * 8,
            "Decisión": [
                "IDEAM principal; NASA compara",
                "IDEAM derivada; NASA compara",
                "IDEAM principal; NASA compara",
                "IDEAM principal; NASA compara",
                "IDEAM con advertencia; NASA contrasta",
                "NASA POWER", "NASA POWER", "NASA POWER",
            ],
        })

    if nombre_territorio in {"Leticia", "Medellín", "San Andrés", "La Paz"}:
        return pd.DataFrame({
            "Variable": [
                "Precipitación", "Temperatura media", "Temperaturas extremas",
                "Humedad relativa", "Viento", "Presión", "Radiación",
            ],
            "IDEAM / terrestre": [
                "Por consolidar", "Por consolidar", "Por consolidar",
                "Por consolidar", "Por consolidar", "Por consolidar", "Por consolidar",
            ],
            "NASA POWER": ["Disponible"] * 7,
            "Uso actual": ["NASA POWER"] * 7,
        })

    return pd.DataFrame({
        "Variable": [
            "Precipitación", "Temperatura media", "Temperatura máxima",
            "Temperatura mínima", "Humedad", "Viento", "Presión", "Radiación",
        ],
        "IDEAM": [
            "98.74 %", "80.76 %", "69.05 %", "73.80 %",
            "40.30 %", "No disponible", "No disponible", "No disponible",
        ],
        "NASA POWER": ["Disponible"] * 8,
        "Decisión": [
            "IDEAM principal; NASA para comparar",
            "IDEAM principal; NASA complementaria",
            "IDEAM con cautela; NASA complementaria",
            "IDEAM con cautela; NASA complementaria",
            "Mostrar ambas con advertencia",
            "NASA POWER", "NASA POWER", "NASA POWER",
        ],
    })

SIAMS_SEDES_PORTADA = {
    "Bogotá": {
        "icono": "🏛️", "tema": "Cartografía y localización",
        "descripcion": "Ubicación multiescala de la Ciudad Universitaria y exploración del contexto espacial.",
    },
    "Leticia": {
        "icono": "🌿", "tema": "Clima y sistemas amazónicos",
        "descripcion": "Datos hidrometeorológicos, cartografía ambiental y observaciones del río Amazonas.",
    },
    "Tumaco": {
        "icono": "🌊", "tema": "Ríos y ambiente costero",
        "descripcion": "Clima regional, manglares y dinámica de los ríos Mira y Rosario.",
    },
    "Medellín": {
        "icono": "⛰️", "tema": "Territorio urbano-andino",
        "descripcion": "Clima, geología, inundación y observaciones del río Medellín.",
    },
    "San Andrés": {
        "icono": "🏝️", "tema": "Agua dulce y acuíferos",
        "descripcion": "Clima insular, vulnerabilidad hidrogeológica y calidad del agua subterránea.",
    },
    "Arauca": {
        "icono": "🌾", "tema": "Agua y llanuras aluviales",
        "descripcion": "Contraste hidrometeorológico, sistema acuífero y observación del río Arauca.",
    },
    "La Paz": {
        "icono": "🌄", "tema": "Clima y agua subterránea",
        "descripcion": "Contexto del Cesar, información climática y almacenamiento hídrico satelital.",
    },
}

CARPETA_FOTOS_SEDES = resolver_carpeta_preferida("Fotos_Sedes", "Presentacion")

def foto_sede_portada(nombre_sede: str):
    """Localiza foto sin exigir tildes o extensiones uniformes; nunca usa otra sede."""
    if not CARPETA_FOTOS_SEDES.is_dir():
        return None
    objetivo = normalizar_etiqueta(nombre_sede)
    extensiones = {".jpg", ".jpeg", ".png", ".webp"}
    for ruta in sorted(CARPETA_FOTOS_SEDES.iterdir(), key=lambda p: p.name.casefold()):
        if (ruta.is_file() and ruta.suffix.casefold() in extensiones
                and normalizar_etiqueta(ruta.stem) == objetivo):
            return ruta
    return None

@st.cache_data(show_spinner=False, max_entries=20)
def foto_sede_data_uri(ruta_texto: str, fecha_cambio_ns: int) -> str:
    """Crea una miniatura liviana en memoria. No modifica el JPG original del proyecto."""
    ruta = Path(ruta_texto)
    try:
        from io import BytesIO
        from PIL import Image, ImageOps
        with Image.open(ruta) as imagen:
            foto = ImageOps.exif_transpose(imagen).convert("RGB")
            # La imagen se recorta solamente al visualizarse (object-fit: cover).
            foto.thumbnail((900, 750), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            foto.save(buffer, format="JPEG", quality=82, optimize=True)
            contenido = buffer.getvalue()
        return "data:image/jpeg;base64," + base64.b64encode(contenido).decode("ascii")
    except (ImportError, OSError, ValueError):
        mime = "image/png" if ruta.suffix.casefold() == ".png" else (
            "image/webp" if ruta.suffix.casefold() == ".webp" else "image/jpeg"
        )
        return "data:" + mime + ";base64," + base64.b64encode(ruta.read_bytes()).decode("ascii")

def recursos_reales_sede_portada(nombre: str) -> list[str]:
    """Solo se muestran recursos con evidencia de un archivo real."""
    etiquetas = []

    def existe(ruta):
        return ruta is not None and Path(ruta).is_file()

    try:
        if existe(ARCHIVOS_IDEAM.get(nombre)):
            etiquetas.append("IDEAM")
        if existe(archivo_nasa_territorio(nombre)):
            etiquetas.append("NASA POWER")
        if any(buscar_mapa(n["archivo"]) is not None
               for n in MAPAS_UBICACION_QGIS.get(nombre, [])):
            etiquetas.append("QGIS")
        if any(buscar_mapa(ruta) is not None
               for ruta in MAPAS_POR_TERRITORIO.get(nombre, {}).values()):
            etiquetas.append("Mapas temáticos")
        if any(buscar_gif_swot(item["archivo"]) is not None
               for item in GIFS_SWOT_POR_TERRITORIO.get(nombre, [])) or any(
                   buscar_tarjeta_swot(archivo) is not None
                   for rio in TARJETAS_SWOT_POR_TERRITORIO.get(nombre, [])
                   for archivo in rio["archivos"].values()
               ):
            etiquetas.append("SWOT")
        cfg_cob = COBERTURAS_POR_TERRITORIO.get(nombre)
        if cfg_cob:
            carpeta = resolver_subcarpeta(CARPETA_COBERTURAS, cfg_cob["carpeta"])
            if carpeta.is_dir() and any(f.is_file() and f.suffix.casefold() in {".csv", ".gif"}
                                        for f in carpeta.iterdir()):
                etiquetas.append("MapBiomas")
        landsat = inventario_landsat(nombre)
        if landsat["gifs"] or existe(landsat["areas"]):
            etiquetas.append("Landsat")
        if buscar_animaciones_sentinel(nombre):
            etiquetas.append("Sentinel-2")
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return etiquetas

def _fecha_valida_portada(valor):
    """Convierte fecha Excel/texto sin confundir un año 2025 con nanosegundos Unix."""
    if valor is None or pd.isna(valor):
        return None
    try:
        if isinstance(valor, (int, float)):
            valor_n = float(valor)
            if valor_n.is_integer() and 1900 <= valor_n <= 2100:
                fecha = pd.Timestamp(year=int(valor_n), month=1, day=1)
            elif 20000 <= valor_n <= 65000:
                fecha = pd.Timestamp("1899-12-30") + pd.to_timedelta(valor_n, unit="D")
            else:
                return None
        else:
            texto = str(valor).strip()
            if re.fullmatch(r"(?:19|20)\d{2}", texto):
                fecha = pd.Timestamp(year=int(texto), month=1, day=1)
            else:
                # ISO YYYY-MM-DD ya declara año/mes/día: no invertir mes y día.
                if re.match(r"^\d{4}-\d{1,2}-\d{1,2}", texto):
                    fecha = pd.to_datetime(valor, errors="coerce", yearfirst=True)
                else:
                    fecha = pd.to_datetime(valor, errors="coerce", dayfirst=True)
        if pd.isna(fecha) or not 1900 <= fecha.year <= 2100:
            return None
        return pd.Timestamp(fecha)
    except (TypeError, ValueError, OverflowError):
        return None

@st.cache_data(show_spinner=False, max_entries=40)
def periodo_excel_sede_portada(ruta_texto: str, fecha_cambio_ns: int):
    """Obtiene años extremos de indicadores/metadata de un Excel NASA o IDEAM.

    No inspecciona nombres de archivos como si fueran años de observación.
    No lee climatologías mensuales como series históricas.
    """
    try:
        with pd.ExcelFile(ruta_texto) as libro:
            hojas = {normalizar_etiqueta(nombre): nombre for nombre in libro.sheet_names}
            inicios, finales = [], []
            if "indicadores" in hojas:
                tabla = pd.read_excel(libro, sheet_name=hojas["indicadores"])
                if len(tabla.columns) >= 2:
                    for etiqueta, valor in tabla.iloc[:, :2].itertuples(index=False, name=None):
                        campo = normalizar_etiqueta(etiqueta)
                        if "fecha" not in campo:
                            continue
                        fecha = _fecha_valida_portada(valor)
                        if fecha is None:
                            continue
                        if any(p in campo for p in ("inicial", "inicio", "primera")):
                            inicios.append(fecha)
                        elif any(p in campo for p in ("final", "fin", "ultima")):
                            finales.append(fecha)
            if not (inicios and finales):
                # Algunos Excel IDEAM ponen periodos por estación/variable en estas hojas.
                for candidato in ("fuentes", "control_faltantes"):
                    if candidato not in hojas:
                        continue
                    tabla = pd.read_excel(libro, sheet_name=hojas[candidato])
                    campos = {normalizar_etiqueta(c): c for c in tabla.columns}
                    columnas_inicio = [c for n, c in campos.items()
                                      if "fecha" in n and ("inicio" in n or "inicial" in n)]
                    columnas_fin = [c for n, c in campos.items()
                                   if "fecha" in n and ("final" in n or "fin" in n)]
                    for c in columnas_inicio:
                        inicios.extend(f for v in tabla[c].dropna().tolist()
                                       if (f := _fecha_valida_portada(v)) is not None)
                    for c in columnas_fin:
                        finales.extend(f for v in tabla[c].dropna().tolist()
                                       if (f := _fecha_valida_portada(v)) is not None)
            if inicios and finales:
                inicio, fin = min(inicios), max(finales)
                if inicio <= fin:
                    return (int(inicio.year), int(fin.year))
    except (OSError, ValueError, KeyError, ImportError, TypeError):
        pass
    return None

@st.cache_data(show_spinner=False, max_entries=48)
def periodo_csv_mapbiomas_portada(ruta_texto: str, fecha_cambio_ns: int):
    """Extrae años de las columnas del CSV de serie temporal (sin sumar datos)."""
    try:
        try:
            tabla = pd.read_csv(ruta_texto, nrows=0, sep=None,
                                engine="python", encoding="utf-8-sig")
        except UnicodeDecodeError:
            tabla = pd.read_csv(ruta_texto, nrows=0, sep=None,
                                engine="python", encoding="cp1252")
        anios = sorted(int(str(c).strip()) for c in tabla.columns
                      if re.fullmatch(r"(?:19|20)\d{2}", str(c).strip()))
        if anios:
            return (anios[0], anios[-1])
    except (OSError, ValueError, TypeError):
        pass
    return None

def periodos_reales_sede_portada(nombre: str) -> list[tuple[str, str]]:
    """Periodos de cobertura de FUENTES distintas, no un único rango inventado."""
    resultado = []
    for etiqueta, ruta in (
        ("IDEAM", ARCHIVOS_IDEAM.get(nombre)),
        ("NASA POWER", archivo_nasa_territorio(nombre)),
    ):
        if ruta is None or not Path(ruta).is_file():
            continue
        periodo = periodo_excel_sede_portada(str(ruta), Path(ruta).stat().st_mtime_ns)
        if periodo:
            resultado.append((etiqueta, f"{periodo[0]}–{periodo[1]}"))

    configuracion = COBERTURAS_POR_TERRITORIO.get(nombre)
    if configuracion:
        rangos = []
        for zona in configuracion["zonas"]:
            archivos = encontrar_csv_coberturas(nombre, zona)
            for ruta in archivos.get("serie", []):
                periodo = periodo_csv_mapbiomas_portada(
                    str(ruta), ruta.stat().st_mtime_ns
                )
                if periodo is not None:
                    rangos.append(periodo)
        if rangos:
            resultado.append(("MapBiomas", f"{min(p[0] for p in rangos)}–{max(p[1] for p in rangos)}"))
    return resultado

def ir_a_ficha_sede_siams(nombre: str) -> None:
    """Cambia widgets del sidebar mediante callback, antes del rerun."""
    st.session_state["siams_nav_territorio"] = nombre
    st.session_state["siams_nav_grupo"] = "Territorio"
    st.session_state["siams_nav_contenido_territorio"] = "Resumen territorial"

def mostrar_sintesis_sedes_inicio() -> None:
    """Galería uniforme 4+3, con fotos y fechas verificadas automáticamente."""
    st.markdown(
        '<div class="siams-home-kicker">SIAMS EN COLOMBIA</div>'
        '<div class="section-title" style="margin-top:0">Conoce nuestras sedes</div>'
        '<p class="siams-home-subtitle">Una mirada rápida a los territorios, '
        'los estudios y los periodos de información disponibles en el semillero.</p>',
        unsafe_allow_html=True,
    )
    orden = ["Bogotá", "Leticia", "Tumaco", "Medellín", "San Andrés", "Arauca", "La Paz"]
    # Se usan siempre cuatro columnas: las tres últimas no se ensanchan.
    # Así TODAS las tarjetas miden igual en escritorio.
    for comienzo in (0, 4):
        columnas = st.columns(4, gap="medium")
        for columna, nombre in zip(columnas, orden[comienzo:comienzo + 4]):
            datos = SIAMS_SEDES_PORTADA[nombre]
            region = TERRITORIOS[nombre]["region"]
            recursos = recursos_reales_sede_portada(nombre)
            periodos = periodos_reales_sede_portada(nombre)
            ruta_foto = foto_sede_portada(nombre)
            if ruta_foto is not None:
                imagen = foto_sede_data_uri(str(ruta_foto), ruta_foto.stat().st_mtime_ns)
                visual = (
                    '<div class="siams-sede-media">'
                    f'<img src="{imagen}" alt="Fotografía de {escape(nombre)}" loading="lazy">'
                    f'<span class="siams-sede-photo-label">{escape(nombre)}</span>'
                    '</div>'
                )
            else:
                visual = (
                    '<div class="siams-sede-media siams-sede-media--empty" '
                    f'title="Falta imagen de {escape(nombre)} en Presentacion">'
                    f'{datos["icono"]}</div>'
                )

            # Se prioriza dar fechas por cada FUENTE. Muestra hasta 3 rangos por tarjeta.
            lineas_fecha = "".join(
                '<div class="siams-sede-date-row">'
                f'<span class="siams-sede-date-source">{escape(fuente)}:</span> '
                f'{escape(rango)}</div>'
                for fuente, rango in periodos[:3]
            )
            if not lineas_fecha:
                lineas_fecha = '<div class="siams-sede-empty">Periodos pendientes de verificar</div>'

            visibles = recursos[:3]
            etiquetas = "".join(
                f'<span class="siams-sede-tag">{escape(recurso)}</span>'
                for recurso in visibles
            )
            if len(recursos) > len(visibles):
                etiquetas += f'<span class="siams-sede-tag">+{len(recursos) - len(visibles)}</span>'
            if not etiquetas:
                etiquetas = '<span class="siams-sede-empty">Recursos por integrar</span>'

            html = (
                '<div class="siams-sede-content">'
                + visual +
                '<div class="siams-sede-body">'
                f'<span class="siams-sede-region">{escape(str(region))}</span>'
                f'<div class="siams-sede-title">{escape(nombre)}</div>'
                f'<div class="siams-sede-focus">{escape(datos["tema"])}</div>'
                f'<p class="siams-sede-description">{escape(datos["descripcion"])}</p>'
                '<div class="siams-sede-dates">'
                '<div class="siams-sede-date-heading">PERIODOS CON DATOS</div>'
                + lineas_fecha + '</div>'
                f'<div class="siams-sede-tags">{etiquetas}</div>'
                '</div></div>'
            )
            with columna:
                with st.container(border=True):
                    st.markdown(html, unsafe_allow_html=True)
                    st.button(
                        "Explorar esta sede  →",
                        key=f"siams_portada_abrir_{normalizar_etiqueta(nombre)}",
                        use_container_width=True,
                        on_click=ir_a_ficha_sede_siams,
                        args=(nombre,),
                    )

    st.markdown(
        '<p class="siams-home-note">'
        'Los periodos corresponden a las fechas declaradas en los Excel de IDEAM/NASA POWER '
        'y a los años presentes en las series CSV de MapBiomas. '
        'Un intervalo entre dos años no implica que existan datos todos los días ni para todas '
        'las variables. SWOT, Landsat y otras fuentes se consultan en cada módulo. '
        'Cuando no se puede comprobar una fecha, se muestra como pendiente.</p>',
        unsafe_allow_html=True,
    )

__all__ = ['obtener_hallazgos_clave', 'mostrar_mapa_sedes_unal', 'tabla_disponibilidad', 'SIAMS_SEDES_PORTADA', 'CARPETA_FOTOS_SEDES', 'foto_sede_portada', 'foto_sede_data_uri', 'recursos_reales_sede_portada', '_fecha_valida_portada', 'periodo_excel_sede_portada', 'periodo_csv_mapbiomas_portada', 'periodos_reales_sede_portada', 'ir_a_ficha_sede_siams', 'mostrar_sintesis_sedes_inicio']
