from pathlib import Path

from textwrap import dedent

from html import escape

import logging

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

logger = logging.getLogger(__name__)

VERSION_APP = "PROTOTIPO-SIAMS-V42-GRACE-M10-2026-10-16"

FECHA_ACTUALIZACION = "16 de octubre de 2026"

MODO_DESARROLLO = False

CARPETA_APP = Path(__file__).resolve().parent

_ICONOS_VALIDOS = {"icono de siams.jpeg", "icono de siams.jpg", "icono de siams.png"}

ICONO_SIAMS = next(
    (
        archivo for archivo in CARPETA_APP.iterdir()
        if archivo.is_file() and archivo.name.casefold() in _ICONOS_VALIDOS
    ),
    None,
)

st.set_page_config(
    page_title="SIAMS | Plataforma Hidroambiental",
    page_icon=str(ICONO_SIAMS) if ICONO_SIAMS is not None else "💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

from siams.estilos import aplicar_estilos
aplicar_estilos()

from siams.catalogo import MESES, UNAL_SEDES, TERRITORIOS, ESTADO_COMPONENTES, METADATOS_MAPAS, FUENTES_CLIMATICAS
from siams.utilidades import normalizar_etiqueta, resolver_carpeta_preferida, resolver_subcarpeta, buscar_archivo_exacto, buscar_excel_climatico, _fechas_desde_dataframe, CARPETA_PROYECTO, CARPETA_DATOS_HIDRO
from siams.grace import encontrar_archivo_gws, ARCHIVO_GWS, cargar_dataset_gws, distancia_haversine_km, extraer_gws_territorio, climatologia_gws, calcular_ggdi

# Complementos de Leticia; un fallo de importación no bloquea las demás sedes.
try:
    from siams.grace_leticia import mostrar_grace_leticia
    ERROR_MODULO_GRACE_LETICIA = None
except ImportError as error:
    mostrar_grace_leticia = None
    ERROR_MODULO_GRACE_LETICIA = str(error)

try:
    from siams.hidrogeoquimica import mostrar_hidrogeoquimica
    ERROR_MODULO_HIDROGEOQUIMICA = None
except ImportError as error:
    mostrar_hidrogeoquimica = None
    ERROR_MODULO_HIDROGEOQUIMICA = str(error)
from siams.tendencias import VARIABLES_TENDENCIA, _buscar_columna_variable, extraer_series_historicas_excel, agregar_serie_anual, mann_kendall, pendiente_sen, analizar_serie_tendencia
from siams.tendencias import mann_kendall_hamed_rao  # SIAMS_M5_IMPORTADO
from siams.componentes import clase_estado, mostrar_semaforo, resumen_estados, mostrar_ficha_mapa, interpretacion_leticia, interpretacion_nasa, interpretacion_ideam_nasa, interpretacion_tumaco, archivo_disponible, territorio_actual, mostrar_encabezado, mostrar_tarjeta
from siams.mapas_datos import MAPAS_LETICIA, MAPAS_TUMACO, MAPAS_MEDELLIN, MAPAS_SAN_ANDRES, MAPAS_ARAUCA, MAPAS_BOGOTA, MAPAS_UBICACION_QGIS, FICHA_QGIS_REFERENCIA, MAPAS_POR_TERRITORIO, encontrar_carpeta_mapas, CARPETA_MAPAS_QGIS, CARPETA_MAPAS
from siams.swot import CARPETA_GIFS, GIFS_SWOT_POR_TERRITORIO, GIFS_SWOT_ANTIGUOS, buscar_gif_swot, mostrar_gifs_swot, CARPETA_TARJETAS_SWOT, TARJETAS_SWOT_POR_TERRITORIO, TARJETAS_SWOT_NOMBRES_NUEVOS, buscar_tarjeta_swot, _mostrar_tarjetas_rio_swot, mostrar_tarjetas_swot, CARPETAS_BUSQUEDA_MAPAS, EXTENSIONES_IMAGEN, EXTENSIONES_MAPA
from siams.clima import series_tendencia_territorio, encontrar_archivo_excel, encontrar_archivo_clima_leticia, ARCHIVO_CLIMA_LETICIA, convertir_fecha_excel, cargar_clima_leticia, ARCHIVO_NASA_TUMACO, ARCHIVO_IDEAM_TUMACO, ARCHIVO_IDEAM_ARAUCA, ARCHIVO_CLIMA_MEDELLIN, ARCHIVO_CLIMA_SAN_ANDRES, ARCHIVO_CLIMA_ARAUCA, ARCHIVO_CLIMA_LA_PAZ, ARCHIVOS_CLIMA_NASA, ARCHIVOS_NASA, ARCHIVOS_IDEAM, archivo_nasa_territorio, cargar_nasa_tumaco, cargar_ideam_tumaco, decisiones_climaticas_ideam, decisiones_climaticas_tumaco, periodo_texto, clima_prototipo
from siams.cartografia import MAPAS_QGIS_NOMBRES_NUEVOS, buscar_mapa, mostrar_pdf_mapa, _circulo_geografico, mostrar_mapa_interactivo_bogota, mostrar_mapa_interactivo_territorio, mostrar_ficha_tecnica_qgis, mostrar_navegador_ubicacion_bogota, mostrar_navegador_ubicacion_qgis
from siams.mapbiomas import CARPETA_COBERTURAS, COBERTURAS_POR_TERRITORIO, COLORES_COBERTURAS, encontrar_csv_coberturas, MAPBIOMAS_GIFS_POR_TERRITORIO, MAPBIOMAS_GIFS_NOMBRES_ANTIGUOS, buscar_gif_mapbiomas, _mostrar_gif_mapbiomas, mostrar_presentacion_cobertura_mapbiomas, buscar_csv_natural_antropico, _tipo_natural_antropico, _numero_antnat, cargar_csv_natural_antropico, mostrar_analisis_natural_antropico, cargar_csv_cobertura, preparar_cobertura_nivel, comparar_coberturas, mostrar_resumen_coberturas, mostrar_analisis_coberturas_nivel, mostrar_coberturas_mapbiomas
from siams.landsat import CARPETA_LANDSAT, COLORES_LANDSAT, carpeta_landsat_sede, inventario_landsat, anio_gif_landsat, leer_csv_landsat, _leer_landsat_si_existe, _tabla_areas_landsat, preparar_gif_landsat_lento, mostrar_landsat_territorio
from siams.sentinel import CARPETA_SENTINEL, CARPETAS_SENTINEL_POR_TERRITORIO, SENTINEL_ARCHIVOS_POR_TERRITORIO, SENTINEL_DESCRIPCIONES, carpeta_sentinel_territorio, buscar_animaciones_sentinel, _mostrar_gif_sentinel, _panel_sentinel, mostrar_sentinel_territorio
from siams.estados import actualizar_estado_coberturas, actualizar_estado_landsat
from siams.inicio import obtener_hallazgos_clave, mostrar_mapa_sedes_unal, tabla_disponibilidad, SIAMS_SEDES_PORTADA, CARPETA_FOTOS_SEDES, foto_sede_portada, foto_sede_data_uri, recursos_reales_sede_portada, _fecha_valida_portada, periodo_excel_sede_portada, periodo_csv_mapbiomas_portada, periodos_reales_sede_portada, ir_a_ficha_sede_siams, mostrar_sintesis_sedes_inicio

# =========================================================
# NASA POWER · Compatibilidad A2 y A3 (solo en app.py)
# Se conservan sin modificar siams/clima.py, siams/tendencias.py
# y los complementos nuevos de GRACE e hidrogeoquímica.
# =========================================================


def _columna_nasa(df: pd.DataFrame, opciones: tuple[str, ...], hoja: str) -> str:
    """Reconoce encabezados antiguos y A2/A3 sin confundir variables."""
    actuales = {normalizar_etiqueta(col): col for col in df.columns}
    for candidato in opciones:
        encontrada = actuales.get(normalizar_etiqueta(candidato))
        if encontrada is not None:
            return encontrada
    raise ValueError(
        f"La hoja {hoja} no tiene ninguna de las columnas esperadas: "
        + ", ".join(opciones)
    )


@st.cache_data(show_spinner=False)
def _leer_nasa_climatologia_a2a3(ruta: str, version_archivo: tuple[int, int], tumaco_ideam: bool = False):
    """Carga regímenes antiguos/A2-A3; no transforma valores numéricos."""
    p = pd.read_excel(ruta, sheet_name="Regimen_P")
    t = pd.read_excel(ruta, sheet_name="Regimen_T")
    hr = pd.read_excel(ruta, sheet_name="Regimen_HR")
    clim = pd.read_excel(ruta, sheet_name="Climatologia_mensual")
    indicadores_df = pd.read_excel(ruta, sheet_name="Indicadores")

    col_p = _columna_nasa(p, (
        "precipitacion_media_mensual_multianual_mm_mes",
        "precipitacion_media_mensual_mm_mes",
        "precipitacion_acumulada_mm_mes",
        "precipitacion_mm_dia",
    ), "Regimen_P")
    # Regimen_P representa la MEDIA de acumulados de cada mes, no lluvia diaria.
    etiqueta_p = "Precipitación NASA (mm)" if tumaco_ideam else "Precipitación mensual (mm)"
    p = p[["mes", col_p]].rename(columns={col_p: etiqueta_p})

    temp = {
        "temperatura_media_C": "Temperatura media NASA (°C)" if tumaco_ideam else "Temperatura media (°C)",
        "temperatura_maxima_C": "Temperatura máxima NASA (°C)" if tumaco_ideam else "Temperatura máxima (°C)",
        "temperatura_minima_C": "Temperatura mínima NASA (°C)" if tumaco_ideam else "Temperatura mínima (°C)",
    }
    columnas_t = ["mes"]
    renombrar_t = {}
    for original, destino in temp.items():
        if original in t.columns:
            columnas_t.append(original)
            renombrar_t[original] = destino
        elif original == "temperatura_media_C":
            raise ValueError("Regimen_T no contiene temperatura_media_C")
    t = t[columnas_t].rename(columns=renombrar_t)

    col_hr = _columna_nasa(hr, ("humedad_relativa_pct",), "Regimen_HR")
    etiqueta_hr = "Humedad NASA (%)" if tumaco_ideam else "Humedad relativa (%)"
    hr = hr[["mes", col_hr]].rename(columns={col_hr: etiqueta_hr})

    col_radiacion = _columna_nasa(clim, (
        "radiacion_solar_media_diaria_MJ_m2_dia",
        "radiacion_solar_media_MJ_m2_dia",
        "radiacion_solar_MJ_m2_dia",
        "radiacion_solar_kWh_m2_dia",
    ), "Climatologia_mensual")
    # Los seis Excel de SIAMS se generaron con POWER AG. El campo antiguo decía
    # kWh, pero el procesamiento original no convirtió el valor entregado en MJ.
    # La corrección es de ETIQUETA; no se multiplica ni divide la serie.
    m = " NASA" if tumaco_ideam else ""
    otras = clim[["mes", "viento_2m_m_s", "presion_superficie_kPa", col_radiacion]].rename(
        columns={
            "viento_2m_m_s": f"Viento a 2 m{m} (m/s)",
            "presion_superficie_kPa": f"Presión{m} (kPa)" if tumaco_ideam else "Presión superficial (kPa)",
            col_radiacion: f"Radiación{m} (MJ/m²/día)" if tumaco_ideam else "Radiación solar (MJ/m²/día)",
        }
    )

    df = p.merge(t, on="mes", how="inner").merge(hr, on="mes", how="inner")
    df = df.merge(otras, on="mes", how="inner").sort_values("mes").reset_index(drop=True)
    df["Mes"] = df["mes"].map(dict(enumerate(MESES, start=1)))
    df = df.drop(columns="mes")
    orden = ["Mes", etiqueta_p, *renombrar_t.values(), etiqueta_hr, *otras.columns.drop("mes")]
    df = df[orden]

    indicadores = dict(zip(indicadores_df["Indicador"].astype(str), indicadores_df["Valor"]))
    for clave in ("Fecha inicial", "Fecha final"):
        if clave in indicadores:
            indicadores[clave] = convertir_fecha_excel(indicadores[clave])
    return df, indicadores


def cargar_clima_leticia(ruta_texto: str):
    """Lector adaptado A2/A3 para todas las sedes NASA sin cambiar clima.py."""
    archivo = Path(ruta_texto)
    st_archivo = archivo.stat()
    return _leer_nasa_climatologia_a2a3(str(archivo), (st_archivo.st_mtime_ns, st_archivo.st_size))


def cargar_nasa_tumaco(ruta_texto: str):
    """Lector compatible NASA POWER + IDEAM para Tumaco y Arauca."""
    archivo = Path(ruta_texto)
    st_archivo = archivo.stat()
    return _leer_nasa_climatologia_a2a3(str(archivo), (st_archivo.st_mtime_ns, st_archivo.st_size), True)


_series_tendencia_original = series_tendencia_territorio


def series_tendencia_territorio(nombre_territorio: str, info_territorio: dict):
    """Preserva IDEAM/GRACE e incluye radiación MJ y excluye años NASA parciales."""
    paquetes = _series_tendencia_original(nombre_territorio, info_territorio)
    ruta = archivo_nasa_territorio(nombre_territorio)
    if ruta is None or not Path(ruta).is_file():
        return paquetes

    try:
        diarios = pd.read_excel(ruta, sheet_name="Datos_diarios")
        col_rad = _columna_nasa(diarios, (
            "radiacion_solar_MJ_m2_dia", "radiacion_solar_kWh_m2_dia",
        ), "Datos_diarios")
        fechas = diarios["fecha"].map(convertir_fecha_excel)
        valores = pd.to_numeric(diarios[col_rad], errors="coerce")
        serie_rad = pd.DataFrame({"Fecha": fechas, "Valor": valores}).dropna()
        serie_rad = serie_rad.sort_values("Fecha").drop_duplicates(subset="Fecha", keep="last")
        if len(serie_rad) >= 20 and serie_rad["Fecha"].dt.year.nunique() >= 3:
            paquetes["Radiación solar"] = {
                "serie": serie_rad.reset_index(drop=True),
                "unidad": "MJ/m²/día",
                "agregacion": "mean",
                "fuente": "NASA POWER",
                "archivo": Path(ruta).name,
                "hoja": "Datos_diarios",
            }

        # El último año del archivo NO debe analizarse como completo si no
        # existen registros hasta el 31 de diciembre. No alteramos IDEAM/GWSa.
        fechas_validas = fechas.dropna()
        if not fechas_validas.empty:
            ultima = fechas_validas.max()
            if (ultima.month, ultima.day) != (12, 31):
                for paquete in paquetes.values():
                    if paquete.get("fuente") == "NASA POWER":
                        tabla = paquete["serie"]
                        paquete["serie"] = tabla.loc[
                            pd.to_datetime(tabla["Fecha"], errors="coerce").dt.year < ultima.year
                        ].reset_index(drop=True)
    except (ValueError, KeyError, OSError) as error:
        # Un libro NASA incompleto no debe bloquear los análisis IDEAM ni GRACE.
        st.warning(f"No se pudo revisar la serie diaria NASA de {nombre_territorio}: {error}")
    return paquetes

# M10 · Vacíos temporales de GRACE (sin interpolación)
def _siams_meses_grace_con_vacios(tabla: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Crea un eje mensual íntegro y deja NaN en los meses sin observación.

    Solo se usa para VISUALIZAR. No modifica las mediciones, el GGDI,
    los cálculos estadísticos ni los archivos de descarga originales.
    """
    nombres = [nombre for nombre in columnas if nombre in tabla.columns]
    if tabla.empty or not nombres:
        return pd.DataFrame(columns=["Fecha", *nombres])
    serie = tabla[["Fecha", *nombres]].copy()
    serie["Fecha"] = pd.to_datetime(serie["Fecha"], errors="coerce")
    serie = serie.dropna(subset=["Fecha"])
    if serie.empty:
        return pd.DataFrame(columns=["Fecha", *nombres])
    serie["_mes"] = serie["Fecha"].dt.to_period("M")
    serie = serie.sort_values("Fecha").drop_duplicates(subset="_mes", keep="last")
    eje = pd.period_range(serie["_mes"].min(), serie["_mes"].max(), freq="M")
    serie = serie.set_index("_mes")[nombres].reindex(eje)
    serie.index = serie.index.to_timestamp()
    return serie.rename_axis("Fecha").reset_index()


from siams.catalogo import restablecer_estados_componentes
restablecer_estados_componentes()
actualizar_estado_coberturas()
actualizar_estado_landsat()


def mostrar_mapa_imagen(
    clave: str,
    titulo: str,
    fuente: str,
    descripcion: str = "",
) -> None:
    """Muestra el mapa del territorio seleccionado o un aviso si falta el archivo."""
    mapas_disponibles = MAPAS_POR_TERRITORIO.get(territorio, {})
    nombre_base = mapas_disponibles.get(clave)

    if nombre_base is None:
        st.info(
            f"No se definió un mapa de **{clave.replace('_', ' ')}** para {territorio}."
        )
        return

    ruta = buscar_mapa(nombre_base)

    if ruta is None:
        st.warning(
            f"No se encontró el archivo **{nombre_base}** en la carpeta de mapas."
        )
        st.code(str(CARPETA_MAPAS), language=None)
        st.caption(
            "Verifica que la imagen esté descomprimida y que su nombre coincida. "
            "La extensión puede ser PNG, JPG, JPEG o WEBP."
        )
        if CARPETA_MAPAS.exists():
            disponibles = sorted(
                archivo.name for archivo in CARPETA_MAPAS.iterdir()
                if archivo.is_file() and archivo.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}
            )
            st.write("**Imágenes encontradas realmente:**")
            st.code("\n".join(disponibles) if disponibles else "Ninguna imagen encontrada", language=None)
        return

    # Se conserva el tamaño original para no agrandar artificialmente capturas pequeñas.
    st.image(
        str(ruta),
        caption=f"{titulo}. Fuente: {fuente}",
        use_container_width=False,
    )

    with open(ruta, "rb") as archivo_imagen:
        st.download_button(
            "Ver mapa en su resolución original",
            data=archivo_imagen.read(),
            file_name=ruta.name,
            mime=f"image/{ruta.suffix.lower().lstrip('.')}",
            key=f"descargar_{territorio}_{clave}_{ruta.name}",
        )

    st.caption(
        "La nitidez depende del archivo original. Para una mejora real conviene "
        "exportar nuevamente el mapa desde el PDF o SIG a 300 ppp; el código evita "
        "ampliarlo artificialmente dentro de la página."
    )

    mostrar_ficha_mapa(territorio, clave)

    if descripcion:
        st.markdown(descripcion)

if ICONO_SIAMS is not None:
    tipo_logo = "image/png" if ICONO_SIAMS.suffix.casefold() == ".png" else "image/jpeg"
    logo_base64 = base64.b64encode(ICONO_SIAMS.read_bytes()).decode("ascii")
    logo_html = (
        f'<img src="data:{tipo_logo};base64,{logo_base64}" '
        'alt="Logotipo del Semillero SIAMS">'
    )
else:
    logo_html = '<span class="siams-sidebar-brand__fallback" aria-hidden="true">💧</span>'

st.sidebar.markdown(
    '<div class="siams-sidebar-brand">'
    f'<div class="siams-sidebar-brand__logo">{logo_html}</div>'
    '<div class="siams-sidebar-brand__label">'
    '<strong>SIAMS</strong>'
    '<small>Plataforma hidroambiental</small>'
    '</div></div>',
    unsafe_allow_html=True,
)

territorio = st.sidebar.selectbox(
    "Territorio",
    ["Bogotá", "Leticia", "Tumaco", "Medellín", "San Andrés", "Arauca", "La Paz"],
    key="siams_nav_territorio",
)

grupo = st.sidebar.selectbox(
    "Sección principal",
    [
        "Inicio",
        "Territorio",
        "Clima y datos",
        "Subsuelo y calidad del agua",
        "Monitoreo",
        "Proyecto",
    ],
    key="siams_nav_grupo",
)

SUBMENUS = {
    "Inicio": [
        "Inicio",
    ],
    "Territorio": [
        "Resumen territorial",
        "Mapa y territorio",
        "Hidrología",
        "Cobertura y relieve",
        "Landsat",
        "Sentinel-2",
    ],
    "Clima y datos": [
        "Clima",
        "Análisis de tendencias",
        "Estaciones y datos",
    ],
    "Subsuelo y calidad del agua": [
        "Geología",
        "Hidrogeología",
        "Agua subterránea (GRACE)",
        "Hidrogeoquímica",
        "Calidad del agua e IRCA",
    ],
    "Monitoreo": [
        "Monitoreo y curvas",
        "Comparar territorios",
    ],
    "Proyecto": [
        "Metodología",
        "Fuentes y descargas",
        "Sobre SIAMS",
    ],
}

opciones_submenu = SUBMENUS[grupo]

if len(opciones_submenu) == 1:
    seccion = opciones_submenu[0]
else:
    seccion = st.sidebar.radio(
        "Contenido",
        opciones_submenu,
        key=f"siams_nav_contenido_{normalizar_etiqueta(grupo)}",
    )

st.sidebar.divider()

st.sidebar.caption("Prototipo académico. Información sujeta a revisión.")

st.sidebar.success(f"Versión activa: {VERSION_APP}")

if MODO_DESARROLLO:
    with st.sidebar.expander("Diagnóstico de archivos", expanded=False):
        st.write(f"**Script:** `{Path(__file__).name}`")
        st.write(f"**Carpeta de mapas temáticos:** `{CARPETA_MAPAS}`")
        st.write(f"**Raíz del proyecto:** `{CARPETA_PROYECTO}`")
        st.write(f"**Carpeta Excel:** `{CARPETA_DATOS_HIDRO}`")
        st.write(f"**Carpeta PDF QGIS:** `{CARPETA_MAPAS_QGIS}`")
        excel_detectados = sorted(
            archivo.name for archivo in CARPETA_DATOS_HIDRO.glob("*")
            if archivo.is_file() and archivo.suffix.casefold() == ".xlsx"
            and not archivo.name.startswith("~$")
        )
        st.write(f"**Excel detectados en {CARPETA_DATOS_HIDRO.name}:**")
        st.code("\n".join(excel_detectados) if excel_detectados else "Ningún Excel detectado", language=None)
        archivos_detectados = set()
        for carpeta_revision in CARPETAS_BUSQUEDA_MAPAS:
            if carpeta_revision.is_dir():
                for archivo in carpeta_revision.iterdir():
                    if archivo.is_file() and archivo.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp", ".pdf"}:
                        archivos_detectados.add(str(archivo.relative_to(CARPETA_PROYECTO)))
        st.write("**Mapas detectados:**")
        st.code("\n".join(sorted(archivos_detectados)) if archivos_detectados else "Ningún mapa detectado", language=None)
        st.write(f"**Carpeta Landsat:** `{CARPETA_LANDSAT}`")
        landsat_inv = inventario_landsat(territorio)
        st.write("**Landsat detectado para la sede:**")
        st.code(
            "\n".join([p.name for p in landsat_inv["gifs"]] +
                      [p.name for p in (landsat_inv["areas"], landsat_inv["control"]) if p is not None])
            or "Ningún archivo Landsat detectado",
            language=None,
        )
        st.write(f"**Carpeta de coberturas:** `{CARPETA_COBERTURAS}`")
        csv_detectados = []
        carpeta_tablas_mapbiomas = CARPETA_PROYECTO / "data/processed/mapbiomas"
        for config_cob in COBERTURAS_POR_TERRITORIO.values():
            carpeta_cob = resolver_subcarpeta(carpeta_tablas_mapbiomas, config_cob["carpeta"])
            if not carpeta_cob.is_dir():
                carpeta_cob = resolver_subcarpeta(CARPETA_COBERTURAS, config_cob["carpeta"])
            if carpeta_cob.is_dir():
                csv_detectados.extend(str(p.relative_to(CARPETA_PROYECTO)) for p in carpeta_cob.iterdir() if p.is_file() and p.suffix.casefold() == ".csv")
        st.code("\n".join(sorted(csv_detectados)) if csv_detectados else "Ningún CSV de coberturas detectado", language=None)
        gifs_detectados = []
        if CARPETA_GIFS.exists() and CARPETA_GIFS.is_dir():
            gifs_detectados = sorted(
                archivo.name for archivo in CARPETA_GIFS.iterdir()
                if archivo.is_file() and archivo.suffix.casefold() == ".gif"
            )
        st.write(f"**Carpeta GIF:** `{CARPETA_GIFS}`")
        st.write("**GIF SWOT detectados:**")
        st.code("\n".join(gifs_detectados) if gifs_detectados else "Ningún GIF detectado", language=None)

        tarjetas_detectadas = []
        if CARPETA_TARJETAS_SWOT.exists() and CARPETA_TARJETAS_SWOT.is_dir():
            tarjetas_detectadas = sorted(
                archivo.name for archivo in CARPETA_TARJETAS_SWOT.iterdir()
                if archivo.is_file() and archivo.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}
            )
        st.write(f"**Carpeta tarjetas SWOT:** `{CARPETA_TARJETAS_SWOT}`")
        st.write("**Tarjetas SWOT detectadas:**")
        st.code(
            "\n".join(tarjetas_detectadas) if tarjetas_detectadas else "Ninguna tarjeta SWOT detectada",
            language=None,
        )
        st.write(f"**NetCDF GWSa:** `{Path(ARCHIVO_GWS).name if ARCHIVO_GWS else 'No encontrado'}`")
        st.write(f"**Carpeta Sentinel:** `{carpeta_sentinel_territorio(territorio)}`")
        archivos_sentinel_detectados = buscar_animaciones_sentinel(territorio)
        lista_sentinel = [
            f"{anio} · {tipo}: {ruta.name}"
            for anio, grupo in sorted(archivos_sentinel_detectados.items(), reverse=True)
            for tipo, ruta in sorted(grupo.items())
        ]
        st.code("\n".join(lista_sentinel) if lista_sentinel else "Ningún GIF Sentinel detectado", language=None)

info = territorio_actual(territorio)

if seccion == "Inicio":
    mostrar_encabezado(
        "Plataforma hidroambiental SIAMS",
        "Un espacio para explorar información climática, hidrológica, geológica, "
        "hidrogeológica y de calidad del agua de los territorios estudiados por el semillero.",
    )

    # Síntesis ejecutiva visible sin desplegar mapas ni tablas.
    mostrar_sintesis_sedes_inicio()

    st.markdown("---")

    with st.expander("🗺️ Ver el mapa nacional de sedes", expanded=False):
        st.markdown(
            '<div class="section-title">Red de sedes de la Universidad Nacional de Colombia</div>',
            unsafe_allow_html=True,
        )

        st.write(
            "El mapa presenta la red de sedes de la Universidad Nacional de Colombia y "
            "resalta los territorios que actualmente hacen parte del prototipo SIAMS."
        )

        mostrar_mapa_sedes_unal()

        m0, m1, m2 = st.columns(3)
        m0.metric("Sedes UNAL ubicadas", f"{len(UNAL_SEDES)}")
        m1.metric("Territorios activos en SIAMS", f"{len(TERRITORIOS)}")
        m2.metric("Cobertura actual", "Bogotá D.C. · Amazonía · Caribe · Andina · Pacífico · Orinoquía · Cesar")

        st.caption(
            "La localización nacional permite contextualizar el alcance territorial del prototipo "
            "y visualizar las sedes priorizadas para esta fase de desarrollo."
        )

    with st.expander("📊 Ver cobertura técnica e indicadores del prototipo", expanded=False):
        st.markdown(
            '<div class="section-title">¿Qué contiene la plataforma?</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            mostrar_tarjeta(
                "Clima",
                "Series, regímenes mensuales, promedios, comparaciones y disponibilidad de datos.",
                "🌧️",
            )
        with c2:
            mostrar_tarjeta(
                "Territorio",
                "Mapas, hidrografía, humedales, cobertura, relieve y contexto espacial.",
                "🗺️",
            )
        with c3:
            mostrar_tarjeta(
                "Subsuelo y agua",
                "Geología, hidrogeología, GWSa, GGDI, hidrogeoquímica y calidad del agua.",
                "🪨",
            )
        with c4:
            mostrar_tarjeta(
                "Monitoreo",
                "Espacio reservado para series de nivel, sondas y curvas validadas.",
                "📡",
            )

        st.markdown(
            '<div class="section-title">Cobertura del prototipo</div>',
            unsafe_allow_html=True,
        )

        cobertura = pd.DataFrame({
            "Territorio": ["Bogotá", "Leticia", "Tumaco", "Medellín", "San Andrés", "Arauca", "La Paz"],
            "Ubicación": ["✅", "✅", "✅", "✅", "✅", "✅", "✅"],
            "Clima": ["—", "✅", "✅", "✅", "✅", "✅", "🟡"],
            "Hidrología": ["🟡", "✅", "✅", "🟡", "✅", "🟡", "—"],
            "Geología": ["—", "✅", "✅", "✅", "✅", "🟡", "—"],
            "Hidrogeología": ["—", "🟡", "🟡", "—", "✅", "🟡", "🟡"],
            "GWSa GRACE": ["—", "✅", "✅", "✅", "—", "✅", "✅"],
            "GGDI": ["—", "✅", "✅", "✅", "—", "✅", "✅"],
            "Calidad del agua": ["—", "🟡", "—", "—", "🟡", "—", "—"],
            "Monitoreo": ["—", "—", "—", "—", "—", "🟡", "🟡"],
        })

        st.dataframe(
            cobertura,
            use_container_width=True,
            hide_index=True,
        )

        st.caption("✅ incorporado · 🟡 parcial / en proceso · — pendiente o sin datos")

        st.markdown(
            '<div class="section-title">Estado del prototipo</div>',
            unsafe_allow_html=True,
        )

        mapas_encontrados = sum(
            1 for mapas in MAPAS_POR_TERRITORIO.values()
            for nombre in mapas.values()
            if buscar_mapa(nombre) is not None
        )
        mapas_esperados = sum(len(mapas) for mapas in MAPAS_POR_TERRITORIO.values())
        componentes_completos = sum(
            1 for territorio_estado in ESTADO_COMPONENTES.values()
            for _, estado, _ in territorio_estado
            if estado == "Completo"
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Territorios", f"{len(TERRITORIOS)}")
        m2.metric("Mapas incorporados", f"{mapas_encontrados}/{mapas_esperados}")
        m3.metric("Componentes completos", componentes_completos)
        m4.metric("Actualización", FECHA_ACTUALIZACION)

        st.info(
            "El prototipo diferencia información completa, información en proceso, "
            "componentes pendientes y secciones sin datos. No se presentan valores "
            "demostrativos como si fueran resultados reales."
        )

# =========================================================
# RESUMEN TERRITORIAL
# =========================================================

elif seccion == "Resumen territorial":
    mostrar_encabezado(
        territorio,
        info["descripcion"],
    )

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Región", info["region"])
    m2.metric("Departamento", info["departamento"])
    m3.metric("Área principal", info["area_principal"])
    m4.metric("Contexto regional", info["contexto"])

    st.markdown(dedent(f"""
        <div class="soft-box">
            <strong>Fuente climática principal:</strong> {info["fuente_clima"]}<br>
            <strong>Estado de los datos:</strong> {info["estado_datos"]}<br>
            <strong>Sede de referencia:</strong> {info["sede"]}
        </div>
        """).strip(), unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(
        [
            "Síntesis",
            "Hallazgos",
            "Pendientes",
        ]
    )

    with tab1:
        st.write(
            "Esta sección reúne una síntesis ambiental del territorio y sirve como punto "
            "de entrada para usuarios generales, estudiantes y personas con interés técnico."
        )

    with tab2:
        st.info(info["hallazgo"])

        st.markdown("### Hallazgos clave")
        hallazgos = obtener_hallazgos_clave(territorio)
        for hallazgo in hallazgos:
            st.markdown(f"- {hallazgo}")

    with tab3:
        pendientes = [
            (componente, nota)
            for componente, estado, nota in ESTADO_COMPONENTES[territorio]
            if estado in {"Pendiente", "Sin datos", "En proceso"}
        ]
        for componente, nota in pendientes:
            st.markdown(f"- **{componente}:** {nota}")

    st.markdown('<div class="section-title">Disponibilidad por componente</div>', unsafe_allow_html=True)
    mostrar_semaforo(territorio)

# =========================================================
# MAPA Y TERRITORIO
# =========================================================

elif seccion == "Mapa y territorio":
    st.title(f"🗺️ Ubicación territorial de {territorio}")

    if territorio in MAPAS_UBICACION_QGIS:
        # Los territorios con tres PDF QGIS se muestran en navegación multiescala.
        mostrar_navegador_ubicacion_qgis(territorio, info)

    else:
        st.write(
            "Este visor interactivo ubica la sede de referencia y permite explorar "
            "su contexto espacial con distintos niveles de acercamiento. Los mapas "
            "temáticos completos continúan en las secciones de hidrología, cobertura, "
            "relieve, geología, hidrogeología e IRCA."
        )

        mostrar_mapa_interactivo_territorio(
            territorio,
            info,
        )

        st.info(
            "El visor interactivo funciona como herramienta de ubicación y exploración. "
            "Los mapas temáticos existentes del proyecto se mantienen como productos "
            "cartográficos independientes dentro de sus respectivas secciones."
        )


# =========================================================
# CLIMA
# =========================================================

elif seccion == "Clima":
    st.title(f"🌧️ Clima de {territorio}")
    st.caption("SIAMS · análisis climático por fuente y calidad de datos")

    # -----------------------------------------------------
    # TUMACO Y ARAUCA: IDEAM terrestre + NASA POWER continuo
    # -----------------------------------------------------
    if territorio in {"Tumaco", "Arauca"}:
        archivo_ideam = ARCHIVOS_IDEAM.get(territorio)
        archivo_nasa = archivo_nasa_territorio(territorio)

        nombres_esperados = {
            'Tumaco': ('analisis_hidrometeorologico_tumaco.xlsx', 'nasa_power_tumaco.xlsx'),
            'Arauca': ('analisis_hidrometeorologico_arauca.xlsx', 'nasa_power_arauca.xlsx'),
        }
        nombre_ideam, nombre_nasa = nombres_esperados[territorio]
        faltantes = []
        if archivo_ideam is None:
            faltantes.append(nombre_ideam)
        if archivo_nasa is None:
            faltantes.append(nombre_nasa)

        if faltantes:
            st.error(
                f"Faltan archivos climáticos de {territorio} en `{CARPETA_DATOS_HIDRO.name}`: "
                + ", ".join(faltantes)
            )
            st.info(
                "La página no mezcla datos inventados. Cuando estén los Excel requeridos, "
                "se activarán automáticamente las comparaciones IDEAM–NASA POWER."
            )
        else:
            try:
                df_nasa, ind_nasa = cargar_nasa_tumaco(str(archivo_nasa))
                df_ideam, ind_ideam, control_ideam, fuentes_ideam = cargar_ideam_tumaco(
                    str(archivo_ideam)
                )
                df = df_ideam.merge(df_nasa, on="Mes", how="inner")

                st.success(
                    f"IDEAM: `{Path(archivo_ideam).name}` · "
                    f"NASA POWER: `{Path(archivo_nasa).name}`"
                )

                if territorio in {"Arauca", "La Paz"}:
                    st.caption(
                        f"Coordenadas de referencia de la sede en SIAMS: "
                        f"{info['lat']:.6f}, {info['lon']:.6f}. "
                        "Los Excel NASA procesados no almacenan las coordenadas de descarga."
                    )

                p_ideam_anual = df["Precipitación IDEAM (mm)"].sum()
                p_nasa_anual = df["Precipitación NASA (mm)"].sum()
                diferencia_p = (
                    (p_nasa_anual / p_ideam_anual - 1) * 100
                    if p_ideam_anual else float("nan")
                )

                fila_p = control_ideam.loc[
                    control_ideam["Variable"].astype(str).eq("precipitacion")
                ]
                completitud_p = (
                    float(fila_p.iloc[0]["Completitud [%]"])
                    if not fila_p.empty else float("nan")
                )

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Precipitación IDEAM", f"{p_ideam_anual:,.0f} mm/año")
                m2.metric("Completitud P IDEAM", f"{completitud_p:.2f} %")
                m3.metric("Precipitación NASA", f"{p_nasa_anual:,.0f} mm/año")
                m4.metric("NASA frente a IDEAM", f"{diferencia_p:+.1f} %")

                if territorio == "Arauca":
                    criterio_texto = (
                        "En Arauca, IDEAM se adopta como referencia terrestre para precipitación y "
                        "temperatura. La temperatura media IDEAM es derivada de Tmax y Tmin. "
                        "La humedad IDEAM se muestra con advertencia porque la serie mínima fue inferida "
                        "a partir del archivo entregado. NASA POWER se conserva como contraste y como "
                        "fuente para viento, presión y radiación."
                    )
                else:
                    criterio_texto = (
                        "En Tumaco, la precipitación IDEAM se usa como referencia principal por su "
                        "alta completitud. NASA POWER se conserva para comparar y para variables sin "
                        "observación terrestre suficiente. Las fuentes se muestran separadas y no se fusionan."
                    )

                st.markdown(
                    dedent(f"""
                    <div class="soft-box">
                        <strong>Criterio adoptado:</strong> {criterio_texto}
                    </div>
                    """).strip(),
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f'<div class="interpretation-box"><strong>Síntesis automática:</strong><br>'
                    f'{interpretacion_ideam_nasa(territorio, df, control_ideam)}</div>',
                    unsafe_allow_html=True,
                )

                tab_p, tab_t, tab_hr, tab_otras, tab_calidad, tab_tabla = st.tabs([
                    "Precipitación",
                    "Temperatura",
                    "Humedad",
                    "Viento, presión y radiación",
                    "Calidad y decisión",
                    "Tabla y descargas",
                ])

                with tab_p:
                    p_larga = pd.concat([
                        df[["Mes", "Precipitación IDEAM (mm)"]].rename(
                            columns={"Precipitación IDEAM (mm)": "Precipitación (mm)"}
                        ).assign(Fuente="IDEAM"),
                        df[["Mes", "Precipitación NASA (mm)"]].rename(
                            columns={"Precipitación NASA (mm)": "Precipitación (mm)"}
                        ).assign(Fuente="NASA POWER"),
                    ], ignore_index=True)

                    fig = px.bar(
                        p_larga,
                        x="Mes",
                        y="Precipitación (mm)",
                        color="Fuente",
                        barmode="group",
                        text_auto=".1f",
                        title=f"Régimen mensual multianual de precipitación · {territorio}",
                    )
                    fig.update_layout(
                        xaxis_title="Mes",
                        yaxis_title="Precipitación mensual (mm)",
                        legend_title_text="Fuente",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    mes_max = df.loc[df["Precipitación IDEAM (mm)"].idxmax()]
                    mes_min = df.loc[df["Precipitación IDEAM (mm)"].idxmin()]
                    relacion = "mayor" if diferencia_p > 0 else "menor"
                    st.info(
                        f"Con IDEAM, el máximo mensual ocurre en **{mes_max['Mes']}** "
                        f"({mes_max['Precipitación IDEAM (mm)']:.1f} mm) y el mínimo en "
                        f"**{mes_min['Mes']}** ({mes_min['Precipitación IDEAM (mm)']:.1f} mm). "
                        f"El acumulado NASA es {abs(diferencia_p):.1f} % {relacion} que el IDEAM."
                    )

                with tab_t:
                    opciones_t = {
                        "Temperatura media": (
                            "Temperatura media IDEAM (°C)",
                            "Temperatura media NASA (°C)",
                        ),
                        "Temperatura máxima": (
                            "Temperatura máxima IDEAM (°C)",
                            "Temperatura máxima NASA (°C)",
                        ),
                        "Temperatura mínima": (
                            "Temperatura mínima IDEAM (°C)",
                            "Temperatura mínima NASA (°C)",
                        ),
                    }
                    seleccion_t = st.selectbox(
                        "Variable de temperatura",
                        list(opciones_t),
                        key=f"temperatura_ideam_nasa_{territorio}",
                    )
                    col_i, col_n = opciones_t[seleccion_t]

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df["Mes"], y=df[col_i], mode="lines+markers", name="IDEAM"
                    ))
                    fig.add_trace(go.Scatter(
                        x=df["Mes"], y=df[col_n], mode="lines+markers", name="NASA POWER"
                    ))
                    fig.update_layout(
                        title=f"{seleccion_t}: comparación mensual · {territorio}",
                        xaxis_title="Mes",
                        yaxis_title="Temperatura (°C)",
                        legend=dict(orientation="h", y=-0.2),
                        margin=dict(b=80),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    diferencia_media = (df[col_n] - df[col_i]).mean()
                    nota_t = (
                        " En Arauca, la temperatura media IDEAM fue estimada como (Tmax + Tmin) / 2."
                        if territorio == "Arauca" and seleccion_t == "Temperatura media"
                        else ""
                    )
                    st.caption(
                        f"Diferencia mensual promedio NASA − IDEAM: {diferencia_media:+.2f} °C. "
                        "La comparación es regional porque IDEAM corresponde a estaciones terrestres específicas."
                        + nota_t
                    )

                with tab_hr:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df["Mes"], y=df["Humedad IDEAM (%)"],
                        mode="lines+markers", name="IDEAM"
                    ))
                    fig.add_trace(go.Scatter(
                        x=df["Mes"], y=df["Humedad NASA (%)"],
                        mode="lines+markers", name="NASA POWER"
                    ))
                    fig.update_layout(
                        title=f"Humedad relativa mensual · {territorio}",
                        xaxis_title="Mes",
                        yaxis_title="Humedad relativa (%)",
                        yaxis=dict(range=[0, 100]),
                        legend=dict(orientation="h", y=-0.2),
                        margin=dict(b=80),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    fila_hr = control_ideam.loc[
                        control_ideam["Variable"].astype(str).eq("humedad_relativa")
                    ]
                    comp_hr = (
                        float(fila_hr.iloc[0]["Completitud [%]"])
                        if not fila_hr.empty else float("nan")
                    )
                    diferencia_hr = (
                        df["Humedad NASA (%)"] - df["Humedad IDEAM (%)"]
                    ).mean()

                    if territorio == "Arauca":
                        st.warning(
                            f"La humedad IDEAM tiene {comp_hr:.2f} % de completitud y NASA difiere "
                            f"en promedio {diferencia_hr:+.2f} puntos porcentuales. La HR media IDEAM "
                            "usa una serie mínima inferida; mantener esta advertencia hasta validar el metadato IDEAM."
                        )
                    else:
                        st.warning(
                            f"La humedad IDEAM tiene {comp_hr:.2f} % de completitud. NASA presenta "
                            f"una diferencia media de {diferencia_hr:+.2f} puntos porcentuales frente a IDEAM. "
                            "Por eso se muestran ambas fuentes con advertencia."
                        )

                with tab_otras:
                    opciones = {
                        "Viento a 2 m": "Viento a 2 m NASA (m/s)",
                        "Presión superficial": "Presión NASA (kPa)",
                        "Radiación solar": "Radiación NASA (MJ/m²/día)",
                    }
                    seleccion = st.selectbox(
                        "Variable NASA POWER",
                        list(opciones),
                        key=f"otras_nasa_{territorio}",
                    )
                    columna = opciones[seleccion]
                    fig = px.line(
                        df,
                        x="Mes",
                        y=columna,
                        markers=True,
                        title=f"Régimen mensual de {seleccion.lower()} · {territorio}",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(
                        f"Estas variables se presentan con NASA POWER porque el archivo IDEAM procesado "
                        f"de {territorio} no contiene series equivalentes."
                    )

                with tab_calidad:
                    st.subheader("Decisión de uso por variable")
                    st.dataframe(
                        decisiones_climaticas_ideam(control_ideam, territorio),
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.subheader("Control de faltantes IDEAM")
                    control_mostrar = control_ideam.copy()
                    for columna in ("Fecha inicial", "Fecha final"):
                        if columna in control_mostrar.columns:
                            control_mostrar[columna] = control_mostrar[columna].apply(
                                lambda x: x.strftime("%Y-%m-%d") if hasattr(x, "strftime") else "—"
                            )
                    st.dataframe(control_mostrar, use_container_width=True, hide_index=True)

                    st.subheader("Estaciones y archivos de origen")
                    fuentes_mostrar = fuentes_ideam.copy()
                    for columna in ("Fecha_inicial", "Fecha_final"):
                        if columna in fuentes_mostrar.columns:
                            fuentes_mostrar[columna] = fuentes_mostrar[columna].apply(
                                lambda x: x.strftime("%Y-%m-%d") if hasattr(x, "strftime") else "—"
                            )
                    columnas_fuente = [
                        "Variable", "CodigoEstacion", "NombreEstacion", "Parametro",
                        "Unidad", "Fecha_inicial", "Fecha_final", "Registros",
                    ]
                    st.dataframe(
                        fuentes_mostrar[[c for c in columnas_fuente if c in fuentes_mostrar.columns]],
                        use_container_width=True,
                        hide_index=True,
                    )

                with tab_tabla:
                    st.dataframe(df.round(2), use_container_width=True, hide_index=True)

                    c1, c2 = st.columns(2)
                    with c1:
                        with open(archivo_ideam, "rb") as archivo:
                            st.download_button(
                                "Descargar base IDEAM procesada",
                                data=archivo.read(),
                                file_name=Path(archivo_ideam).name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"descarga_ideam_{territorio}",
                            )
                    with c2:
                        with open(archivo_nasa, "rb") as archivo:
                            st.download_button(
                                "Descargar base NASA POWER",
                                data=archivo.read(),
                                file_name=Path(archivo_nasa).name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"descarga_nasa_{territorio}",
                            )

            except Exception as error:
                st.error(
                    f"Se encontraron los Excel de {territorio}, pero ocurrió un error al procesarlos."
                )
                st.code(str(error), language=None)

    # -----------------------------------------------------
    # LETICIA, MEDELLÍN, SAN ANDRÉS Y LA PAZ: NASA POWER
    # La Paz se deja deliberadamente solo con NASA POWER.
    # -----------------------------------------------------
    else:
        archivo_nasa = ARCHIVOS_CLIMA_NASA.get(territorio)
        indicadores = {}
        datos_reales = archivo_nasa is not None

        if datos_reales:
            try:
                df, indicadores = cargar_clima_leticia(str(archivo_nasa))
                st.success(
                    f"Datos reales cargados desde `{Path(archivo_nasa).name}` · Fuente: NASA POWER."
                )
                if territorio == "La Paz":
                    st.caption(
                        f"Coordenadas oficiales de referencia de la Sede de La Paz en SIAMS: "
                        f"{info['lat']:.6f}, {info['lon']:.6f}. "
                        "El Excel NASA procesado no almacena la coordenada usada durante la descarga."
                    )
            except Exception as error:
                datos_reales = False
                df = clima_prototipo(info) if info.get("precipitacion") else pd.DataFrame()
                st.error(
                    f"Se encontró el Excel climático de {territorio}, pero ocurrió un error al procesarlo."
                )
                st.code(str(error), language=None)
        else:
            df = clima_prototipo(info) if info.get("precipitacion") else pd.DataFrame()
            prefijos = {
                "Leticia": "NASA_POWER_LETICIA",
                "Medellín": "NASA_POWER_MEDELLÍN",
                "San Andrés": "NASA_POWER_SAN_ANDRES",
                "La Paz": "NASA_POWER_LAPAZ",
            }
            st.warning(
                f"No se encontró el Excel de NASA POWER para **{territorio}**. "
                f"Ubícalo en `{CARPETA_DATOS_HIDRO.name}` como "
                f"`nasa_power_{normalizar_etiqueta(territorio)}.xlsx`."
            )

        if df.empty:
            st.info(
                "No se muestran datos demostrativos. La sección se activará automáticamente "
                "cuando el Excel climático sea detectado."
            )
        else:
            if datos_reales and indicadores:
                fecha_inicial = indicadores.get("Fecha inicial")
                fecha_final = indicadores.get("Fecha final")
                dias = indicadores.get("Número de días descargados", "—")
                p_max = indicadores.get("Precipitación diaria máxima [mm/día]", "—")
                t_media = indicadores.get("Temperatura media del periodo [°C]", "—")
                hr_media = indicadores.get("Humedad relativa media [%]", "—")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Periodo", periodo_texto(fecha_inicial, fecha_final))
                m2.metric("Días analizados", f"{int(dias):,}" if pd.notna(dias) else "—")
                m3.metric("Máxima diaria", f"{float(p_max):.2f} mm/día" if pd.notna(p_max) else "—")
                m4.metric("Temperatura media", f"{float(t_media):.2f} °C" if pd.notna(t_media) else "—")

                if pd.notna(hr_media):
                    st.markdown(dedent(f"""
                        <div class="soft-box">
                            <strong>Humedad relativa media del periodo:</strong> {float(hr_media):.2f} %<br>
                            <strong>Fuente:</strong> NASA POWER.<br>
                            <strong>Tratamiento:</strong> régimen mensual multianual calculado a partir de datos diarios.<br>
                            <strong>Nota:</strong> la precipitación de <code>Regimen_P</code> se interpreta como total mensual climatológico.
                        </div>
                        """).strip(), unsafe_allow_html=True)

                st.markdown(
                    f'<div class="interpretation-box"><strong>Síntesis automática:</strong><br>'
                    f'{interpretacion_nasa(territorio, df)}</div>',
                    unsafe_allow_html=True,
                )

            tab1, tab2, tab3, tab4 = st.tabs([
                "Precipitación",
                "Temperatura y humedad",
                "Viento, presión y radiación",
                "Tabla y descarga",
            ])

            with tab1:
                fig = px.bar(
                    df,
                    x="Mes",
                    y="Precipitación mensual (mm)",
                    title=f"Régimen mensual multianual de precipitación · {territorio}",
                    text_auto=".1f",
                )
                fig.update_layout(
                    xaxis_title="Mes",
                    yaxis_title="Precipitación mensual (mm)",
                )
                st.plotly_chart(fig, use_container_width=True)

                p_anual = df["Precipitación mensual (mm)"].sum()
                mes_max = df.loc[df["Precipitación mensual (mm)"].idxmax()]
                mes_min = df.loc[df["Precipitación mensual (mm)"].idxmin()]
                st.caption(
                    f"Acumulado climatológico anual aproximado: {p_anual:.1f} mm. "
                    f"Máximo mensual: {mes_max['Mes']} ({mes_max['Precipitación mensual (mm)']:.1f} mm). "
                    f"Mínimo mensual: {mes_min['Mes']} ({mes_min['Precipitación mensual (mm)']:.1f} mm)."
                )

            with tab2:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df["Mes"],
                    y=df["Temperatura media (°C)"],
                    mode="lines+markers",
                    name="Temperatura media",
                ))
                if "Temperatura máxima (°C)" in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df["Mes"],
                        y=df["Temperatura máxima (°C)"],
                        mode="lines",
                        name="Temperatura máxima",
                        line=dict(dash="dot"),
                    ))
                if "Temperatura mínima (°C)" in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df["Mes"],
                        y=df["Temperatura mínima (°C)"],
                        mode="lines",
                        name="Temperatura mínima",
                        line=dict(dash="dot"),
                    ))
                fig.add_trace(go.Scatter(
                    x=df["Mes"],
                    y=df["Humedad relativa (%)"],
                    mode="lines+markers",
                    name="Humedad relativa",
                    yaxis="y2",
                ))
                fig.update_layout(
                    title=f"Temperatura y humedad relativa · {territorio}",
                    xaxis_title="Mes",
                    yaxis=dict(title="Temperatura (°C)"),
                    yaxis2=dict(
                        title="Humedad (%)",
                        overlaying="y",
                        side="right",
                        range=[0, 100],
                    ),
                    legend=dict(orientation="h", y=-0.2),
                    margin=dict(b=80),
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab3:
                columnas_otras = [
                    "Viento a 2 m (m/s)",
                    "Presión superficial (kPa)",
                    "Radiación solar (MJ/m²/día)",
                ]
                disponibles = [col for col in columnas_otras if col in df.columns]
                if disponibles:
                    variable = st.selectbox(
                        "Variable climática",
                        disponibles,
                        key=f"variable_clima_{territorio}",
                    )
                    fig = px.line(
                        df,
                        x="Mes",
                        y=variable,
                        markers=True,
                        title=f"{variable} · {territorio}",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Estas variables no están disponibles en el archivo procesado.")

            with tab4:
                st.dataframe(df.round(2), use_container_width=True, hide_index=True)
                if datos_reales and archivo_nasa is not None:
                    with open(archivo_nasa, "rb") as archivo_excel:
                        st.download_button(
                            "Descargar base climática procesada",
                            data=archivo_excel.read(),
                            file_name=Path(archivo_nasa).name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"descarga_clima_{territorio}",
                        )

# =========================================================
# ANÁLISIS DE TENDENCIAS · MANN-KENDALL + SEN
# =========================================================

elif seccion == "Análisis de tendencias":
    st.title(f"📈 Análisis de tendencias · {territorio}")
    st.caption("Mann–Kendall original · Hamed–Rao con autocorrelación · pendiente de Sen")

    st.markdown(dedent("""
        <div class="soft-box">
            <strong>¿Qué hace esta sección?</strong> Evalúa si una variable presenta una tendencia
            monotónica creciente o decreciente en el tiempo. Mann-Kendall determina si la tendencia
            es estadísticamente significativa y la pendiente de Sen estima cuánto cambia por año.
            Para evitar confundir la estacionalidad normal de los meses con una tendencia de largo
            plazo, el análisis se realiza sobre valores <strong>anuales</strong> obtenidos desde la
            serie histórica original.
        </div>
        """).strip(), unsafe_allow_html=True)

    if np is None:
        st.error("Falta NumPy para ejecutar el análisis de tendencias.")
        st.code("pip install numpy", language="bash")
    else:
        series_disp = series_tendencia_territorio(territorio, info)

        if not series_disp:
            st.warning(
                "No se encontraron series históricas compatibles para este territorio. "
                "La climatología de 12 meses no se usa para Mann-Kendall. Para activar clima, "
                "el Excel debe conservar una hoja con fechas reales (o YEAR/MO/DY) y los datos diarios/mensuales."
            )
        else:
            resumen_tendencias = []
            for variable, paquete in series_disp.items():
                try:
                    anual, res = analizar_serie_tendencia(
                        paquete["serie"], paquete["agregacion"], alpha=0.05
                    )
                    if res is None:
                        continue
                    hr = mann_kendall_hamed_rao(anual["Año"], anual["Valor"])
                    resumen_tendencias.append({
                        "Variable": variable,
                        "Fuente": paquete["fuente"],
                        "Periodo": f"{int(anual['Año'].min())}–{int(anual['Año'].max())}",
                        "Años": len(anual),
                        "Tau": res["tau"],
                        "p-value": res["p"],
                        "p Hamed–Rao": hr["p"],
                        "Resultado Hamed–Rao": hr["tendencia"],
                        "Pendiente Sen": res["pendiente"],
                        "Unidad/año": f"{paquete['unidad']}/año",
                        "Resultado": res["tendencia"],
                    })
                except Exception:
                    continue

            if not resumen_tendencias:
                st.warning(
                    "Se detectaron datos, pero ninguna variable tiene al menos cinco años válidos "
                    "después del control de completitud anual."
                )
            else:
                df_resumen_tend = pd.DataFrame(resumen_tendencias)

                # M5_VISUAL_INICIO — lectura comparativa sin cambiar los cálculos de MK, Hamed–Rao o Sen.
                evaluables_hr = df_resumen_tend["p Hamed–Rao"].notna()
                comparables_hr = df_resumen_tend.loc[evaluables_hr]
                cambios_hr = int((
                    comparables_hr["Resultado"] != comparables_hr["Resultado Hamed–Rao"]
                ).sum())
                n_no_evaluables = int((~evaluables_hr).sum())

                st.subheader("Panorama estadístico del territorio")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Variables analizadas", len(df_resumen_tend))
                r2.metric("Con corrección Hamed–Rao", int(evaluables_hr.sum()))
                r3.metric("Significativas corregidas", int((comparables_hr["p Hamed–Rao"] < 0.05).sum()))
                r4.metric("Conclusiones que cambian", cambios_hr)

                st.markdown("#### ¿Cuánto cambia la significancia al considerar autocorrelación?")
                fig_hr = go.Figure()
                # Segmentos unen los p-values de la misma variable, solo cuando hay ambos.
                lineas_x, lineas_y = [], []
                for _, fila_hr in comparables_hr.iterrows():
                    lineas_x.extend([max(float(fila_hr["p-value"]), 1e-6),
                                     max(float(fila_hr["p Hamed–Rao"]), 1e-6), None])
                    lineas_y.extend([fila_hr["Variable"], fila_hr["Variable"], None])
                fig_hr.add_trace(go.Scatter(
                    x=lineas_x, y=lineas_y, mode="lines",
                    line=dict(color="#B3C2CF", width=2),
                    showlegend=False, hoverinfo="skip",
                ))
                for campo_p, etiqueta, color in (
                    ("p-value", "Mann–Kendall original", "#2563EB"),
                    ("p Hamed–Rao", "Hamed–Rao corregido", "#EA580C"),
                ):
                    serie_p = df_resumen_tend[["Variable", campo_p]].dropna()
                    fig_hr.add_trace(go.Scatter(
                        x=serie_p[campo_p].clip(lower=1e-6),
                        y=serie_p["Variable"],
                        customdata=serie_p[campo_p],
                        mode="markers", name=etiqueta,
                        marker=dict(size=13, color=color, line=dict(color="white", width=1.5)),
                        hovertemplate="%{y}<br>p = %{customdata:.6g}<extra>%{fullData.name}</extra>",
                    ))
                fig_hr.add_vline(x=0.05, line_color="#B91C1C", line_dash="dash",
                                 annotation_text="α = 0,05", annotation_position="top right")
                fig_hr.update_layout(
                    xaxis=dict(type="log", range=[-6.1, 0.04], title="p-value (escala logarítmica)",
                               tickvals=[1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 5e-2, 1e-1, 1],
                               ticktext=["10⁻⁶", "10⁻⁵", "10⁻⁴", "0,001", "0,01", "0,05", "0,1", "1"]),
                    yaxis=dict(autorange="reversed", title=""),
                    height=max(390, 90 + 46 * len(df_resumen_tend)),
                    margin=dict(l=8, r=16, t=48, b=28),
                    legend=dict(orientation="h", y=1.15, x=0),
                    hovermode="closest",
                )
                st.plotly_chart(fig_hr, use_container_width=True,
                                key=f"siams_m5_comparacion_{territorio}")
                st.caption(
                    "A la izquierda de la línea roja (p < 0,05): resultado significativo. "
                    "La escala logarítmica permite ver valores muy pequeños sin perder los grandes. "
                    f"No evaluables con Hamed–Rao: {n_no_evaluables}; se muestran solo con su p original. "
                    "Los puntos en p = 0 en el cálculo se dibujan en 10⁻⁶ para poder representarlos."
                )
                # M5_VISUAL_FIN

                st.subheader("Resultados por variable")
                tabla_tend = df_resumen_tend.copy()
                tabla_tend["Cambio tras corregir"] = [
                    ("No evaluable" if pd.isna(fila["p Hamed–Rao"]) else
                     "Sí" if fila["Resultado"] != fila["Resultado Hamed–Rao"] else "No")
                    for _, fila in tabla_tend.iterrows()
                ]
                tabla_tend["Tau"] = tabla_tend["Tau"].map(lambda x: f"{x:+.3f}")
                tabla_tend["p-value"] = tabla_tend["p-value"].map(lambda x: f"{x:.4f}")
                tabla_tend["p Hamed–Rao"] = tabla_tend["p Hamed–Rao"].map(
                    lambda x: f"{x:.4f}" if pd.notna(x) else "—"
                )
                tabla_tend["Pendiente Sen"] = tabla_tend["Pendiente Sen"].map(lambda x: f"{x:+.4f}")
                st.dataframe(tabla_tend, use_container_width=True, hide_index=True)
                st.caption(
                    "p-value: Mann–Kendall original. p Hamed–Rao: varianza corregida "
                    "por autocorrelación de los rangos sin tendencia (hasta 3 rezagos). "
                    "«No evaluable» indica años no consecutivos o datos insuficientes. "
                    "La pendiente de Sen no cambia."
                )

                variables_validas = df_resumen_tend["Variable"].tolist()
                seleccion = st.selectbox(
                    "Variable para ver en detalle",
                    variables_validas,
                    key=f"variable_mk_{territorio}",
                )
                paquete = series_disp[seleccion]
                anual, res = analizar_serie_tendencia(
                    paquete["serie"], paquete["agregacion"], alpha=0.05
                )

                if res is not None:
                    icono = "↗️" if res["significativa"] and res["tau"] > 0 else (
                        "↘️" if res["significativa"] and res["tau"] < 0 else "➡️"
                    )
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        st.markdown(
                            dedent(f"""
                            <div class="trend-result-card">
                                <div class="trend-label">Resultado</div>
                                <div class="trend-value">{icono} {res['tendencia']}</div>
                            </div>
                            """).strip(),
                            unsafe_allow_html=True,
                        )
                    m2.metric("Tau de Kendall", f"{res['tau']:+.3f}")
                    m3.metric("p-value", f"{res['p']:.4f}")
                    m4.metric(
                        "Pendiente de Sen",
                        f"{res['pendiente']:+.4f} {paquete['unidad']}/año",
                    )

                    hr_detalle = mann_kendall_hamed_rao(anual["Año"], anual["Valor"])
                    st.markdown("#### Efecto de la autocorrelación en esta variable")
                    if hr_detalle["disponible"]:
                        h1, h2, h3 = st.columns(3)
                        h1.metric("p Hamed–Rao", f"{hr_detalle['p']:.4f}")
                        h2.metric("Factor de varianza", f"{hr_detalle['factor_varianza']:.3f}")
                        rezagos = hr_detalle["lags_significativos"]
                        h3.metric("Rezagos significativos", ", ".join(map(str, rezagos)) if rezagos else "Ninguno")
                        if hr_detalle["tendencia"] != res["tendencia"]:
                            st.warning(
                                f"**La conclusión cambia:** Mann–Kendall original: {res['tendencia']}; "
                                f"corregido por Hamed–Rao: {hr_detalle['tendencia']}. "
                                "La pendiente de Sen y Tau no se modifican."
                            )
                        else:
                            st.success(
                                f"**La conclusión se mantiene:** {hr_detalle['tendencia']}. "
                                "Hamed–Rao ajusta la significancia; Tau y la pendiente de Sen se conservan."
                            )
                    else:
                        st.warning(f"**Hamed–Rao no evaluable:** {hr_detalle['motivo']}")

                    tendencia_sen = res["intercepto"] + res["pendiente"] * anual["Año"].astype(float)
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=anual["Año"], y=anual["Valor"],
                        mode="lines+markers", name=seleccion,
                    ))
                    fig.add_trace(go.Scatter(
                        x=anual["Año"], y=tendencia_sen,
                        mode="lines", name="Pendiente de Sen",
                        line=dict(dash="dash"),
                    ))
                    fig.update_layout(
                        title=f"{seleccion} · tendencia anual · {territorio}",
                        xaxis_title="Año",
                        yaxis_title=f"{seleccion} ({paquete['unidad']})",
                        hovermode="x unified",
                        legend=dict(orientation="h", y=-0.2),
                        margin=dict(b=80),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    if res["significativa"]:
                        direccion = "aumenta" if res["tau"] > 0 else "disminuye"
                        st.success(
                            f"Con α = 0.05, Mann-Kendall identifica una tendencia "
                            f"{('creciente' if res['tau'] > 0 else 'decreciente')} estadísticamente significativa. "
                            f"La pendiente de Sen estima que {seleccion.lower()} {direccion} aproximadamente "
                            f"{abs(res['pendiente']):.4f} {paquete['unidad']} por año."
                        )
                    else:
                        sentido = "positiva" if res["pendiente"] > 0 else "negativa" if res["pendiente"] < 0 else "nula"
                        st.info(
                            f"La pendiente de Sen es {sentido} ({res['pendiente']:+.4f} {paquete['unidad']}/año), "
                            f"pero Mann-Kendall no la considera estadísticamente significativa con α = 0.05. "
                            "Por tanto, la plataforma no afirma que exista una tendencia de largo plazo."
                        )

                    st.caption(
                        f"Fuente: {paquete['fuente']} · archivo: {paquete['archivo']} · "
                        f"origen interno: {paquete.get('hoja', '—')} · "
                        f"periodo analizado: {int(anual['Año'].min())}–{int(anual['Año'].max())} · "
                        f"{len(anual)} años válidos."
                    )

                    with st.expander("Ver datos anuales utilizados", expanded=False):
                        st.dataframe(anual.round(4), use_container_width=True, hide_index=True)

                with st.expander("Cómo leer Mann–Kendall, Hamed–Rao y Sen", expanded=False):
                    st.markdown(
                        "**Mann–Kendall** prueba si existe una tendencia monotónica; "
                        "**Hamed–Rao** ajusta su varianza para considerar autocorrelación temporal; "
                        "**Sen** estima la magnitud del cambio por año. "
                        "El umbral α = 0,05 determina si el p-value es significativo. "
                        "Cuando Hamed–Rao es *No evaluable* no debe interpretarse como ausencia de tendencia. "
                        "Que ambos métodos coincidan no demuestra la causa física de los cambios. "
                        "Hay que valorar homogeneidad, años ausentes, cambios de instrumento y representatividad espacial."
                    )

                st.caption(
                    "El módulo queda preparado para incorporar en el futuro niveles de sonda, caudales "
                    "y parámetros de calidad del agua cuando existan series temporales validadas."
                )


# =========================================================
# HIDROLOGÍA
# =========================================================

elif seccion == "Hidrología":
    st.title(f"💦 Hidrología de {territorio}")

    # Animaciones temporales y fichas técnicas SWOT disponibles para Leticia, Tumaco, Medellín y Arauca.
    mostrar_gifs_swot(territorio)
    mostrar_tarjetas_swot(territorio)

    if territorio == "Leticia":
        mostrar_mapa_imagen(
            "hidrografia", "Mapa de hidrografía del municipio de Leticia",
            "Instituto Amazónico de Investigaciones Científicas SINCHI",
            "El mapa permite reconocer la red de drenaje del municipio y su conexión con el sistema fluvial amazónico.",
        )
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("Ver mapa regional de humedales", expanded=False):
                mostrar_mapa_imagen("humedales", "Humedales de Leticia y Puerto Nariño", "Corpoamazonia")
        with c2:
            with st.expander("Ver mapa de inundación urbana", expanded=False):
                mostrar_mapa_imagen("inundacion", "Áreas de inundación en la zona urbana de Leticia", "Corpoamazonia")

    elif territorio == "Tumaco":
        mostrar_mapa_imagen(
            "hidrografia", "Sistemas hídricos de Tumaco y el Bajo Mira",
            "Parques Nacionales Naturales de Colombia",
            "Contexto regional de ríos, esteros, manglares y ambientes marino-costeros.",
        )
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("Ver mapa regional de manglares", expanded=False):
                mostrar_mapa_imagen("manglares", "Distribución regional de manglares en Nariño", "CORPONARIÑO y entidades participantes")
        with c2:
            with st.expander("Ver mapa de amenaza por inundación", expanded=False):
                mostrar_mapa_imagen("inundacion", "Amenaza por inundación en la cuenca del río Mira", "CORPONARIÑO – POMCA Río Mira")

    elif territorio == "San Andrés":
        mostrar_mapa_imagen(
            "microcuencas", "Principales microcuencas y arroyos estacionales de San Andrés",
            "CORALINA",
            "El mapa permite visualizar los límites de microcuenca y los drenajes estacionales de la isla, "
            "elementos especialmente relevantes en un territorio con disponibilidad limitada de agua dulce.",
        )
        st.info("En San Andrés el componente hídrico superficial debe leerse junto con la hidrogeología, porque el acuífero es clave para el abastecimiento de agua dulce.")

    elif territorio == "Medellín":
        mostrar_mapa_imagen(
            "inundacion", "Amenaza por inundaciones en Medellín",
            "Alcaldía de Medellín – Plan de Ordenamiento Territorial (POT)",
            "La cartografía muestra sectores con distintos niveles de amenaza por inundación. Debe interpretarse según la escala y metodología del POT.",
        )
        st.caption("Para una siguiente versión conviene complementar este componente con la red hídrica y las microcuencas/quebradas del Valle de Aburrá.")
    elif territorio == "Arauca":
        st.subheader("Contexto hídrico y presión sobre el recurso")
        mostrar_mapa_imagen(
            "anomalia_oferta_alta",
            "Anomalía de la Oferta Hídrica Superficial en condiciones altas",
            "IDEAM – Estudio Nacional del Agua 2014",
            "El mapa permite ubicar a Arauca dentro del comportamiento nacional de la oferta hídrica superficial bajo condiciones altas. Se usa como contexto histórico y regional, no como análisis local actualizado.",
        )

        c1, c2 = st.columns(2)
        with c1:
            with st.expander("Ver demanda de agua de la industria manufacturera · 2021", expanded=False):
                mostrar_mapa_imagen(
                    "demanda_industria",
                    "Demanda de agua de la industria manufacturera por departamento",
                    "IDEAM · 2021",
                    "Mapa departamental útil para comparar la presión asociada a la industria manufacturera. No representa consumos puntuales de la Sede Orinoquía.",
                )
        with c2:
            with st.expander("Ver vertimientos de la industria manufacturera · 2021", expanded=False):
                mostrar_mapa_imagen(
                    "vertimientos_industria",
                    "Vertimientos de aguas residuales de la industria manufacturera",
                    "IDEAM · 2021",
                    "Referencia departamental de presión por vertimientos industriales. Debe leerse junto con información local de calidad y cuerpos receptores cuando esté disponible.",
                )

        st.caption(
            "Los tres productos son de escala nacional o departamental. Se presentan como contexto para Arauca y no como cartografía detallada del entorno inmediato de la sede."
        )

    elif territorio == "Bogotá":
        st.info(
            "Bogotá ya cuenta con el piloto de ubicación multiescala en **Territorio → Mapa y territorio**. "
            "La cartografía hidrológica temática queda para una siguiente fase."
        )
    else:
        st.info(
            f"El módulo hidrológico de {territorio} ya está habilitado, pero todavía no tiene "
            "cartografía temática validada. Se puede incorporar sin modificar la estructura de la página."
        )

# =========================================================
# GEOLOGÍA
# =========================================================

elif seccion == "Geología":
    st.title(f"🪨 Geología de {territorio}")

    tab1, tab2, tab3 = st.tabs(
        [
            "Mapa",
            "Unidades geológicas",
            "Fuentes y escala",
        ]
    )

    with tab1:
        if territorio == "Leticia":
            mostrar_mapa_imagen("geologia", "Distribución espacial de las unidades geológicas del Trapecio Sur", "Instituto SINCHI, con base en información geológica regional")
        elif territorio == "Tumaco":
            mostrar_mapa_imagen("geologia", "Unidades geológicas de la cuenca hidrográfica del río Mira", "CORPONARIÑO – POMCA Río Mira")
        elif territorio == "San Andrés":
            mostrar_mapa_imagen("geologia", "Conformación geológica de la isla de San Andrés", "CORALINA")
        elif territorio == "Medellín":
            mostrar_mapa_imagen("geologia", "Plancha geológica 228 – Medellín", "Servicio Geológico Colombiano (SGC)")
        elif territorio == "Arauca":
            mostrar_mapa_imagen(
                "geologia",
                "Mapa Geológico de Colombia 2023 · referencia para Arauca",
                "Servicio Geológico Colombiano (SGC)",
                "Se usa como marco geológico regional. La escala nacional permite ubicar las grandes unidades, pero no reemplaza cartografía de detalle para la Sede Orinoquía o el municipio de Arauca.",
            )
        else:
            st.info(f"Todavía no se ha incorporado un mapa geológico validado para {territorio}.")

    with tab2:
        st.warning(
            "La cartografía geológica se presenta como referencia visual. Todavía no se ha transcrito y validado "
            "para cada territorio la tabla completa de códigos, edades y litologías de la leyenda. Para evitar errores, "
            "el prototipo no inventa unidades geológicas."
        )
        st.markdown(
            """
            **Para cerrar este componente faltaría:**

            - Código y nombre de cada unidad.
            - Edad o periodo geológico.
            - Litología o material dominante.
            - Descripción resumida.
            - Escala, año y referencia completa del mapa.
            """
        )

    with tab3:
        st.markdown(
            """
            Registrar para cada capa:

            - Entidad responsable.
            - Escala.
            - Año.
            - Sistema de referencia.
            - Descripción de la leyenda.
            - Limitaciones de uso.
            """
        )

# =========================================================
# HIDROGEOLOGÍA
# =========================================================

elif seccion == "Hidrogeología":
    st.title(f"💧 Hidrogeología de {territorio}")

    c1, c2, c3 = st.columns(3)

    with c1:
        mostrar_tarjeta(
            "Unidades hidrogeológicas",
            "Acuíferos, acuítardos y materiales dominantes.",
            "🧭",
        )

    with c2:
        mostrar_tarjeta(
            "Pozos",
            "Ubicación, profundidad, nivel y uso, cuando exista información.",
            "🕳️",
        )

    with c3:
        mostrar_tarjeta(
            "Recarga",
            "Zonas potenciales y limitaciones de interpretación.",
            "🌧️",
        )

    if territorio == "Leticia":
        st.subheader("Pozos y aguas subterráneas")
        mostrar_mapa_imagen(
            "pozos_irca", "Distribución de pozos de agua subterránea en Leticia",
            "SENA – recurso académico de aguas subterráneas de Leticia",
            "El mapa se incorpora como referencia académica complementaria.",
        )
    elif territorio == "San Andrés":
        st.subheader("Vulnerabilidad del acuífero")
        mostrar_mapa_imagen(
            "vulnerabilidad_acuifero", "Vulnerabilidad de las rocas que conforman los acuíferos de San Andrés",
            "CORALINA",
            "La cartografía clasifica sectores con vulnerabilidad extrema, alta y moderada, y aporta una lectura directa del riesgo hidrogeológico de la isla.",
        )

    elif territorio == "Arauca":
        st.subheader("Sistema Acuífero Arauca-Arauquita")
        mostrar_mapa_imagen(
            "sistema_acuifero",
            "SAP3.3 Sistema Acuífero Arauca-Arauquita",
            "IDEAM – Anexo 7 de Aguas Subterráneas",
            "La ficha delimita el sistema acuífero y resume la información disponible. La propia fuente señala que faltan estudios locales de caracterización hidrogeológica y reporta varios campos como NRI.",
        )

        st.subheader("Contexto hidrogeológico regional")
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("Ver criterio de demanda e hidrogeológico · PEXAS 2005", expanded=False):
                mostrar_mapa_imagen(
                    "criterio_hidrogeologico",
                    "Programa de Exploración de Aguas Subterráneas – criterio de demanda e hidrogeológico",
                    "Servicio Geológico Colombiano – PEXAS · 2005",
                    "La visualización muestra áreas priorizadas o evaluadas a escala regional. Es útil para contextualizar Arauca, pero no constituye por sí sola una delimitación actual del acuífero.",
                )
        with c2:
            with st.expander("Ver distribución de puntos de agua subterránea · ENA 2014", expanded=False):
                mostrar_mapa_imagen(
                    "puntos_agua_subterranea",
                    "Distribución de puntos de agua subterránea por Autoridad Ambiental",
                    "IDEAM – Estudio Nacional del Agua 2014",
                    "El mapa resume el número de puntos inventariados por autoridad ambiental; no corresponde a un inventario georreferenciado de pozos individuales dentro de Arauca.",
                )

        with st.expander("Ver volúmenes de agua subterránea concesionada · ENA 2014", expanded=False):
            mostrar_mapa_imagen(
                "volumen_concesionado",
                "Volúmenes de agua subterránea concesionada objeto de cobro TUA",
                "IDEAM – Estudio Nacional del Agua 2014",
                "Se incorpora como antecedente nacional de uso concesionado del agua subterránea. La información es histórica y agregada, por lo que no debe interpretarse como extracción actual del sistema Arauca-Arauquita.",
            )

    st.markdown(dedent("""
        <div class="warning-box">
            <strong>Nota:</strong> La plataforma debe diferenciar claramente entre
            información oficial, interpretación general y resultados propios del semillero.
        </div>
        """).strip(), unsafe_allow_html=True)

# =========================================================
# AGUA SUBTERRÁNEA · GRACE / GLDAS
# =========================================================

elif seccion == "Agua subterránea (GRACE)":
    st.title(f"🌐 Agua subterránea satelital · {territorio}")
    st.caption("GWSa + índice de sequía de agua subterránea (GGDI) · GRACE/GRACE-FO + GLDAS")
    st.markdown(
        "**¿Qué aprenderás aquí?** Los satélites ayudan a identificar si el agua "
        "almacenada bajo la superficie está por encima o por debajo de una referencia "
        "histórica. Puedes explorar cuándo ocurren cambios y compararlos entre fechas. "
        "No es una medición de cuántos metros hay hasta el agua en un pozo."
    )
    with st.expander("Primera vez aquí: ¿cómo interpretar GRACE y GGDI?", expanded=False):
        st.markdown(
            "**1. GWSa (cm):** cambio de almacenamiento subterráneo respecto a una "
            "referencia. Un valor positivo significa *más que en la referencia*; "
            "un valor negativo, *menos*. Cero no significa ausencia de agua.\n\n"
            "**2. GGDI:** compara cada mes con lo habitual para ese mismo mes. "
            "Un GGDI negativo indica una condición más seca que la referencia mensual, "
            "pero no demuestra por sí solo que un pozo vaya a secarse.\n\n"
            "**3. Alcance:** GRACE observa regiones amplias, no un pozo individual. "
            "Para decisiones locales hay que contrastarlo con mediciones de campo."
        )

    st.markdown(dedent("""
        <div class="soft-box">
            <strong>¿Qué representa?</strong> GWSa indica cambios del almacenamiento de agua
            subterránea respecto a una condición de referencia. No representa profundidad del
            nivel freático ni el volumen total del acuífero. El producto es regional y debe
            interpretarse junto con información hidrogeológica y mediciones de campo.
        </div>
        """).strip(), unsafe_allow_html=True)

    if xr is None or np is None:
        st.error("Faltan dependencias para leer el NetCDF.")
        st.code("pip install xarray netCDF4 numpy", language="bash")
    elif ARCHIVO_GWS is None:
        st.warning(
            "No se encontró `COL_GWS_estimations.nc` en `data/processed/grace/`. "
            "Comprueba el archivo y revisa el procedimiento A5 de GRACE."
        )
    else:
        try:
            df_gws, meta_gws = extraer_gws_territorio(
                str(ARCHIVO_GWS), info["lat"], info["lon"]
            )

            if not meta_gws.get("disponible", False) or df_gws.empty:
                st.warning(
                    f"No se publica una serie GWSa para **{territorio}** con este NetCDF. "
                    f"{meta_gws.get('motivo', 'No hay cobertura válida cercana.')}"
                )
                if territorio == "San Andrés":
                    st.info(
                        "Esto es esperable para la isla: el archivo entregado cubre principalmente "
                        "la Colombia continental. La página evita usar un píxel continental lejano "
                        "como si representara San Andrés."
                    )
            else:
                ultimo = df_gws.iloc[-1]
                promedio = df_gws["GWSa (cm)"].mean()
                minimo = df_gws["GWSa (cm)"].min()
                maximo = df_gws["GWSa (cm)"].max()
                pendiente = meta_gws["pendiente_cm_anio"]

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Última GWSa", f"{ultimo['GWSa (cm)']:.2f} cm", f"{ultimo['Fecha']:%Y-%m}")
                m2.metric("Promedio histórico", f"{promedio:.2f} cm")
                m3.metric("Mínimo / máximo", f"{minimo:.1f} / {maximo:.1f} cm")
                m4.metric("Pendiente lineal exploratoria", f"{pendiente:+.3f} cm/año")

                st.caption(
                    f"Píxel utilizado: {meta_gws['lat_pixel']:.4f}, {meta_gws['lon_pixel']:.4f} · "
                    f"distancia aproximada a la sede: {meta_gws['distancia_km']:.1f} km · "
                    f"periodo: {meta_gws['fecha_inicial']:%Y-%m} a {meta_gws['fecha_final']:%Y-%m}."
                )

                tab_serie, tab_clim, tab_ggdi, tab_mapa, tab_metodo = st.tabs([
                    "Serie histórica",
                    "Comportamiento mensual",
                    "GGDI",
                    "Mapa por fecha",
                    "Cómo interpretarlo",
                ])

                with tab_serie:
                    # M10: también en el GRACE ORIGINAL se conservan meses ausentes.
                    serie_grace_viz = _siams_meses_grace_con_vacios(df_gws, ["GWSa (cm)"])
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=serie_grace_viz["Fecha"],
                        y=serie_grace_viz["GWSa (cm)"],
                        mode="lines", name="GWSa · GRACE/GLDAS",
                        connectgaps=False,
                    ))
                    fig.update_layout(
                        title=f"Anomalía de almacenamiento de agua subterránea · {territorio}"
                    )
                    fig.add_hline(
                        y=0, line_dash="dash",
                        annotation_text="Referencia = 0 cm", annotation_position="top left",
                    )
                    fig.update_layout(
                        xaxis_title="Fecha", yaxis_title="GWSa (cm)", hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(
                        "Los meses sin datos GRACE se muestran como cortes en la línea: no se interpolan "
                        "ni se unen observaciones a través de vacíos. Los valores positivos y negativos "
                        "son desviaciones frente a la referencia, no clasificaciones de sostenibilidad."
                    )

                    csv_gws = df_gws.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        "Descargar serie GWSa de esta sede",
                        data=csv_gws,
                        file_name=f"GWSa_{territorio.replace(' ', '_')}.csv",
                        mime="text/csv",
                        key=f"descargar_gwsa_{territorio}",
                    )

                with tab_clim:
                    clim_gws = climatologia_gws(df_gws)
                    fig = px.bar(
                        clim_gws, x="Mes", y="GWSa (cm)",
                        title=f"Climatología mensual de GWSa · {territorio}",
                        text_auto=".2f",
                    )
                    fig.add_hline(y=0, line_dash="dash")
                    fig.update_layout(yaxis_title="GWSa media (cm)", xaxis_title="Mes")
                    st.plotly_chart(fig, use_container_width=True)

                    fila_min = clim_gws.loc[clim_gws["GWSa (cm)"].idxmin()]
                    fila_max = clim_gws.loc[clim_gws["GWSa (cm)"].idxmax()]
                    st.info(
                        f"En la climatología de este píxel, el promedio mensual más bajo ocurre en "
                        f"**{fila_min['Mes']}** ({fila_min['GWSa (cm)']:.2f} cm) y el más alto en "
                        f"**{fila_max['Mes']}** ({fila_max['GWSa (cm)']:.2f} cm)."
                    )

                with tab_ggdi:
                    df_ggdi, meta_ggdi = calcular_ggdi(df_gws)

                    if not meta_ggdi.get("disponible", False) or df_ggdi.empty:
                        st.warning(
                            "No fue posible calcular GGDI para esta sede. "
                            + meta_ggdi.get("motivo", "")
                        )
                    else:
                        st.markdown(dedent("""
                            <div class="soft-box">
                                <strong>GGDI · GRACE Groundwater Drought Index.</strong><br>
                                Para cada registro mensual se compara la GWSa observada con la
                                climatología de ese mismo mes. Primero se calcula
                                <strong>GSD = GWSa observada − GWSa climatológica</strong> y después
                                se normaliza como <strong>GGDI = GSD / σ(GSD)</strong>.<br><br>
                                <strong>GGDI &gt; 0:</strong> almacenamiento por encima de lo habitual
                                para ese mes. <strong>GGDI &lt; 0:</strong> déficit respecto a lo habitual.
                                El índice es adimensional y no representa profundidad del nivel freático.
                            </div>
                        """).strip(), unsafe_allow_html=True)

                        ultimo_ggdi = df_ggdi.iloc[-1]
                        fila_min_ggdi = df_ggdi.loc[df_ggdi["GGDI"].idxmin()]

                        g1, g2, g3, g4 = st.columns(4)
                        g1.metric(
                            "GGDI más reciente",
                            f"{ultimo_ggdi['GGDI']:+.2f}",
                            f"{ultimo_ggdi['Fecha']:%Y-%m}",
                        )
                        g2.metric(
                            "Mínimo histórico",
                            f"{meta_ggdi['ggdi_min']:+.2f}",
                            f"{fila_min_ggdi['Fecha']:%Y-%m}",
                        )
                        g3.metric(
                            "Meses con GGDI < 0",
                            f"{meta_ggdi['porcentaje_deficit']:.1f} %",
                        )
                        g4.metric(
                            "σ de GSD",
                            f"{meta_ggdi['sigma_gsd_cm']:.2f} cm",
                        )

                        serie_ggdi_viz = _siams_meses_grace_con_vacios(df_ggdi, ["GGDI"])
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=serie_ggdi_viz["Fecha"],
                            y=serie_ggdi_viz["GGDI"],
                            mode="lines",
                            name="GGDI",
                            connectgaps=False,
                        ))
                        fig.add_hline(
                            y=0,
                            line_dash="dash",
                            annotation_text="Condición mensual de referencia",
                            annotation_position="top left",
                        )
                        fig.update_layout(
                            title=f"Serie temporal del GGDI · {territorio}",
                            xaxis_title="Fecha",
                            yaxis_title="GGDI (adimensional)",
                            hovermode="x unified",
                        )
                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                            key=f"ggdi_serie_{territorio}",
                        )
                        st.caption("El GGDI no une meses sin dato. Los vacíos se conservan en la visualización.")

                        st.subheader("Revisar un año observado contra su climatología")
                        anios_ggdi = sorted(df_ggdi["Año"].unique().tolist())
                        anio_default = anios_ggdi[-1]
                        anio_sel = st.selectbox(
                            "Año observado",
                            anios_ggdi,
                            index=len(anios_ggdi) - 1,
                            key=f"anio_ggdi_{territorio}",
                        )
                        df_anio = df_ggdi[df_ggdi["Año"] == anio_sel].copy()
                        # M10: cada mes del año se muestra, incluso si falta el producto.
                        meses_eje = pd.DataFrame({
                            "Mes_num": list(range(1, 13)), "Mes": list(MESES)
                        })
                        df_anio_viz = meses_eje.merge(
                            df_anio.drop(columns=["Mes"], errors="ignore")
                            .drop_duplicates(subset=["Mes_num"]),
                            on="Mes_num", how="left",
                        )

                        fig_comp = go.Figure()
                        fig_comp.add_trace(go.Scatter(
                            x=df_anio_viz["Mes"],
                            y=df_anio_viz["GWSa (cm)"],
                            mode="lines+markers", connectgaps=False,
                            name=f"GWSa observada {anio_sel}",
                        ))
                        fig_comp.add_trace(go.Scatter(
                            x=df_anio_viz["Mes"],
                            y=df_anio_viz["GWSa climatológica (cm)"],
                            mode="lines+markers", connectgaps=False,
                            name="Climatología mensual",
                            line=dict(dash="dash"),
                        ))
                        fig_comp.update_layout(
                            title=f"GWSa observada vs. referencia mensual · {anio_sel}",
                            xaxis_title="Mes",
                            yaxis_title="GWSa (cm)",
                            hovermode="x unified",
                            legend=dict(orientation="h", y=-0.2),
                            margin=dict(b=80),
                        )
                        st.plotly_chart(
                            fig_comp,
                            use_container_width=True,
                            key=f"ggdi_comparacion_{territorio}_{anio_sel}",
                        )

                        fig_anio = px.bar(
                            df_anio,
                            x="Mes",
                            y="GGDI",
                            title=f"GGDI mensual · {anio_sel} · {territorio}",
                            text_auto=".2f",
                        )
                        fig_anio.add_hline(y=0, line_dash="dash")
                        fig_anio.update_layout(
                            xaxis_title="Mes",
                            yaxis_title="GGDI (adimensional)",
                        )
                        st.plotly_chart(
                            fig_anio,
                            use_container_width=True,
                            key=f"ggdi_barras_{territorio}_{anio_sel}",
                        )

                        st.subheader("Déficit histórico más fuerte por mes")
                        min_mensual = (
                            df_ggdi.groupby(["Mes_num", "Mes"], as_index=False)["GGDI"]
                            .min()
                            .sort_values("Mes_num")
                        )
                        fig_min = px.bar(
                            min_mensual,
                            x="Mes",
                            y="GGDI",
                            title=f"Mínimo histórico del GGDI para cada mes · {territorio}",
                            text_auto=".2f",
                        )
                        fig_min.add_hline(y=0, line_dash="dash")
                        fig_min.update_layout(
                            xaxis_title="Mes",
                            yaxis_title="GGDI mínimo",
                        )
                        st.plotly_chart(
                            fig_min,
                            use_container_width=True,
                            key=f"ggdi_min_mensual_{territorio}",
                        )

                        st.caption(
                            f"GGDI calculado con {meta_ggdi['registros']} registros mensuales "
                            f"y {meta_ggdi['anios']} años disponibles, desde "
                            f"{meta_ggdi['fecha_inicial']:%Y-%m} hasta "
                            f"{meta_ggdi['fecha_final']:%Y-%m}. La climatología se calcula "
                            "por separado para enero, febrero, marzo, etc., usando toda la serie disponible."
                        )

                        with st.expander("Ver cálculo mensual de GWSa → climatología → GSD → GGDI", expanded=False):
                            tabla_ggdi = df_ggdi.copy()
                            tabla_ggdi["Fecha"] = tabla_ggdi["Fecha"].dt.strftime("%Y-%m")
                            st.dataframe(
                                tabla_ggdi.round({
                                    "GWSa (cm)": 3,
                                    "GWSa climatológica (cm)": 3,
                                    "GSD (cm)": 3,
                                    "GGDI": 3,
                                }),
                                use_container_width=True,
                                hide_index=True,
                            )

                        csv_ggdi = df_ggdi.to_csv(index=False).encode("utf-8-sig")
                        st.download_button(
                            "Descargar serie GGDI de esta sede",
                            data=csv_ggdi,
                            file_name=f"GGDI_{territorio.replace(' ', '_')}.csv",
                            mime="text/csv",
                            key=f"descargar_ggdi_{territorio}",
                        )

                        st.warning(
                            "Interpretación del prototipo: se usa el signo del GGDI para distinguir "
                            "condiciones por encima o por debajo de la referencia mensual. No se agregan "
                            "categorías arbitrarias de severidad que no estén definidas en la metodología utilizada."
                        )

                with tab_mapa:
                    ds_gws = cargar_dataset_gws(str(ARCHIVO_GWS))
                    fechas = pd.to_datetime(ds_gws["time"].values)
                    etiquetas = [f"{f:%Y-%m}" for f in fechas]
                    etiqueta = st.select_slider(
                        "Fecha del mapa", options=etiquetas, value=etiquetas[-1],
                        key=f"fecha_mapa_gws_{territorio}",
                    )
                    indice_fecha = etiquetas.index(etiqueta)
                    matriz = np.asarray(ds_gws["GWS_anom"].isel(time=indice_fecha).values, dtype=float)

                    fig = go.Figure(data=go.Heatmap(
                        z=matriz,
                        x=np.asarray(ds_gws["lon"].values, dtype=float),
                        y=np.asarray(ds_gws["lat"].values, dtype=float),
                        colorscale="RdBu",
                        zmid=0,
                        colorbar=dict(title="GWSa (cm)"),
                        hovertemplate="Lon %{x:.2f}<br>Lat %{y:.2f}<br>GWSa %{z:.2f} cm<extra></extra>",
                    ))
                    fig.add_trace(go.Scatter(
                        x=[meta_gws["lon_pixel"]], y=[meta_gws["lat_pixel"]],
                        mode="markers", name=f"Píxel de {territorio}",
                        marker=dict(size=10, symbol="x", color="black"),
                    ))
                    fig.update_layout(
                        title=f"Distribución espacial de GWSa · {etiqueta}",
                        xaxis_title="Longitud", yaxis_title="Latitud",
                        height=620, margin=dict(l=20, r=20, t=60, b=30),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(
                        "Visualización de la malla del NetCDF. Las celdas sin estimación aparecen vacías. "
                        "No debe interpretarse como un mapa de profundidad del acuífero."
                    )

                with tab_metodo:
                    st.markdown(
                        """
                        La metodología del artículo de Romero y Piña estima GWSa a partir de las
                        variaciones de almacenamiento total observadas por GRACE/GRACE-FO y componentes
                        terrestres de GLDAS. Para la plataforma se usa directamente el producto NetCDF
                        entregado y se extrae el píxel válido más cercano a cada sede. A partir de esa
                        serie se construye la climatología mensual, se calcula GSD y se normaliza para
                        obtener GGDI.

                        **Decisiones del prototipo:**
                        - No se muestra GWSa como nivel freático.
                        - No se convierte automáticamente a recarga usando un Sy genérico.
                        - El análisis formal de tendencia se consulta en **Clima y datos → Análisis de tendencias**, con Mann-Kendall + Sen.
                        - El GGDI se calcula a partir de la GWSa observada, la climatología mensual y la desviación estándar de GSD.
                        - No se calcula aún el índice integrado de sostenibilidad, resiliencia o vulnerabilidad.
                        - Si no existe un píxel válido razonablemente cercano, la plataforma lo informa y no extrapola.
                        """
                    )
                    st.caption(
                        "Referencia metodológica: Romero, P. & Piña, A. (2025), "
                        "GRACE-based analysis of groundwater sustainability in the tropics, "
                        "Journal of Hydrology: Regional Studies."
                    )

        except Exception as error:
            st.error("Se encontró el NetCDF, pero ocurrió un error al procesar GWSa.")
            st.code(str(error), language=None)

    # Complemento: GRACE/GRACE-FO frente a niveles medidos en Leticia.
    # Se mantiene independiente del NetCDF de Colombia para mostrarlo aunque
    # el producto nacional no esté disponible temporalmente.
    if territorio == "Leticia":
        if mostrar_grace_leticia is None:
            st.warning("No se pudo cargar el módulo de niveles y GRACE de Leticia.")
            st.code(ERROR_MODULO_GRACE_LETICIA, language=None)
            st.caption("Comprueba que exista siams/grace_leticia.py y sus dependencias.")
        else:
            mostrar_grace_leticia()

# =========================================================
# HIDROGEOQUÍMICA
# =========================================================

elif seccion == "Hidrogeoquímica":
    if territorio == "Leticia":
        # Calculadora del taller, datos de laboratorio y diagramas.
        if mostrar_hidrogeoquimica is None:
            st.title("🧪 Hidrogeoquímica de Leticia")
            st.warning("No se pudo cargar la calculadora fisicoquímica de SIAMS.")
            st.code(ERROR_MODULO_HIDROGEOQUIMICA, language=None)
            st.caption("Verifica siams/hidrogeoquimica.py, hidrogeoquimica_datos.py e hidrogeoquimica_nucleo.py.")
        else:
            mostrar_hidrogeoquimica(territorio)
    else:
        st.title(f"🧪 Hidrogeoquímica de {territorio}")

        st.write(
            "Esta sección mostrará puntos de muestreo, parámetros fisicoquímicos y, "
            "cuando los datos lo permitan, diagramas hidroquímicos."
        )

        if territorio == "San Andrés":
            mostrar_mapa_imagen(
                "nitratos", "Concentraciones de nitratos en aguas subterráneas de San Andrés",
                "CORALINA",
                "El mapa se integra como antecedente de calidad de aguas subterráneas. Los valores deben interpretarse según la fecha y los puntos de muestreo de la fuente original.",
            )

        c1, c2 = st.columns(2)

        with c1:
            parametros = pd.DataFrame(
                {
                    "Grupo": [
                        "Campo",
                        "Iones mayoritarios",
                        "Calidad",
                    ],
                    "Parámetros": [
                        "pH, conductividad, temperatura y sólidos disueltos",
                        "Ca, Mg, Na, K, HCO₃, Cl y SO₄",
                        "Nitratos, hierro y otros parámetros disponibles",
                    ],
                }
            )

            st.dataframe(
                parametros,
                use_container_width=True,
                hide_index=True,
            )

        with c2:
            mostrar_tarjeta(
                "Diagramas futuros",
                "Piper, Schoeller o Stiff, únicamente si las muestras y unidades están completas.",
                "📈",
            )

# =========================================================
# CALIDAD DEL AGUA E IRCA
# =========================================================

elif seccion == "Calidad del agua e IRCA":
    st.title(f"🚰 Calidad del agua e IRCA – {territorio}")

    st.write(
        "Esta sección presenta la clasificación del riesgo y, cuando existe "
        "información georreferenciada, la ubicación de los puntos evaluados."
    )

    if territorio == "Leticia":
        mostrar_mapa_imagen(
            "pozos_irca",
            "Pozos y clasificación del riesgo IRCA en Leticia",
            "SENA – recurso académico de aguas subterráneas de Leticia",
            "El mapa corresponde a puntos específicos y no representa automáticamente "
            "la calidad del agua de toda el área municipal.",
        )

    irca = pd.DataFrame(
        {
            "Clasificación": [
                "Sin riesgo",
                "Riesgo bajo",
                "Riesgo medio",
                "Riesgo alto",
                "Inviable sanitariamente",
                "Sin información",
            ],
            "Representación": [
                "Verde",
                "Azul",
                "Amarillo",
                "Naranja",
                "Rojo",
                "Gris",
            ],
        }
    )

    st.dataframe(
        irca,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "La clasificación debe verificarse con el valor, la fecha, la fuente y el "
        "punto de muestreo representado."
    )

# =========================================================
# SENTINEL-2 · VISOR SATELITAL POR SEDE
# =========================================================

elif seccion == "Sentinel-2":
    st.title(f"🛰️ Sentinel-2 · {territorio}")
    mostrar_sentinel_territorio(territorio)

elif seccion == "Landsat":
    st.title(f"🛰️ Landsat · {territorio}")
    mostrar_landsat_territorio(territorio)

# =========================================================
# COBERTURA Y RELIEVE
# =========================================================

elif seccion == "Cobertura y relieve":
    st.title(f"🌿 Cobertura y relieve de {territorio}")
    tab_coberturas, tab_landsat, tab_cartografia = st.tabs([
        "Coberturas MapBiomas", "Landsat · evolución por fechas", "Mapas y relieve"
    ])
    with tab_coberturas:
        mostrar_coberturas_mapbiomas(territorio)
    with tab_landsat:
        mostrar_landsat_territorio(territorio)
    with tab_cartografia:
        if territorio in {"Leticia", "Tumaco"}:
            tab1, tab2 = st.tabs(["Cobertura", "Relieve y geomorfología"])
            with tab1:
                if territorio == "Leticia":
                    mostrar_mapa_imagen("cobertura", "Coberturas de la tierra del municipio de Leticia", "Instituto SINCHI")
                else:
                    mostrar_mapa_imagen("cobertura", "Cobertura y uso actual de la tierra en la cuenca del río Mira", "CORPONARIÑO – POMCA Río Mira")
            with tab2:
                if territorio == "Leticia":
                    mostrar_mapa_imagen("relieve", "Geomorfología y características generales del relieve del Trapecio Sur", "Instituto SINCHI")
                else:
                    mostrar_mapa_imagen("relieve", "Distribución de pendientes en la cuenca hidrográfica del río Mira", "CORPONARIÑO – POMCA Río Mira")
        elif territorio == "Medellín":
            st.subheader("Estructura Ecológica Principal")
            mostrar_mapa_imagen(
                "estructura_ecologica", "Estructura Ecológica Principal de Medellín",
                "Alcaldía de Medellín – Plan de Ordenamiento Territorial (POT)",
                "Se incorpora como contexto ambiental municipal para relacionar corredores, áreas de interés ecológico y el sistema hídrico con el entorno urbano.",
            )
            st.info("Para completar esta sección conviene agregar después un mapa de pendientes o un DEM recortado alrededor de la sede.")
        elif territorio == "San Andrés":
            st.info("Todavía no se incorporó cartografía específica de relieve para San Andrés. Consulta los CSV de SA y SAC en la pestaña Coberturas MapBiomas.")
        else:
            st.info(f"Para {territorio} todavía no se incorporaron mapas de relieve en este bloque. Las estadísticas CSV se consultan en Coberturas MapBiomas cuando están disponibles.")

# =========================================================
# ESTACIONES Y DATOS
# =========================================================

elif seccion == "Estaciones y datos":
    st.title(f"📚 Estaciones y disponibilidad de datos – {territorio}")

    archivo_ideam = ARCHIVOS_IDEAM.get(territorio)
    if territorio in {"Tumaco", "Arauca"} and archivo_ideam is not None:
        try:
            _, _, control_ideam, fuentes_ideam = cargar_ideam_tumaco(str(archivo_ideam))
            st.subheader("Resumen de decisión por variable")
            st.dataframe(
                decisiones_climaticas_ideam(control_ideam, territorio),
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Estaciones IDEAM utilizadas")
            fuentes_mostrar = fuentes_ideam.copy()
            for columna in ("Fecha_inicial", "Fecha_final"):
                if columna in fuentes_mostrar.columns:
                    fuentes_mostrar[columna] = fuentes_mostrar[columna].apply(
                        lambda x: x.strftime("%Y-%m-%d") if hasattr(x, "strftime") else "—"
                    )
            columnas = [
                "Variable", "CodigoEstacion", "NombreEstacion", "Parametro",
                "Unidad", "Fecha_inicial", "Fecha_final", "Registros",
            ]
            st.dataframe(
                fuentes_mostrar[[c for c in columnas if c in fuentes_mostrar.columns]],
                use_container_width=True,
                hide_index=True,
            )

            if territorio == "Arauca":
                st.warning(
                    "En Arauca, la temperatura media es derivada de Tmax y Tmin. La humedad relativa "
                    "media usa una serie mínima inferida; validar ese metadato IDEAM antes de publicación definitiva."
                )
        except Exception as error:
            st.error(f"No fue posible leer el inventario IDEAM de {territorio}.")
            st.code(str(error), language=None)
    else:
        st.dataframe(
            tabla_disponibilidad(territorio),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown(
        """
        Para cada estación se documentan nombre, código, variable, periodo, registros,
        completitud y criterio de uso. Las fuentes IDEAM y NASA POWER se conservan separadas:
        una comparación entre ambas no implica que las series hayan sido fusionadas.
        """
    )

# =========================================================
# MONITOREO Y CURVAS
# =========================================================

elif seccion == "Monitoreo y curvas":
    st.title(f"📡 Monitoreo y curvas – {territorio}")

    st.warning(
        "Esta sección corresponde al monitoreo con sondas o niveles medidos en campo. "
        "Cuando no existan series validadas, no se publican gráficas demostrativas. "
        "El producto satelital GWSa se consulta por separado en Subsuelo y calidad del agua."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        mostrar_tarjeta(
            "Serie requerida",
            "Fecha, hora, nivel o profundidad, cota de referencia y control de valores faltantes.",
            "📈",
        )
    with c2:
        mostrar_tarjeta(
            "Lluvia asociada",
            "Precipitación del mismo periodo, fuente, unidad y resolución temporal compatibles.",
            "🌧️",
        )
    with c3:
        mostrar_tarjeta(
            "Producto futuro",
            "Curvas precipitación–nivel, eventos, tiempo de respuesta y coeficiente aprobado.",
            "🧪",
        )

    st.markdown(dedent("""
        <div class="soft-box">
            <strong>Criterio de publicación:</strong> esta sección solo se habilitará cuando las
            series hayan sido procesadas externamente, revisadas y acompañadas por una metodología.
            La página mostrará resultados finales; no realizará el procesamiento de sondas en línea.
        </div>
        """).strip(), unsafe_allow_html=True)

# =========================================================
# COMPARAR TERRITORIOS
# =========================================================

elif seccion == "Comparar territorios":

    st.title("⚖️ Comparación climática entre territorios")

    st.markdown(
        """
        <div class="soft-box">
            <strong>Criterio de comparación:</strong>
            Leticia, Medellín, San Andrés y La Paz utilizan NASA POWER cuando el archivo procesado está disponible.
            Tumaco y Arauca utilizan IDEAM como referencia terrestre para precipitación y temperatura,
            mientras que NASA POWER se usa como contraste y para variables sin observación terrestre equivalente.
            En Arauca la humedad IDEAM se muestra con advertencia metodológica. Las fuentes no se fusionan.
        </div>
        """,
        unsafe_allow_html=True,
    )

    datasets = []
    fuentes_resumen = []

    # -----------------------------------------------------
    # TERRITORIOS NASA POWER COMO FUENTE PRINCIPAL
    # -----------------------------------------------------
    for nombre in ("Leticia", "Medellín", "San Andrés", "La Paz"):
        archivo = ARCHIVOS_CLIMA_NASA.get(nombre)
        if archivo is None:
            continue

        try:
            df_nasa, _ = cargar_clima_leticia(str(archivo))
            temporal = df_nasa.copy()
            temporal["Territorio"] = nombre
            temporal["Fuente principal"] = "NASA POWER"
            datasets.append(temporal)

            fuentes_resumen.append({
                "Territorio": nombre,
                "Precipitación": "NASA POWER",
                "Temperatura": "NASA POWER",
                "Humedad": "NASA POWER",
                "Viento / presión / radiación": "NASA POWER",
            })
        except Exception:
            logger.exception("M3: fallo al cargar NASA POWER en comparación territorial: %s", nombre)
            st.warning(f"No fue posible incorporar los datos NASA POWER de {nombre} en la comparación.")

    # -----------------------------------------------------
    # TUMACO Y ARAUCA: IDEAM + NASA POWER
    # -----------------------------------------------------
    for nombre in ("Tumaco", "Arauca"):
        archivo_i = ARCHIVOS_IDEAM.get(nombre)
        archivo_n = archivo_nasa_territorio(nombre)

        if archivo_i is None:
            # Si IDEAM falta pero NASA existe, no se elimina el territorio de la comparación.
            if archivo_n is not None:
                try:
                    df_n, _ = cargar_clima_leticia(str(archivo_n))
                    temporal = df_n.copy()
                    temporal["Territorio"] = nombre
                    temporal["Fuente principal"] = "NASA POWER (IDEAM no detectado)"
                    datasets.append(temporal)
                    fuentes_resumen.append({
                        "Territorio": nombre,
                        "Precipitación": "NASA POWER (fallback)",
                        "Temperatura": "NASA POWER (fallback)",
                        "Humedad": "NASA POWER (fallback)",
                        "Viento / presión / radiación": "NASA POWER",
                    })
                except Exception:
                    logger.exception("M3: fallo en la fuente alternativa NASA POWER para %s", nombre)
                    st.warning(f"{nombre}: IDEAM no está disponible y tampoco se pudo cargar NASA POWER; el territorio se omite de la comparación.")
            continue

        try:
            df_i, _, _, _ = cargar_ideam_tumaco(str(archivo_i))
            combinado = df_i.copy()
            contraste_nasa_disponible = False

            if archivo_n is not None:
                try:
                    df_n, _ = cargar_nasa_tumaco(str(archivo_n))
                    combinado = combinado.merge(df_n, on="Mes", how="left")
                    contraste_nasa_disponible = True
                except Exception:
                    logger.exception("M3: fallo al combinar NASA POWER con IDEAM para %s", nombre)
                    st.warning(f"{nombre}: no se pudo incorporar el contraste NASA POWER. Se conservan los datos IDEAM disponibles.")

            if nombre == "Arauca":
                humedad = (
                    combinado["Humedad IDEAM (%)"]
                    if "Humedad IDEAM (%)" in combinado.columns else pd.NA
                )
                fuente_hr = ("IDEAM con advertencia + contraste NASA" if contraste_nasa_disponible
                             else "IDEAM (sin contraste NASA)")
            else:
                humedad = (
                    combinado["Humedad NASA (%)"]
                    if "Humedad NASA (%)" in combinado.columns
                    else combinado.get("Humedad IDEAM (%)", pd.NA)
                )
                fuente_hr = ("NASA POWER + contraste IDEAM" if "Humedad NASA (%)" in combinado.columns
                             else "IDEAM" if "Humedad IDEAM (%)" in combinado.columns
                             else "No disponible")

            temporal = pd.DataFrame({
                "Mes": combinado["Mes"],
                "Precipitación mensual (mm)": combinado["Precipitación IDEAM (mm)"],
                "Temperatura media (°C)": combinado["Temperatura media IDEAM (°C)"],
                "Temperatura máxima (°C)": combinado.get("Temperatura máxima IDEAM (°C)", pd.NA),
                "Temperatura mínima (°C)": combinado.get("Temperatura mínima IDEAM (°C)", pd.NA),
                "Humedad relativa (%)": humedad,
                "Viento a 2 m (m/s)": combinado.get("Viento a 2 m NASA (m/s)", pd.NA),
                "Presión superficial (kPa)": combinado.get("Presión NASA (kPa)", pd.NA),
                "Radiación solar (MJ/m²/día)": combinado.get("Radiación NASA (MJ/m²/día)", pd.NA),
                "Territorio": nombre,
                "Fuente principal": "IDEAM + NASA POWER" if contraste_nasa_disponible else "IDEAM (sin contraste NASA POWER)",
            })
            datasets.append(temporal)

            fuentes_resumen.append({
                "Territorio": nombre,
                "Precipitación": "IDEAM",
                "Temperatura": "IDEAM",
                "Humedad": fuente_hr,
                "Viento / presión / radiación": "NASA POWER" if contraste_nasa_disponible else "No disponible (sin contraste NASA POWER)",
            })
        except Exception:
            logger.exception("M3: fallo al procesar IDEAM en comparación territorial: %s", nombre)
            st.warning(f"No fue posible incorporar los datos IDEAM de {nombre} en la comparación.")

    # -----------------------------------------------------
    # VISUALIZACIÓN
    # -----------------------------------------------------
    if datasets:
        comparar = pd.concat(datasets, ignore_index=True, sort=False)

        tab_p, tab_t, tab_hr, tab_otras, tab_resumen, tab_fuentes = st.tabs([
            "Precipitación",
            "Temperatura",
            "Humedad",
            "Viento, presión y radiación",
            "Resumen anual",
            "Fuentes",
        ])

        with tab_p:
            fig = px.bar(
                comparar,
                x="Mes",
                y="Precipitación mensual (mm)",
                color="Territorio",
                barmode="group",
                title="Régimen mensual de precipitación",
            )
            fig.update_layout(
                xaxis_title="Mes",
                yaxis_title="Precipitación mensual (mm)",
                legend_title_text="Territorio",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Tumaco y Arauca usan precipitación IDEAM; Leticia, Medellín, San Andrés y La Paz usan NASA POWER."
            )

        with tab_t:
            fig = px.line(
                comparar,
                x="Mes",
                y="Temperatura media (°C)",
                color="Territorio",
                markers=True,
                title="Temperatura media mensual",
            )
            fig.update_layout(
                xaxis_title="Mes",
                yaxis_title="Temperatura media (°C)",
                legend_title_text="Territorio",
            )
            st.plotly_chart(fig, use_container_width=True)

            resumen_temp = (
                comparar.groupby("Territorio")
                .agg(
                    Temperatura_media_C=("Temperatura media (°C)", "mean"),
                    Temperatura_min_media_C=("Temperatura media (°C)", "min"),
                    Temperatura_max_media_C=("Temperatura media (°C)", "max"),
                )
                .reset_index()
            )
            resumen_temp["Amplitud_media_mensual_C"] = (
                resumen_temp["Temperatura_max_media_C"] - resumen_temp["Temperatura_min_media_C"]
            )
            st.dataframe(resumen_temp.round(2), use_container_width=True, hide_index=True)

        with tab_hr:
            datos_hr = comparar.dropna(subset=["Humedad relativa (%)"])
            if not datos_hr.empty:
                fig = px.line(
                    datos_hr,
                    x="Mes",
                    y="Humedad relativa (%)",
                    color="Territorio",
                    markers=True,
                    title="Humedad relativa mensual",
                )
                fig.update_layout(
                    xaxis_title="Mes",
                    yaxis_title="Humedad relativa (%)",
                    yaxis=dict(range=[0, 100]),
                    legend_title_text="Territorio",
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption(
                    "Arauca usa IDEAM con advertencia metodológica; Tumaco prioriza NASA POWER para humedad continua."
                )
            else:
                st.info("No hay datos de humedad disponibles para comparar.")

        with tab_otras:
            opciones = {
                "Viento a 2 m": "Viento a 2 m (m/s)",
                "Presión superficial": "Presión superficial (kPa)",
                "Radiación solar": "Radiación solar (MJ/m²/día)",
            }
            seleccion = st.selectbox(
                "Variable",
                list(opciones.keys()),
                key="comparacion_otras_territorios",
            )
            columna = opciones[seleccion]
            datos_variable = comparar.dropna(subset=[columna])

            if not datos_variable.empty:
                fig = px.line(
                    datos_variable,
                    x="Mes",
                    y=columna,
                    color="Territorio",
                    markers=True,
                    title=f"{seleccion} · comparación entre territorios",
                )
                fig.update_layout(xaxis_title="Mes", legend_title_text="Territorio")
                st.plotly_chart(fig, use_container_width=True)
                st.caption(
                    "Viento, presión y radiación se comparan con NASA POWER para mantener una fuente homogénea."
                )
            else:
                st.info(f"No hay suficientes datos de {seleccion.lower()} para construir la comparación.")

        with tab_resumen:
            resumen = (
                comparar.groupby("Territorio")
                .agg(
                    Precipitacion_anual_mm=("Precipitación mensual (mm)", "sum"),
                    Temperatura_media_C=("Temperatura media (°C)", "mean"),
                    Humedad_media_pct=("Humedad relativa (%)", "mean"),
                    Viento_medio_m_s=("Viento a 2 m (m/s)", "mean"),
                    Presion_media_kPa=("Presión superficial (kPa)", "mean"),
                    Radiacion_media_MJ_m2_dia=("Radiación solar (MJ/m²/día)", "mean"),
                )
                .reset_index()
            )
            st.dataframe(resumen.round(2), use_container_width=True, hide_index=True)

            if not resumen.empty:
                mas_lluvioso = resumen.loc[resumen["Precipitacion_anual_mm"].idxmax()]
                mas_calido = resumen.loc[resumen["Temperatura_media_C"].idxmax()]
                mas_humedo = resumen.dropna(subset=["Humedad_media_pct"])

                c1, c2, c3 = st.columns(3)
                c1.metric(
                    "Mayor precipitación anual",
                    mas_lluvioso["Territorio"],
                    f"{mas_lluvioso['Precipitacion_anual_mm']:.0f} mm",
                )
                c2.metric(
                    "Mayor temperatura media",
                    mas_calido["Territorio"],
                    f"{mas_calido['Temperatura_media_C']:.1f} °C",
                )
                if not mas_humedo.empty:
                    fila_h = mas_humedo.loc[mas_humedo["Humedad_media_pct"].idxmax()]
                    c3.metric(
                        "Mayor humedad media",
                        fila_h["Territorio"],
                        f"{fila_h['Humedad_media_pct']:.1f} %",
                    )

        with tab_fuentes:
            st.subheader("Fuente principal por variable")
            st.dataframe(
                pd.DataFrame(fuentes_resumen),
                use_container_width=True,
                hide_index=True,
            )
            st.warning(
                "Las diferencias observadas no deben interpretarse únicamente como diferencias climáticas. "
                "También influyen la fuente de datos, el periodo de análisis y la escala espacial de cada producto."
            )
    else:
        st.warning(
            "No se encontraron suficientes archivos climáticos para construir la comparación entre territorios."
        )

# =========================================================
# METODOLOGÍA
# =========================================================

elif seccion == "Metodología":
    st.title("🧭 Metodología")

    pasos = [
        (
            "1. Selección del territorio",
            "Definición de la sede y del área principal de análisis.",
        ),
        (
            "2. Consulta de fuentes",
            "Búsqueda de IDEAM, NASA POWER, SGC, IGAC, SIAC y otras entidades.",
        ),
        (
            "3. Control de calidad",
            "Revisión de periodos, vacíos, continuidad y confiabilidad.",
        ),
        (
            "4. Procesamiento",
            "Preparación de series, mapas, indicadores y resultados en herramientas externas.",
        ),
        (
            "5. Revisión técnica",
            "Validación de textos, gráficas, unidades y limitaciones.",
        ),
        (
            "6. Publicación",
            "Carga de resultados revisados en la plataforma.",
        ),
    ]

    for titulo, texto in pasos:
        st.markdown(dedent(f"""
            <div class="card" style="min-height:auto;">
                <h3>{titulo}</h3>
                <p>{texto}</p>
            </div>
            """).strip(), unsafe_allow_html=True)

# =========================================================
# FUENTES Y DESCARGAS
# =========================================================

elif seccion == "Fuentes y descargas":

    st.title("📂 Fuentes y descargas")

    tab_archivos, tab_mapas, tab_fuentes = st.tabs([
        "Archivos de datos", "Estado de mapas", "Inventario de fuentes"
    ])

    with tab_archivos:
        st.write(
            "Los botones se habilitan únicamente cuando el archivo existe junto al script o en una carpeta de datos reconocida."
        )
        archivos = [
            ("NASA POWER · Leticia", ARCHIVO_CLIMA_LETICIA, "descarga_fuente_leticia"),
            ("NASA POWER · Medellín", ARCHIVO_CLIMA_MEDELLIN, "descarga_fuente_medellin"),
            ("NASA POWER · San Andrés", ARCHIVO_CLIMA_SAN_ANDRES, "descarga_fuente_san_andres"),
            ("NASA POWER · Arauca", ARCHIVO_CLIMA_ARAUCA, "descarga_fuente_arauca"),
            ("NASA POWER · La Paz", ARCHIVO_CLIMA_LA_PAZ, "descarga_fuente_la_paz"),
            ("NASA POWER · Tumaco", ARCHIVO_NASA_TUMACO, "descarga_fuente_nasa_tumaco"),
            ("IDEAM procesado · Tumaco", ARCHIVO_IDEAM_TUMACO, "descarga_fuente_ideam_tumaco"),
            ("IDEAM procesado · Arauca", ARCHIVO_IDEAM_ARAUCA, "descarga_fuente_ideam_arauca"),
            ("GWSa Colombia · GRACE/GLDAS", ARCHIVO_GWS, "descarga_fuente_gws"),
        ]
        for nombre_cob, config_cob in COBERTURAS_POR_TERRITORIO.items():
            for codigo_cob, zona_cob in config_cob["zonas"].items():
                rutas_cob = encontrar_csv_coberturas(nombre_cob, codigo_cob)
                for tipo_cob, candidatos_cob in rutas_cob.items():
                    ruta_cob = candidatos_cob[0] if len(candidatos_cob) == 1 else None
                    archivos.append((f"MapBiomas · {zona_cob} · {tipo_cob}", ruta_cob, f"fuente_cob_{codigo_cob}_{tipo_cob}"))
        estado = []
        for etiqueta, ruta, clave_boton in archivos:
            estado.append({
                "Archivo": etiqueta,
                "Nombre detectado": Path(ruta).name if ruta else "—",
                "Estado": archivo_disponible(ruta),
            })
            if ruta is not None and Path(ruta).exists():
                with open(ruta, "rb") as archivo:
                    extension = Path(ruta).suffix.lower()
                    mime = (
                        "text/csv" if extension == ".csv"
                        else "application/x-netcdf" if extension == ".nc"
                        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.download_button(
                        f"Descargar {etiqueta}",
                        data=archivo.read(),
                        file_name=Path(ruta).name,
                        mime=mime,
                        key=clave_boton,
                    )
        st.dataframe(pd.DataFrame(estado), use_container_width=True, hide_index=True)

    with tab_mapas:
        st.write(f"**Ubicación detectada:** `{CARPETA_MAPAS}`")
        estado_mapas = []
        for nombre_territorio, mapas in MAPAS_POR_TERRITORIO.items():
            for clave, nombre_base in mapas.items():
                ruta = buscar_mapa(nombre_base)
                estado_mapas.append({
                    "Territorio": nombre_territorio,
                    "Mapa": clave.replace("_", " ").title(),
                    "Archivo esperado": nombre_base,
                    "Estado": "Encontrado" if ruta else "No encontrado",
                })
        for nombre_territorio, niveles in MAPAS_UBICACION_QGIS.items():
            for nivel in niveles:
                ruta = buscar_mapa(nivel["archivo"])
                estado_mapas.append({
                    "Territorio": nombre_territorio,
                    "Mapa": f"QGIS · {nivel['titulo']} · {nivel['escala']}",
                    "Archivo esperado": nivel["archivo"],
                    "Estado": "Encontrado" if ruta else "No encontrado",
                })
        st.dataframe(pd.DataFrame(estado_mapas), use_container_width=True, hide_index=True)

    with tab_fuentes:
        fuentes = pd.DataFrame({
            "Fuente": [
                "IDEAM", "NASA POWER", "Instituto SINCHI", "Corpoamazonia",
                "CORPONARIÑO / POMCA Río Mira", "Parques Nacionales", "SENA",
                "CORALINA", "Servicio Geológico Colombiano", "Alcaldía de Medellín / POT",
                "Romero & Piña (2025) · GRACE/GLDAS", "Cartografía de ubicación · Sede Bogotá",
                "SGC – PEXAS", "IDEAM – ENA / Anexo 7", "SIAMS",
            ],
            "Uso": [
                "Series terrestres y control de completitud", "Variables climáticas continuas",
                "Mapas regionales de Leticia", "Humedales e inundación de Leticia",
                "Geología, cobertura, relieve e inundación de Tumaco", "Contexto hídrico y costero de Tumaco",
                "Referencia académica de pozos e IRCA en Leticia",
                "Geología, acuíferos, nitratos y microcuencas de San Andrés",
                "Plancha geológica 228 de Medellín", "Estructura ecológica y amenaza por inundación de Medellín",
                "Anomalías de almacenamiento de agua subterránea (GWSa) para Colombia",
                "Ubicación nacional, regional y de campus para el piloto de la Sede Bogotá",
                "Criterios regionales de exploración y demanda hidrogeológica en Arauca",
                "Oferta hídrica, presión sobre el recurso, aguas subterráneas y sistema Arauca-Arauquita",
                "Procesamiento, decisiones de uso e integración web",
            ],
            "Condición": [
                "Principal o complementaria según variable", "Principal o complementaria según variable",
                "Referencia cartográfica", "Referencia cartográfica", "Referencia cartográfica",
                "Referencia cartográfica", "Referencia académica complementaria", "Referencia cartográfica",
                "Referencia cartográfica oficial", "Referencia cartográfica oficial",
                "Producto científico satelital / modelo global", "Elaboración cartográfica del proyecto",
                "Referencia cartográfica oficial", "Referencia cartográfica y ficha técnica oficial", "Producto académico",
            ],
        })
        st.dataframe(fuentes, use_container_width=True, hide_index=True)
        st.warning(
            "Antes de redistribuir mapas o documentos completos debe verificarse la licencia y la forma de citación de cada entidad."
        )

# =========================================================
# SOBRE SIAMS
# =========================================================

elif seccion == "Sobre SIAMS":
    mostrar_encabezado(
        "Sobre SIAMS",
        "Somos un equipo académico interesado en comprender y comunicar la relación "
        "entre el agua, el territorio y las comunidades.",
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        mostrar_tarjeta(
            "Propósito",
            "Organizar información hidroambiental y facilitar su consulta para distintos públicos.",
            "🎯",
        )

    with c2:
        mostrar_tarjeta(
            "Qué hacemos",
            "Consulta, procesamiento, análisis cartográfico, monitoreo y divulgación.",
            "🔎",
        )

    with c3:
        mostrar_tarjeta(
            "Alcance",
            "Proyecto académico e informativo que no reemplaza estudios técnicos oficiales.",
            "📘",
        )

    st.subheader("Información institucional pendiente")

    st.markdown(
        """
        - Reseña oficial del semillero.
        - Docente coordinador.
        - Integrantes autorizados.
        - Líneas de trabajo.
        - Logos.
        - Contacto institucional.
        """
    )

st.divider()

st.caption(
    f"SIAMS · Universidad Nacional de Colombia · Prototipo hidroambiental · "
    f"Territorio seleccionado: {territorio} · Actualización: {FECHA_ACTUALIZACION}"
)
