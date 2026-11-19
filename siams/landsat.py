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
CARPETA_LANDSAT_CSV = CARPETA_PROYECTO / "data/processed/landsat"

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
    """Inventario de videos MP4, GIF y CSV asociados a una sede.

    Se mantienen las claves anteriores para que app.py y los tests existentes
    sigan funcionando. Se prefiere MP4 sin ocultar otros años disponibles.
    """
    carpeta = carpeta_landsat_sede(nombre_territorio)
    if carpeta is None:
        return {
            "carpeta": None, "gifs": [], "videos": [], "animaciones": [],
            "areas": None, "control": None,
        }

    archivos = [p for p in carpeta.iterdir() if p.is_file()]
    gifs = sorted(
        [p for p in archivos if p.suffix.casefold() == ".gif"
         and normalizar_etiqueta(p.stem).startswith("gif_landsat")],
        key=lambda p: p.name.casefold(),
    )
    videos = sorted(
        [p for p in archivos if p.suffix.casefold() == ".mp4"
         and "landsat" in normalizar_etiqueta(p.stem)],
        key=lambda p: p.name.casefold(),
    )

    # Si se dejó una versión _COMPRIMIDO junto con la de nombre definitivo,
    # preferimos la definitiva para no duplicar visualmente el mismo año.
    anios_normales = {
        anio_gif_landsat(p) for p in videos
        if not p.stem.casefold().endswith("_comprimido")
    }
    videos = [
        p for p in videos
        if not (p.stem.casefold().endswith("_comprimido")
                and anio_gif_landsat(p) in anios_normales)
    ]
    animaciones = sorted(
        [*videos, *gifs],
        key=lambda p: (
            -(anio_gif_landsat(p) or 0),
            0 if p.suffix.casefold() == ".mp4" else 1,
            p.name.casefold(),
        ),
    )

    def csv_buscar(nombre):
        nuevo = CARPETA_LANDSAT_CSV / carpeta.name / nombre
        if nuevo.is_file():
            return nuevo
        return next((p for p in archivos if p.name.casefold() == nombre.casefold()), None)

    return {
        "carpeta": carpeta,
        "gifs": gifs,
        "videos": videos,
        "animaciones": animaciones,
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

# --- Interfaz Landsat con criterios documentados (2026) -----------------------
# Los GIF/MP4 antiguos se conservan en el inventario por compatibilidad, pero
# no se muestran: el panel usa compuestos y escenas que cumplen los criterios.

import json
import tomllib


def _criterios_landsat() -> dict:
    """Carga los umbrales del proyecto, sin alterarlos silenciosamente."""
    ruta = CARPETA_PROYECTO / "config" / "landsat_criterios.toml"
    if not ruta.is_file():
        return {}
    try:
        with ruta.open("rb") as archivo:
            return tomllib.load(archivo)
    except (OSError, tomllib.TOMLDecodeError) as error:
        st.warning(f"No se pudo cargar la configuración Landsat: {error}")
        return {}


def _metadatos_landsat(carpeta: Path) -> pd.DataFrame:
    """Lee las decisiones del script 07, sin recalcular ni cambiar 'cumple'."""
    ruta = carpeta / "metadatos_escenas.csv"
    df = _leer_landsat_si_existe(ruta)
    if df is None or df.empty:
        return pd.DataFrame()
    requeridas = {"fecha", "id_escena", "cumple", "nube_aoi_pct"}
    if not requeridas.issubset(df.columns):
        st.warning(
            f"`{ruta.name}` no contiene las columnas necesarias: "
            + ", ".join(sorted(requeridas - set(df.columns)))
        )
        return pd.DataFrame()
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["cumple"] = df["cumple"].astype(str).str.strip().str.casefold().isin(
        ["true", "1", "si", "sí"]
    )
    df["nube_aoi_pct"] = pd.to_numeric(df["nube_aoi_pct"], errors="coerce")
    df["nubosidad_catalogo_pct"] = pd.to_numeric(
        df.get("nubosidad_catalogo_pct", pd.Series(index=df.index, dtype=float)),
        errors="coerce",
    )
    return df.dropna(subset=["fecha"]).sort_values("fecha", ascending=False)


def _escenas_landsat_validas(meta: pd.DataFrame, umbral_pct: float) -> pd.DataFrame:
    """Solo permite estrechar el filtro precomputado (nunca relajar el original)."""
    if meta.empty:
        return meta.copy()
    return meta.loc[
        meta["cumple"]
        & meta["nube_aoi_pct"].notna()
        & meta["nube_aoi_pct"].le(umbral_pct)
    ].copy()


def _compuestos_landsat(carpeta: Path) -> list[dict]:
    """Lee fichas JSON y empareja únicamente las imágenes de esa misma carpeta."""
    origen = carpeta / "compuestos"
    if not origen.is_dir():
        return []
    resultado = []
    for ruta in sorted(origen.glob("*_compuesto.json"), reverse=True):
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as error:
            st.warning(f"No se pudo leer `{ruta.name}`: {error}")
            continue
        imagenes = datos.get("imagenes", {})
        rutas_imagenes = {}
        for nombre in ("color_natural", "falso_color"):
            archivo = imagenes.get(nombre, "")
            # Los nombres provienen del JSON local; impedir rutas fuera de compuestos/.
            if not isinstance(archivo, str) or Path(archivo).name != archivo:
                continue
            posible = origen / archivo
            if posible.is_file() and posible.suffix.casefold() in {".jpg", ".jpeg", ".png"}:
                rutas_imagenes[nombre] = posible
        resultado.append({"ficha": ruta, "datos": datos, "imagenes": rutas_imagenes})
    return resultado


def _compuesto_principal_chingaza(compuestos, max_sin_dato):
    """Prefiere un compuesto conjunto aprobado; si falta, el anual aprobado más reciente."""
    candidatos = []
    for i, c in enumerate(compuestos):
        d = c["datos"]
        try:
            falta = float(d["aoi_sin_observacion_pct"])
            temporadas = d["temporadas"]
            if (d.get("sede") != "Chingaza" or d.get("publicable") is not True
                    or not math.isfinite(falta) or not 0 <= falta <= max_sin_dato
                    or not temporadas or not {"color_natural", "falso_color"}.issubset(c["imagenes"])):
                continue
            candidatos.append((len(set(temporadas)), max(temporadas), -i, i))
        except (KeyError, TypeError, ValueError):
            continue
    return max(candidatos)[-1] if candidatos else 0


def _imagen_escena_landsat(carpeta: Path, id_escena: str):
    """Busca PNG validado por el script 07 para un ID Landsat bien formado."""
    if not isinstance(id_escena, str) or not re.fullmatch(r"[A-Za-z0-9_\-]+", id_escena):
        return None
    ruta = carpeta / "escenas" / f"{id_escena}.png"
    return ruta if ruta.is_file() else None


def _descarga_landsat(ruta: Path, etiqueta: str, clave: str) -> None:
    if not ruta.is_file():
        return
    tipos = {".csv": "text/csv", ".json": "application/json",
             ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".mp4": "video/mp4"}
    st.download_button(
        etiqueta, data=ruta.read_bytes(), file_name=ruta.name,
        mime=tipos.get(ruta.suffix.casefold(), "application/octet-stream"),
        key=clave,
    )


def mostrar_landsat_territorio(nombre_territorio: str) -> None:
    """Muestra compuestos, escenas verificadas, series y trazabilidad.

    Los criterios científicos provienen de `config/landsat_criterios.toml` y
    `metadatos_escenas.csv`; esta interfaz NO reclasifica imágenes.
    """
    inv = inventario_landsat(nombre_territorio)
    carpeta = inv["carpeta"]
    slug = normalizar_etiqueta(nombre_territorio)

    st.caption("SIAMS · OBSERVACIÓN SATELITAL")
    st.markdown("### Landsat · imágenes con criterios")
    st.caption("Compuestos multitemporales, escenas de calidad y trazabilidad.")
    st.info(
        "Para análisis de cambios de cobertura, **MapBiomas es la referencia**. "
        "Las imágenes Landsat de este apartado son productos de observación y la "
        "clasificación propia es preliminar; no equivale a una validación de coberturas."
    )

    if carpeta is None:
        st.warning(f"No se encontró la carpeta Landsat para {nombre_territorio}.")
        return

    criterios = _criterios_landsat()
    general = criterios.get("general", {})
    valores_compuesto = criterios.get("compuestos", {})
    if not criterios:
        st.warning(
            "Falta `config/landsat_criterios.toml` o no se pudo leer. "
            "Se utilizarán las decisiones ya calculadas en el CSV, "
            "sin recalcular filtros; verifica la configuración antes de publicar."
        )
    umbral_base = float(general.get("nube_aoi_max_pct", 20.0))
    max_sin_dato = float(valores_compuesto.get("sin_dato_max_pct", 5.0))
    meses = criterios.get("ventana_estacional", {}).get(nombre_territorio)
    if meses is None:
        meses = next(
            (valor for sede, valor in criterios.get("ventana_estacional", {}).items()
             if normalizar_etiqueta(sede) == slug), None
        )

    compuestos = _compuestos_landsat(carpeta)
    meta = _metadatos_landsat(carpeta)
    solo_compuestos = slug == "chingaza" and meta.empty
    umbral = umbral_base
    if not solo_compuestos:
        umbral = st.slider(
            "Máximo de AOI sin dato útil para mostrar escenas ya aprobadas (%)",
            min_value=0.0, max_value=max(umbral_base, 0.1), value=umbral_base,
            step=0.5,
            help="Solo filtra de forma más estricta las escenas que ya pasaron "
                 "el procesamiento; no permite aprobar escenas rechazadas.",
            key=f"landsat_nube_aoi_{slug}",
        )
    validas = _escenas_landsat_validas(meta, float(umbral))
    n_aprobadas_original = int(meta["cumple"].sum()) if not meta.empty else 0
    etiquetas = ["Compuesto de temporada seca", "Escenas que cumplen",
                 "Series de coberturas", "Metadatos y descargas"]
    vistas = dict(zip(etiquetas, st.tabs(etiquetas)))

    with vistas["Compuesto de temporada seca"]:
        if nombre_territorio == "Chingaza":
            st.caption("Área de interés: límite del PNN Chingaza del proyecto SIG. No es un buffer circular ni toda la zona de influencia.")
        st.markdown("#### Compuesto multitemporal de temporada seca")
        if not compuestos:
            st.info("No hay compuestos JPG/JSON disponibles para esta sede.")
        else:
            nombres = [c["datos"].get("periodo", c["ficha"].stem) for c in compuestos]
            if slug == "chingaza":
                principal = _compuesto_principal_chingaza(compuestos, max_sin_dato)
                indice = principal
                if len(compuestos) > 1:
                    with st.expander("Consultar otros compuestos por temporada", expanded=False):
                        opciones = [principal] + [i for i in range(len(compuestos)) if i != principal]
                        indice = st.selectbox("Período del compuesto", opciones,
                            format_func=lambda i: str(nombres[i]), key=f"landsat_compuesto_chingaza_v2")
                st.caption(f"Período mostrado: {nombres[indice]}.")
            else:
                indice = (st.selectbox(
                    "Período del compuesto", range(len(compuestos)),
                    format_func=lambda i: str(nombres[i]),
                    key=f"landsat_compuesto_{slug}",
                ) if len(compuestos) > 1 else 0)
            elegido = compuestos[indice]
            datos = elegido["datos"]
            faltantes = float(datos.get("aoi_sin_observacion_pct", 100.0))
            publicable = datos.get("publicable") is True and faltantes <= max_sin_dato
            a, b, c = st.columns(3)
            a.metric("Escenas consultadas", datos.get("escenas_consultadas", "—"))
            b.metric("Escenas utilizadas", datos.get("escenas_usadas", "—"))
            c.metric("AOI sin observación", f"{faltantes:.2f} %")
            if not publicable:
                st.warning(
                    "La ficha no autoriza publicar este compuesto o supera el máximo "
                    f"de área sin observaciones ({max_sin_dato:g} %)."
                )
            else:
                natural, falso = st.columns(2)
                with natural:
                    st.markdown("**Color natural (B4–B3–B2)**")
                    ruta = elegido["imagenes"].get("color_natural")
                    if ruta:
                        st.image(str(ruta), width="stretch")
                    else:
                        st.info("No está disponible la imagen de color natural.")
                with falso:
                    st.markdown("**Falso color (SWIR1–NIR–rojo)**")
                    ruta = elegido["imagenes"].get("falso_color")
                    if ruta:
                        st.image(str(ruta), width="stretch")
                    else:
                        st.info("No está disponible la imagen de falso color.")
            st.caption(
                f"Fuente: {datos.get('producto', 'Landsat C2 L2')} · "
                f"Observaciones: {datos.get('primera_fecha','—')} a "
                f"{datos.get('ultima_fecha','—')} · "
                f"Resolución: {datos.get('pixel_m', '—')} m."
            )
            st.warning(
                "Este compuesto combina observaciones de distintas fechas mediante "
                "mediana por píxel. **No es una escena única ni permite inferir por sí "
                "solo cambios temporales de cobertura.**"
            )

        if nombre_territorio in {"Bogotá", "Chingaza"} and meses:
            from .landsat_secuencia import fotogramas_aprobados
            origen = carpeta / "compuestos"
            video = origen / f"landsat_{slug}_temporadas.mp4"
            ficha_video = video.with_suffix(".json")
            if video.is_file() and ficha_video.is_file():
                try:
                    registros = fotogramas_aprobados(origen, max_sin_dato, nombre_territorio, meses)
                    vigente = len(registros) >= 2 and json.loads(ficha_video.read_text(encoding="utf-8")) == registros
                except (OSError, ValueError, RuntimeError):
                    vigente = False
                if vigente:
                    with st.expander("Evolución de compuestos anuales aprobados", expanded=False):
                        st.video(str(video), autoplay=True, loop=True, muted=True)
                        st.caption("Temporadas incluidas: " + ", ".join(str(r["temporada"]) for r in registros) + ". No se interpolan años faltantes.")
                        _descarga_landsat(video, "Descargar MP4", f"landsat_video_{slug}")
                else:
                    st.info("La secuencia debe regenerarse con las fichas aprobadas actuales.")

    with vistas["Escenas que cumplen"]:
        st.markdown("#### Escenas individuales que cumplen los criterios")
        if meta.empty:
            st.info("Pendiente de procesamiento de escenas individuales. El compuesto de temporada seca está separado de esta evaluación.")
        else:
            a, b, c = st.columns(3)
            a.metric("Escenas registradas", len(meta))
            b.metric("Aceptadas originalmente", n_aprobadas_original)
            c.metric("Visibles con este umbral", len(validas))
            if validas.empty:
                st.info(
                    "No hay escenas individuales que cumplan todos los criterios "
                    "y el umbral seleccionado. El compuesto multitemporal puede "
                    "estar disponible en la primera pestaña."
                )
            else:
                posibles = []
                for _, fila in validas.iterrows():
                    imagen = _imagen_escena_landsat(carpeta, str(fila["id_escena"]))
                    if imagen:
                        posibles.append((fila, imagen))
                if not posibles:
                    st.warning(
                        "Hay escenas aprobadas en el registro, pero faltan sus imágenes "
                        "PNG. No se mostrarán imágenes sin trazabilidad."
                    )
                else:
                    idx = st.selectbox(
                        "Fecha / escena validada", range(len(posibles)),
                        format_func=lambda i: (
                            f"{posibles[i][0]['fecha']:%Y-%m-%d} · "
                            f"{posibles[i][0]['id_escena']} · "
                            f"AOI sin dato {posibles[i][0]['nube_aoi_pct']:.1f} %"
                        ),
                        key=f"landsat_escena_{slug}",
                    )
                    fila, imagen = posibles[idx]
                    st.image(str(imagen), width="stretch")
                    st.caption(
                        f"Sensor: {fila.get('sensor', '—')} · "
                        f"Path/row: {fila.get('path_row', '—')} · "
                        f"Tier: {fila.get('tier', '—')} · "
                        f"Nubosidad catálogo: {fila.get('nubosidad_catalogo_pct', float('nan')):.1f} % "
                        f"(escena completa, distinta del AOI)."
                    )
                    _descarga_landsat(
                        imagen, "Descargar escena PNG",
                        f"landsat_png_{slug}_{imagen.stem}",
                    )
            st.caption(
                "El filtro `cumple` procede de `scripts/07_landsat_filtrar_escenas.py`. "
                "Cambiar los criterios exige regenerar los metadatos; este selector "
                "solo puede ser más estricto."
            )

    with vistas["Series de coberturas"]:
        st.markdown("#### Series de coberturas preliminares")
        df_areas, clases = _tabla_areas_landsat(_leer_landsat_si_existe(inv["areas"]))
        if meta.empty:
            st.info(
                "Serie de coberturas pendiente: falta la tabla de calidad "
                "con la cual identificar las fechas aceptadas."
            )
        elif validas.empty:
            st.info(
                "No existen fechas aprobadas bajo los criterios de calidad; "
                "no se publican series de clasificación para esta sede."
            )
        elif df_areas.empty or not clases:
            st.info("No hay una tabla de áreas de coberturas disponible o compatible.")
        else:
            fechas_validas = set(validas["fecha"].dt.normalize())
            filtrada = df_areas.loc[df_areas["Fecha"].dt.normalize().isin(fechas_validas)].copy()
            filtrada = filtrada.loc[filtrada["Área clasificada (ha)"].gt(0)]
            if filtrada.empty:
                st.info(
                    "Las fechas con clasificación disponible no coinciden con "
                    "las escenas que cumplen los criterios. No se grafica una serie no validada."
                )
            else:
                largos = filtrada.melt(
                    id_vars=["Fecha", "Área clasificada (ha)"],
                    value_vars=clases, var_name="Cobertura", value_name="Superficie (ha)",
                )
                largos["% del área clasificada"] = (
                    100 * largos["Superficie (ha)"].clip(lower=0)
                    / largos["Área clasificada (ha)"]
                )
                grafica = px.line(
                    largos, x="Fecha", y="% del área clasificada",
                    color="Cobertura", markers=True,
                    color_discrete_map=COLORES_LANDSAT,
                    labels={"Fecha": "Fecha de observación"},
                )
                grafica.update_layout(
                    height=450, margin=dict(l=10, r=10, t=25, b=5),
                    hovermode="x unified", legend_title_text="Cobertura",
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(grafica, width="stretch", key=f"landsat_serie_{slug}")
                st.caption(
                    "Porcentaje calculado sobre el área efectivamente clasificada "
                    "en cada fecha. Las hectáreas NO son directamente comparables "
                    "sin una máscara espacial común. Clasificación exploratoria, "
                    "sin validación independiente de exactitud."
                )
                with st.expander("Tabla de coberturas filtradas"):
                    st.dataframe(
                        filtrada[["Fecha"] + clases + ["Área clasificada (ha)"]],
                        hide_index=True, width="stretch",
                    )
        if inv["areas"] and inv["areas"].is_file():
            _descarga_landsat(
                inv["areas"], "Descargar CSV original de coberturas",
                f"landsat_areas_{slug}",
            )

    with vistas["Metadatos y descargas"]:
        st.markdown("#### Trazabilidad y control de calidad")
        st.markdown(
            f"**AOI sin dato útil permitido:** {umbral_base:g} %  "
            f"**Máximo sin observación en el compuesto:** {max_sin_dato:g} %  "
            f"**Meses de comparación:** {', '.join(map(str, meses)) if meses else 'no indicados'}"
        )
        st.caption(
            "AOI sin dato útil = píxeles no aprovechables dentro del área de interés de la sede. "
            "No equivale a la nubosidad reportada para la escena Landsat completa."
        )
        if meta.empty:
            st.caption("No hay un inventario de escenas individuales aprobado por el script 07. Los registros de las escenas consultadas por el script 08 se presentan en las fichas de los compuestos, cuando existen.")
        else:
            st.dataframe(
                meta[[c for c in (
                    "fecha", "id_escena", "sensor", "tier", "nube_aoi_pct",
                    "nubosidad_catalogo_pct", "cumple", "motivos"
                ) if c in meta.columns]],
                hide_index=True, width="stretch",
            )
            _descarga_landsat(
                carpeta / "metadatos_escenas.csv", "Descargar metadatos de escenas",
                f"landsat_meta_{slug}",
            )
        if inv["control"] and inv["control"].is_file():
            with st.expander("Registro original de control de escenas"):
                control = _leer_landsat_si_existe(inv["control"])
                if control is not None:
                    st.dataframe(control, hide_index=True, width="stretch")
            _descarga_landsat(
                inv["control"], "Descargar Control_escenas.csv",
                f"landsat_control_{slug}",
            )
        for compuesto in compuestos:
            ficha = compuesto["ficha"]
            with st.expander(f"Ficha del compuesto · {compuesto['datos'].get('periodo', ficha.stem)}"):
                d = compuesto["datos"]
                campos = {
                    "sede": "Territorio", "periodo": "Período", "temporadas": "Temporadas",
                    "ventana_meses": "Meses de comparación", "area_interes": "Área de interés",
                    "buffer_km": "Radio del buffer (km)", "crs": "Sistema de referencia",
                    "pixel_m": "Resolución (m)", "producto": "Fuente y producto",
                    "sensores": "Sensores", "escenas_consultadas": "Escenas consultadas",
                    "escenas_usadas": "Escenas utilizadas", "primera_fecha": "Primera observación",
                    "ultima_fecha": "Última observación", "aoi_sin_observacion_pct": "AOI sin observación (%)",
                    "publicable": "Aprobado para visualización", "criterio_publicacion": "Criterio de publicación",
                    "mascara": "Máscara de calidad", "metodo": "Método", "script": "Script de origen",
                }
                filas = []
                for clave, etiqueta in campos.items():
                    valor = d.get(clave)
                    if valor is None:
                        continue
                    if isinstance(valor, bool):
                        valor = "Sí" if valor else "No"
                    elif isinstance(valor, list):
                        valor = ", ".join(map(str, valor))
                    filas.append({"Parámetro": etiqueta, "Valor": str(valor)})
                st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
                _descarga_landsat(
                    ficha, "Descargar ficha JSON",
                    f"landsat_json_{slug}_{ficha.stem}",
                )
                escenas = ficha.with_name(ficha.name.replace("_compuesto.json", "_escenas.csv"))
                if escenas.is_file():
                    registro = _leer_landsat_si_existe(escenas)
                    if registro is not None and not registro.empty:
                        st.markdown("**Escenas consultadas para este compuesto**")
                        st.caption("La inclusión en el compuesto no significa aprobación como escena individual; son criterios distintos.")
                        st.dataframe(registro.rename(columns={
                            "id_escena": "ID de escena", "fecha": "Fecha", "sensor": "Sensor",
                            "path_row": "Path/row", "nubosidad_catalogo_pct": "Nubosidad catálogo (%)",
                            "aoi_cubierto_pct": "AOI cubierto (%)", "aoi_despejado_pct": "AOI despejado (%)",
                            "usada_en_compuesto": "Utilizada en compuesto",
                        }), hide_index=True, width="stretch")
                    _descarga_landsat(
                        escenas, "Descargar escenas del compuesto CSV",
                        f"landsat_escenascomp_{slug}_{escenas.stem}",
                    )
                for tipo, imagen in compuesto["imagenes"].items():
                    _descarga_landsat(
                        imagen, f"Descargar imagen {tipo.replace('_', ' ')}",
                        f"landsat_comp_img_{slug}_{imagen.stem}",
                    )
        st.warning(
            "Las animaciones históricas sin trazabilidad no se muestran. "
            "No se eliminan del disco ni de Git automáticamente."
        )


__all__ = [
    "CARPETA_LANDSAT", "COLORES_LANDSAT", "carpeta_landsat_sede",
    "inventario_landsat", "anio_gif_landsat", "leer_csv_landsat",
    "_leer_landsat_si_existe", "_tabla_areas_landsat",
    "preparar_gif_landsat_lento", "mostrar_landsat_territorio",
]
