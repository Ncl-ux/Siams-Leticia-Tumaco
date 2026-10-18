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
    # SIAMS_M1_MP4_PRECEDENCIA: MP4 primero; GIF de respaldo.
    video = buscar_archivo_exacto(CARPETA_GIFS, Path(nombre_archivo).with_suffix('.mp4').name)
    if video is not None:
        return video
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
            # SIAMS_M1_MP4_PRECEDENCIA: reproducir video en bucle, conservando imagen alternativa.
            if ruta.suffix.casefold() == '.mp4':
                st.video(str(ruta), autoplay=True, loop=True, muted=True)
                st.caption(f"{item['descripcion']} · Fuente: HydroWeb / SWOT")
            else:
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

    # M7: la revisión tabular queda al lado de las tarjetas originales.
    # Esta llamada no modifica tarjetas ni animaciones ni requiere cambios en app.py.
    mostrar_control_calidad_swot(nombre_territorio)

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



# ================================================================
# M7 · TRAZABILIDAD Y CONTROL EXPLORATORIO DE SERIES SWOT / HYDROWEB
# Los CSV normalizados viven en la carpeta EXISTENTE Tarjetas_SWOT.
# Se mantienen las imágenes de tarjetas y los GIF sin alteraciones.
# ================================================================

def _archivos_series_swot(nombre_territorio: str) -> list[Path]:
    """Descubre solo los CSV consolidados de la sede; no confunde ríos."""
    nombres = {
        "Leticia": "Leticia", "Tumaco": "Tumaco",
        "Medellín": "Medellin", "Arauca": "Arauca",
    }
    clave = nombres.get(nombre_territorio)
    carpeta_series = CARPETA_PROYECTO / "data/processed/swot"
    if not carpeta_series.is_dir():
        carpeta_series = CARPETA_TARJETAS_SWOT
    if clave is None or not carpeta_series.is_dir():
        return []
    # Acepta archivos futuros del tipo SWOT_Tumaco_Mira_reach_...csv,
    # además de los actuales SWOT_Leticia_reach_...csv.
    return sorted(
        ruta for ruta in carpeta_series.glob(f"SWOT_{clave}*_reach_*.csv")
        if ruta.is_file()
    )


def _leer_serie_swot_m7(ruta: Path) -> pd.DataFrame:
    """Valida fechas y columnas, sin excluir ni imputar observaciones."""
    datos = pd.read_csv(ruta, encoding="utf-8-sig", dtype={"reach_id": str})
    requeridas = {
        "reach_id", "fecha_utc", "wse_m", "wse_incertidumbre_m",
        "ancho_m", "ancho_incertidumbre_m", "area_m2",
        "area_incertidumbre_m2", "pendiente_m_m",
        "pendiente_incertidumbre_m_m", "revisar_salto_wse",
        "bandera_calidad_oficial", "salto_absoluto_wse_m",
        "umbral_robusto_salto_wse_m",
    }
    faltantes = sorted(requeridas.difference(datos.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(faltantes)}")
    if datos.empty:
        raise ValueError("El CSV no contiene observaciones")
    datos["fecha_utc"] = pd.to_datetime(datos["fecha_utc"], utc=True, errors="coerce")
    if datos["fecha_utc"].isna().any():
        raise ValueError("Hay fechas UTC ilegibles")
    if datos["fecha_utc"].duplicated().any():
        raise ValueError("Hay fechas duplicadas en el mismo reach")
    if datos["reach_id"].isna().any() or datos["reach_id"].nunique() != 1:
        raise ValueError("Un CSV debe contener un único reach_id")
    columnas_numericas = [
        "wse_m", "wse_incertidumbre_m", "ancho_m", "ancho_incertidumbre_m",
        "area_m2", "area_incertidumbre_m2", "pendiente_m_m",
        "pendiente_incertidumbre_m_m", "salto_absoluto_wse_m",
        "umbral_robusto_salto_wse_m",
    ]
    for columna in columnas_numericas:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")
    # En HydroWeb algunas fechas solo poseen ancho/área u otras variables.
    # Mantener la fecha y mostrar el vacío WSE, sin imputar ni desplazar filas.
    if datos["wse_m"].notna().sum() < 2:
        raise ValueError("No hay suficientes observaciones WSE para el control exploratorio")
    datos = datos.sort_values("fecha_utc").reset_index(drop=True)
    datos["revisar_salto_wse"] = datos["revisar_salto_wse"].astype(str).str.upper().str.strip()
    if not datos["revisar_salto_wse"].isin({"SI", "NO"}).all():
        raise ValueError("Alertas diferentes de SI/NO en la columna revisar_salto_wse")
    # Verifica que la alerta declarada concuerda con el umbral documentado.
    alertas_recalculadas = (
        datos["salto_absoluto_wse_m"] > datos["umbral_robusto_salto_wse_m"]
    ).fillna(False)
    if (alertas_recalculadas != datos["revisar_salto_wse"].eq("SI")).any():
        raise ValueError("Las alertas no coinciden con el umbral robusto del archivo")
    return datos


def _estado_calidad_swot_m7(datos: pd.DataFrame) -> str:
    """No confunde un texto marcador con una bandera oficial de RiverSP."""
    contenido = set(datos["bandera_calidad_oficial"].dropna().astype(str).str.strip().unique())
    ausentes = {"", "NO_PRESENTE_EN_CSV", "NO_PRESENTES", "SIN_DATO", "nan"}
    return "Sin banderas oficiales" if not contenido or contenido.issubset(ausentes) else "Revisar metadatos de banderas"


def mostrar_control_calidad_swot(nombre_territorio: str) -> None:
    """Muestra resultados M7 sin sustituir el control oficial RiverSP."""
    archivos = _archivos_series_swot(nombre_territorio)
    if not archivos:
        # En otras sedes se conserva por completo el aspecto de la sección actual.
        return

    st.markdown("### Control de calidad y trazabilidad de datos · M7")
    st.caption(
        "Series de HydroWeb/SWOT por reach. Se muestran datos e incertidumbres originales; "
        "las alertas son estadísticas y NO equivalen a banderas oficiales de calidad."
    )
    if nombre_territorio == "Tumaco":
        st.info(
            "Los reaches de Tumaco están organizados por prefijo de identificador "
            "(672050001 y 672050012). Su correspondencia con los ríos Mira y Rosario "
            "debe confirmarse con el mapa o el catálogo HydroWeb; no se asignan por suposiciones."
        )
    grupos: dict[str, pd.DataFrame] = {}
    problemas = []
    for ruta in archivos:
        try:
            tabla = _leer_serie_swot_m7(ruta)
            identificador = str(tabla["reach_id"].iloc[0])
            if identificador in grupos:
                problemas.append(f"{ruta.name}: reach_id repetido; no se mezclaron archivos")
                continue
            grupos[identificador] = tabla
        except (OSError, UnicodeError, ValueError, pd.errors.ParserError) as error:
            problemas.append(f"{ruta.name}: {error}")

    for error in problemas:
        st.warning(f"No se incorporó este archivo SWOT: {error}")
    if not grupos:
        st.info("No hay series SWOT M7 válidas para mostrar.")
        return

    resumen = []
    for identificador, tabla in sorted(grupos.items()):
        mascara = tabla["revisar_salto_wse"].eq("SI")
        resumen.append({
            "Reach ID": identificador,
            "Fechas registradas": len(tabla),
            "WSE disponible": int(tabla["wse_m"].notna().sum()),
            "Fechas incompletas": int(tabla[["wse_m", "ancho_m", "area_m2", "pendiente_m_m"]].isna().any(axis=1).sum()),
            "Primera fecha UTC": tabla["fecha_utc"].min().strftime("%Y-%m-%d"),
            "Última fecha UTC": tabla["fecha_utc"].max().strftime("%Y-%m-%d"),
            "Saltos a revisar": int(mascara.sum()),
            "Salto máximo WSE (m)": round(float(tabla["salto_absoluto_wse_m"].max()), 3),
            "Calidad oficial": _estado_calidad_swot_m7(tabla),
        })
    resumen_df = pd.DataFrame(resumen)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tramos con datos", len(grupos))
    c2.metric("Fechas registradas", int(resumen_df["Fechas registradas"].sum()))
    c3.metric("Cambios para revisar", int(resumen_df["Saltos a revisar"].sum()))
    c4.metric("Con banderas oficiales", int((resumen_df["Calidad oficial"] != "Sin banderas oficiales").sum()))

    st.warning(
        "M7 todavía NO constituye validación oficial de SWOT. Estos CSV exportados "
        "no incluyen los indicadores reach_q/reach_q_b de RiverSP. "
        "Las incertidumbres y los saltos detectados no sustituyen esas banderas; "
        "no se descarta automáticamente ninguna observación."
    )
    st.dataframe(resumen_df, hide_index=True, use_container_width=True)
    seleccion = st.selectbox(
        "Tramo para revisar (reach_id)",
        sorted(grupos),
        format_func=lambda rid: (
            f"{grupos[rid]['grupo_reaches_por_prefijo'].iloc[0]} · Reach {rid}"
            if "grupo_reaches_por_prefijo" in grupos[rid].columns
            else f"Reach {rid}"
        ),
        key=f"swot_m7_reach_{nombre_territorio}",
    )
    tabla = grupos[seleccion]
    alertas = tabla[tabla["revisar_salto_wse"].eq("SI")]
    faltantes = int(tabla[["wse_m", "ancho_m", "area_m2", "pendiente_m_m"]].isna().any(axis=1).sum())
    if faltantes:
        st.caption(
            f"{faltantes} fecha(s) presentan alguna variable ausente. "
            "Se conservan como vacíos; las fechas se cruzan exactamente en UTC."
        )
    p1, p2, p3 = st.tabs(["WSE y alertas", "Otras variables", "Datos y método"])

    with p1:
        figura = go.Figure()
        figura.add_trace(go.Scatter(
            x=tabla["fecha_utc"], y=tabla["wse_m"],
            mode="lines+markers", connectgaps=False,
            name="WSE (todas las mediciones)",
            customdata=tabla[["wse_incertidumbre_m"]].to_numpy(),
            hovertemplate=("Fecha: %{x|%Y-%m-%d %H:%M UTC}<br>"
                           "WSE: %{y:.3f} m<br>Incertidumbre: %{customdata[0]:.3f} m<extra></extra>"),
        ))
        if not alertas.empty:
            figura.add_trace(go.Scatter(
                x=alertas["fecha_utc"], y=alertas["wse_m"],
                mode="markers", marker={"symbol": "diamond", "size": 12, "color": "#E09A35"},
                name="Salto a revisar (no excluido)",
                hovertemplate="Fecha: %{x|%Y-%m-%d}<br>WSE: %{y:.3f} m<extra></extra>",
            ))
        figura.update_layout(
            title=f"Elevación del agua · reach {seleccion}",
            xaxis_title="Fecha (UTC)", yaxis_title="WSE (m)",
            hovermode="x unified", legend={"orientation": "h", "y": -0.2},
            margin={"b": 85},
        )
        st.plotly_chart(figura, use_container_width=True, key=f"swot_m7_wse_{nombre_territorio}")
        st.caption(
            f"Se marcaron {len(alertas)} de {len(tabla)} observaciones para revisar. "
            "El marcador naranja señala cambios bruscos entre fechas consecutivas; "
            "no implica que el dato sea erróneo."
        )
        if not alertas.empty:
            columnas_alerta = [
                "fecha_utc", "wse_m", "wse_incertidumbre_m",
                "salto_absoluto_wse_m", "dias_desde_anterior",
                "tramos_con_alerta_misma_fecha",
            ]
            st.dataframe(
                alertas[[c for c in columnas_alerta if c in alertas.columns]],
                hide_index=True, use_container_width=True,
            )

    with p2:
        variables = {
            "Ancho de río (m)": ("ancho_m", "ancho_incertidumbre_m", "m"),
            "Área superficial (m²)": ("area_m2", "area_incertidumbre_m2", "m²"),
            "Pendiente (m/m)": ("pendiente_m_m", "pendiente_incertidumbre_m_m", "m/m"),
        }
        nombre = st.selectbox(
            "Variable", list(variables), key=f"swot_m7_variable_{nombre_territorio}",
        )
        valor, incertidumbre, unidad = variables[nombre]
        f2 = go.Figure(go.Scatter(
            x=tabla["fecha_utc"], y=tabla[valor], mode="lines+markers", name=nombre,
            customdata=tabla[[incertidumbre]].to_numpy(),
            hovertemplate=(f"Fecha: %{{x|%Y-%m-%d}}<br>Valor: %{{y:.5g}} {unidad}"
                           f"<br>Incertidumbre: %{{customdata[0]:.5g}} {unidad}<extra></extra>"),
        ))
        f2.update_layout(
            title=f"{nombre} · reach {seleccion}", xaxis_title="Fecha (UTC)",
            yaxis_title=nombre, hovermode="x unified",
        )
        st.plotly_chart(f2, use_container_width=True, key=f"swot_m7_otra_{nombre_territorio}")
        st.caption("Los valores e incertidumbres proceden de los CSV originales, sin filtros automáticos; los vacíos se conservan.")

    with p3:
        st.markdown(
            "**Criterio exploratorio documentado:** para cada reach se calcula la serie de "
            "diferencias absolutas de WSE entre observaciones sucesivas. "
            "Una observación se marca cuando el salto supera "
            "`mediana(|ΔWSE|) + 6 × 1,4826 × MAD(|ΔWSE|)`. "
            "El umbral es estadístico; no es un límite hidrológico oficial, "
            "y los intervalos entre observaciones pueden ser irregulares."
        )
        st.info(
            "Pendiente: sin filtrado automático. Para cerrar M7 debemos recuperar las "
            "banderas oficiales del producto RiverSP y cotejar los resultados y tarjetas "
            "contra los CSV o productos que las generaron."
        )
        st.dataframe(tabla, hide_index=True, use_container_width=True)
        st.download_button(
            "Descargar datos del reach (CSV)",
            data=tabla.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"SWOT_{nombre_territorio}_reach_{seleccion}.csv",
            mime="text/csv", key=f"swot_m7_desc_{nombre_territorio}",
        )
        st.download_button(
            "Descargar resumen de control (CSV)",
            data=resumen_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"Resumen_Control_SWOT_{nombre_territorio}_M7.csv",
            mime="text/csv", key=f"swot_m7_resumen_{nombre_territorio}",
        )


__all__ = ['CARPETA_GIFS', 'GIFS_SWOT_POR_TERRITORIO', 'GIFS_SWOT_ANTIGUOS', 'buscar_gif_swot', 'mostrar_gifs_swot', 'CARPETA_TARJETAS_SWOT', 'TARJETAS_SWOT_POR_TERRITORIO', 'TARJETAS_SWOT_NOMBRES_NUEVOS', 'buscar_tarjeta_swot', '_mostrar_tarjetas_rio_swot', 'mostrar_tarjetas_swot', 'CARPETAS_BUSQUEDA_MAPAS', 'EXTENSIONES_IMAGEN', 'EXTENSIONES_MAPA']
