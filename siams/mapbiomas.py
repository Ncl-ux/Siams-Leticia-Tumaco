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

from .utilidades import buscar_archivo_exacto, normalizar_etiqueta, resolver_carpeta_preferida, resolver_subcarpeta

CARPETA_COBERTURAS = resolver_carpeta_preferida("Coberturas_MapBiomas", "Coberturas MapBio")
CARPETA_CSV_MAPBIOMAS = resolver_carpeta_preferida("data/processed/mapbiomas", "Coberturas_MapBiomas")

COBERTURAS_POR_TERRITORIO = {
    "Arauca": {"carpeta": "Arauca", "zonas": {"A": "Arauca"}},
    "La Paz": {"carpeta": "La_Paz", "zonas": {"LP": "La Paz"}},
    "Leticia": {"carpeta": "Leticia", "zonas": {"L": "Leticia"}},
    "Medellín": {"carpeta": "Medellín", "zonas": {"M": "Medellín"}},
    "San Andrés": {
        "carpeta": "San_Andres",
        "zonas": {"SA": "San Andrés", "SAC": "San Andrés Costa"},
    },
    "Tumaco": {"carpeta": "Tumaco", "zonas": {"T": "Tumaco"}},
}

COLORES_COBERTURAS = {
    "Formación boscosa": "#208b47",
    "Formación natural no boscosa": "#bbce58",
    "Área agropecuaria": "#f0c86a",
    "Área sin vegetación": "#df4b51",
    "Cuerpo de agua": "#2b63e8",
}

def encontrar_csv_coberturas(nombre_territorio: str, codigo: str) -> dict:
    """Separa los archivos anual/serie y las siglas SA/SAC; acepta 'Copia de'."""
    config = COBERTURAS_POR_TERRITORIO.get(nombre_territorio)
    resultado = {"anual": [], "serie": []}
    if config is None or codigo not in config["zonas"]:
        return resultado
    carpeta = resolver_subcarpeta(CARPETA_CSV_MAPBIOMAS, config["carpeta"])
    if not carpeta.is_dir() or not any(carpeta.glob("*.csv")):
        carpeta = resolver_subcarpeta(CARPETA_COBERTURAS, config["carpeta"])
    if not carpeta.is_dir():
        return resultado
    for archivo in sorted(carpeta.iterdir(), key=lambda p: p.name.casefold()):
        if not archivo.is_file() or archivo.suffix.casefold() != ".csv":
            continue
        nombre = normalizar_etiqueta(archivo.stem)
        if nombre.split("_")[-1] != codigo.casefold() or "cobertura" not in nombre:
            continue
        tipo = "serie" if "serie_temporal" in nombre else "anual"
        resultado[tipo].append(archivo)
    return resultado

MAPBIOMAS_GIFS_POR_TERRITORIO = {
    "Arauca": {
        "Nivel 1": "mapbiomas_arauca_nivel_1.gif",
        "Nivel 2": "mapbiomas_arauca_nivel_2.gif",
        "Natural / antrópico": "mapbiomas_arauca_ant_nat.gif",
    },
    "La Paz": {
        "Nivel 1": "mapbiomas_la_paz_nivel_1.gif",
        "Nivel 2": "mapbiomas_la_paz_nivel_2.gif",
        "Natural / antrópico": "mapbiomas_la_paz_ant_nat.gif",
    },
    "Leticia": {
        "Nivel 1": "mapbiomas_leticia_nivel_1.gif",
        "Nivel 2": "mapbiomas_leticia_nivel_2.gif",
        "Natural / antrópico": "mapbiomas_leticia_ant_nat.gif",
    },
    "Medellín": {
        "Nivel 1": "mapbiomas_medellin_nivel_1.gif",
        "Nivel 2": "mapbiomas_medellin_nivel_2.gif",
        "Natural / antrópico": "mapbiomas_medellin_ant_nat.gif",
    },
    "San Andrés": {
        "Nivel 1": "mapbiomas_san_andres_nivel_1.gif",
        "Nivel 2": "mapbiomas_san_andres_nivel_2.gif",
        "Natural / antrópico": "mapbiomas_san_andres_ant_nat.gif",
    },
    "Tumaco": {
        "Nivel 1": "mapbiomas_tumaco_nivel_1.gif",
        "Nivel 2": "mapbiomas_tumaco_nivel_2.gif",
        "Natural / antrópico": "mapbiomas_tumaco_ant_nat.gif",
    },
}

MAPBIOMAS_GIFS_NOMBRES_ANTIGUOS = {'mapbiomas_arauca_nivel_1.gif': 'MapBiomas Gif Arauca.gif', 'mapbiomas_arauca_nivel_2.gif': 'MapBiomas Gif Arauca 2.gif', 'mapbiomas_arauca_ant_nat.gif': 'MapBiomas Gif Arauca AntNat.gif', 'mapbiomas_la_paz_nivel_1.gif': 'MapBiomas Gif La Paz.gif', 'mapbiomas_la_paz_nivel_2.gif': 'MapBiomas Gif La Paz 2.gif', 'mapbiomas_la_paz_ant_nat.gif': 'MapBiomas Gif La Paz AntNat.gif', 'mapbiomas_leticia_nivel_1.gif': 'MapBiomas Gif Leticia.gif', 'mapbiomas_leticia_nivel_2.gif': 'MapBiomas Gif Leticia 2.gif', 'mapbiomas_leticia_ant_nat.gif': 'MapBiomas Gif Leticia AntNat.gif', 'mapbiomas_medellin_nivel_1.gif': 'MapBiomas Gif Medellin.gif', 'mapbiomas_medellin_nivel_2.gif': 'MapBiomas Gif Medellin 2.gif', 'mapbiomas_medellin_ant_nat.gif': 'MapBiomas Gif Medellin AntNat.gif', 'mapbiomas_san_andres_nivel_1.gif': 'MapBiomas Gif San Andres.gif', 'mapbiomas_san_andres_nivel_2.gif': 'MapBiomas Gif San Andres 2.gif', 'mapbiomas_san_andres_ant_nat.gif': 'MapBiomas Gif San Andres AntNat.gif', 'mapbiomas_tumaco_nivel_1.gif': 'MapBiomas Gif Tumaco.gif', 'mapbiomas_tumaco_nivel_2.gif': 'MapBiomas Gif Tumaco 2.gif', 'mapbiomas_tumaco_ant_nat.gif': 'MapBiomas Gif Tumaco AntNat.gif'}

def buscar_gif_mapbiomas(nombre_territorio: str, nombre_archivo: str):
    """Busca GIF de nivel exacto de la sede, sin sustituir nivel 1, 2 o Ant/Nat."""
    config = COBERTURAS_POR_TERRITORIO.get(nombre_territorio)
    if config is None:
        return None
    carpeta = resolver_subcarpeta(CARPETA_COBERTURAS, config['carpeta'])
    return buscar_archivo_exacto(carpeta, nombre_archivo,
                                MAPBIOMAS_GIFS_NOMBRES_ANTIGUOS.get(nombre_archivo, ''))

def _mostrar_gif_mapbiomas(ruta: Path, titulo: str, descripcion: str) -> None:
    """Renderiza el GIF sin convertirlo para conservar la animación."""
    gif_b64 = base64.b64encode(ruta.read_bytes()).decode("ascii")
    st.markdown(
        f"""
        <div style="
            width:100%;
            display:flex;
            justify-content:center;
            align-items:center;
            margin:0.35rem 0 0.65rem 0;
        ">
            <img
                src="data:image/gif;base64,{gif_b64}"
                alt="{escape(str(titulo))}"
                style="
                    display:block;
                    width:auto;
                    height:auto;
                    max-width:100%;
                    border-radius:14px;
                    box-shadow:0 8px 22px rgba(0,0,0,0.10);
                "
            >
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(descripcion)

def mostrar_presentacion_cobertura_mapbiomas(nombre_territorio: str, tipo: str, zona: str) -> None:
    """Encabezado y GIF del apartado seleccionado, junto a su explicación.

    El GIF es territorial, mientras que la estadística proviene de la zona CSV.
    En San Andrés esto importa para no confundir la isla con San Andrés Costa.
    """
    detalles = {
        "Nivel 1": {
            "titulo": "🌳 Nivel 1 · Coberturas generales",
            "descripcion": (
                "Clasificación general de las coberturas de la tierra. "
                "La animación muestra los cambios espaciales y las estadísticas "
                "resumen la superficie por categoría."
            ),
            "explicacion": (
                "**Lectura:** identifica las grandes categorías de cobertura y compara "
                "su participación y evolución en el tiempo."
            ),
        },
        "Nivel 2": {
            "titulo": "🧩 Nivel 2 · Detalle de coberturas",
            "descripcion": (
                "Desagregación de las coberturas generales en subclases. "
                "Permite identificar cambios con mayor detalle temático."
            ),
            "explicacion": (
                "**Lectura:** las subclases se analizan por separado, sin volver a sumar "
                "los totales de Nivel 1."
            ),
        },
        "Natural / antrópico": {
            "titulo": "🌿 Natural / Antrópico",
            "descripcion": (
                "Síntesis de las coberturas naturales frente a las transformadas "
                "por actividades humanas. Se presenta una sola clasificación Ant/Nat."
            ),
            "explicacion": (
                "**Lectura:** compara la superficie natural y antrópica, su participación "
                "y sus cambios a lo largo de la serie histórica."
            ),
        },
    }
    cfg = detalles[tipo]
    st.markdown(f"### {cfg['titulo']}")
    st.caption(cfg["descripcion"])
    col_gif, col_texto = st.columns([1.65, 1.0])
    with col_gif:
        archivo = MAPBIOMAS_GIFS_POR_TERRITORIO.get(nombre_territorio, {}).get(tipo)
        ruta = buscar_gif_mapbiomas(nombre_territorio, archivo) if archivo else None
        if ruta is None:
            st.info(f"Animación {tipo} no encontrada para {nombre_territorio}.")
            if archivo:
                st.caption(f"Archivo esperado: Coberturas_MapBiomas/{COBERTURAS_POR_TERRITORIO[nombre_territorio]['carpeta']}/{archivo}")
        else:
            _mostrar_gif_mapbiomas(
                ruta,
                f"{nombre_territorio} · {tipo}",
                f"Animación MapBiomas · {tipo}",
            )
    with col_texto:
        st.markdown("#### Interpretación del mapa")
        st.markdown(cfg["explicacion"])
        st.markdown(f"**Zona estadística:** {zona}")
        st.caption("Fuente: MapBiomas · estadísticas y animación de coberturas.")
        if nombre_territorio == "San Andrés":
            st.caption(
                "El GIF representa San Andrés a escala territorial. Las estadísticas "
                "se consultan para SA (isla) o SAC (costa) por separado."
            )
    st.divider()

def buscar_csv_natural_antropico(nombre_territorio: str, codigo: str):
    """Localiza CSV Ant-Nat sin confundirlos con las series de Nivel 1/2."""
    cfg = COBERTURAS_POR_TERRITORIO.get(nombre_territorio)
    if not cfg or codigo not in cfg["zonas"]:
        return [], []
    carpeta = resolver_subcarpeta(CARPETA_CSV_MAPBIOMAS, cfg["carpeta"])
    if not carpeta.is_dir() or not any(carpeta.glob("*.csv")):
        carpeta = resolver_subcarpeta(CARPETA_COBERTURAS, cfg["carpeta"])
    if not carpeta.is_dir():
        return [], []

    candidatos = []
    for ruta in sorted(carpeta.iterdir(), key=lambda p: p.name.casefold()):
        if not ruta.is_file() or ruta.suffix.casefold() != ".csv":
            continue
        nombre = normalizar_etiqueta(ruta.stem)
        if (("ant_nat" in nombre or "nat_ant" in nombre)
                and "mapbiomas" in nombre):
            candidatos.append(ruta)

    # SA y SAC deben permanecer separados. No asignamos basándonos en
    # nombres ambiguos como «San Andrés y Providencia».
    if nombre_territorio != "San Andrés":
        return candidatos, []

    asignados = []
    ambiguos = []
    for ruta in candidatos:
        nombre = normalizar_etiqueta(ruta.stem)
        tokens = set(nombre.split("_"))
        es_costa = ("sac" in tokens or "costa" in tokens)
        es_isla = ("sa" in tokens or "isla" in tokens) and not es_costa
        if (codigo == "SAC" and es_costa) or (codigo == "SA" and es_isla):
            asignados.append(ruta)
        elif not es_costa and not es_isla:
            ambiguos.append(ruta)
    return asignados, ambiguos

def _tipo_natural_antropico(texto: str):
    """Reconoce etiquetas de las dos clases; no adivina códigos numéricos."""
    etiqueta = normalizar_etiqueta(texto)
    if not etiqueta:
        return None
    palabras = set(etiqueta.split("_"))
    if ("antropico" in palabras or "antropica" in palabras
            or "antropicos" in palabras or "antropicas" in palabras
            or "anthropic" in palabras or any(p.startswith("antrop") or p.startswith("antropiz") for p in palabras)):
        return "Antrópica"
    if (("natural" in palabras or "naturales" in palabras)
            and not ("no" in palabras or "semi" in palabras)):
        return "Natural"
    return None

def _numero_antnat(valor):
    """Acepta números, decimal con coma y miles + decimal mixtos."""
    if pd.isna(valor):
        return float("nan")
    if isinstance(valor, (int, float)):
        return float(valor)
    t = str(valor).strip().replace("\u00a0", "").replace(" ", "")
    t = t.replace("%", "")
    if not t or t in {"-", "—", "NA", "N/A"}:
        return float("nan")
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return float("nan")

@st.cache_data(show_spinner=False)
def cargar_csv_natural_antropico(ruta_texto: str, marca_archivo: int = 0):
    """Admite dos clases por filas, por columnas o en formato año-clase-área.

    Devuelve datos largos normalizados [Año, Clase, Valor] y metadatos de
    unidad. Las estadísticas descargadas de MapBiomas se presentan en hectáreas
    cuando el CSV no señala expresamente otra unidad.
    """
    ruta = Path(ruta_texto)
    errores = []
    tabla = None
    for codificacion in ("utf-8-sig", "cp1252"):
        try:
            tabla = pd.read_csv(ruta, sep=None, engine="python", encoding=codificacion)
            break
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
            errores.append(str(exc))
    if tabla is None:
        raise ValueError("No se pudo interpretar el CSV. " + "; ".join(errores[-2:]))

    tabla.columns = [str(c).strip().replace("\ufeff", "") for c in tabla.columns]
    tabla = tabla.loc[:, [not normalizar_etiqueta(c).startswith("unnamed") for c in tabla.columns]]
    tabla = tabla.dropna(how="all")
    if tabla.empty:
        raise ValueError("El archivo CSV está vacío.")

    columnas = list(tabla.columns)
    columnas_norm = {c: normalizar_etiqueta(c) for c in columnas}
    anios_col = [c for c in columnas if str(c).strip().isdigit()
                 and len(str(c).strip()) == 4 and 1900 <= int(str(c).strip()) <= 2100]
    unit = "ha"  # Estadísticas de área de la plataforma MapBiomas Colombia.
    cabecera = " ".join(columnas_norm.values())
    if any(k in cabecera for k in ("porcentaje", "percent", "participacion", "pct")) or "%" in " ".join(columnas):
        unit = "%"
    elif any(k in cabecera for k in ("hectarea", "area_ha", "superficie_ha", "_ha")):
        unit = "ha"
    elif "km2" in cabecera or "km_2" in cabecera:
        unit = "km²"

    # Formato nativo MapBiomas Ant-Nat: Level 1 / Level 2 / 1985 ... 2024.
    # Los registros Level 2 vacíos SON TOTALES: no se pueden sumar a sus hijas.
    nombres = {normalizar_etiqueta(c): c for c in columnas}
    col_n1 = next((nombres[k] for k in ("level_1", "nivel_1") if k in nombres), None)
    col_n2 = next((nombres[k] for k in ("level_2", "nivel_2") if k in nombres), None)
    if col_n1 is not None and col_n2 is not None and anios_col:
        t = tabla.copy()
        t["_grupo"] = t[col_n1].map(_tipo_natural_antropico)
        t["_subclase"] = t[col_n2].fillna("").astype(str).str.strip()
        for columna_anio in anios_col:
            t[columna_anio] = t[columna_anio].map(_numero_antnat)
            if t[columna_anio].isna().any() or (t[columna_anio] < 0).any():
                raise ValueError(f"Datos faltantes o negativos en el año {columna_anio}.")

        padres = t[t["_subclase"].eq("") & t["_grupo"].notna()].copy()
        hijas = t[t["_subclase"].ne("") & t["_grupo"].notna()].copy()
        if not {"Natural", "Antrópica"}.issubset(set(padres["_grupo"])):
            raise ValueError("Faltan las filas totales Natural / Anthropic (Level 2 vacío).")
        if padres["_grupo"].duplicated().any():
            raise ValueError("Hay totales repetidos para Natural o Anthropic.")

        datos = padres.melt(id_vars=["_grupo"], value_vars=anios_col,
                            var_name="Año", value_name="Valor")
        datos = datos.rename(columns={"_grupo": "Clase"})
        datos["Año"] = datos["Año"].astype(int)
        datos = datos[["Año", "Clase", "Valor"]].sort_values(["Año", "Clase"]).reset_index(drop=True)

        if not hijas.empty:
            detalle = hijas.melt(id_vars=["_grupo", "_subclase"], value_vars=anios_col,
                                var_name="Año", value_name="Valor")
            detalle = detalle.rename(columns={"_grupo": "Nivel 1", "_subclase": "Nivel 2"})
            detalle["Año"] = detalle["Año"].astype(int)
            detalle["Clase"] = detalle["Nivel 2"] + " · " + detalle["Nivel 1"]
            detalle = detalle[["Año", "Clase", "Nivel 1", "Nivel 2", "Valor"]]
            detalle = (detalle.groupby(["Año", "Clase", "Nivel 1", "Nivel 2"], as_index=False)["Valor"]
                       .sum().sort_values(["Año", "Nivel 1", "Nivel 2"]).reset_index(drop=True))
        else:
            detalle = pd.DataFrame(columns=["Año", "Clase", "Nivel 1", "Nivel 2", "Valor"])

        discrepancias = []
        if not detalle.empty:
            comprobacion = detalle.groupby(["Año", "Nivel 1"])["Valor"].sum()
            for fila in datos.itertuples(index=False):
                subtotal = comprobacion.get((fila.Año, fila.Clase), float("nan"))
                if not math.isfinite(subtotal) or not math.isclose(
                    float(fila.Valor), float(subtotal), abs_tol=1e-5, rel_tol=1e-8
                ):
                    discrepancias.append(f"{fila.Clase} {fila.Año}")

        no_def = t[t["_subclase"].eq("") & t["_grupo"].isna() &
                   t[col_n1].astype(str).map(normalizar_etiqueta).isin({"not_defined", "no_definido", "sin_clasificar"})]
        sin_clasificar = {}
        if not no_def.empty:
            sin_clasificar = {int(a): float(no_def[a].sum()) for a in anios_col}

        return datos, {
            "unidad": unit, "archivo": ruta.name,
            "detalle_nivel_2": detalle,
            "discrepancias": discrepancias,
            "sin_clasificar": sin_clasificar,
        }

    categoria = None
    if anios_col:
        # Disposición ancha: Tipo | 1985 | 1986 ...
        otras = [c for c in columnas if c not in anios_col]
        if otras:
            puntajes = {c: tabla[c].map(_tipo_natural_antropico).notna().sum() for c in otras}
            categoria = max(puntajes, key=puntajes.get)
            if puntajes[categoria] == 0:
                categoria = None
        if categoria is None:
            raise ValueError("Se encontraron columnas de años, pero no filas identificables como Natural y Antrópica.")
        datos = tabla.melt(id_vars=[categoria], value_vars=anios_col, var_name="Año", value_name="Valor")
        datos["Clase"] = datos[categoria].map(_tipo_natural_antropico)
        datos = datos[["Año", "Clase", "Valor"]]
    else:
        # Disposición larga: Año | Categoría | Área, o Año | Natural | Antrópica.
        posibles_anio = [c for c in columnas if columnas_norm[c] in
                         {"ano", "anio", "year", "periodo", "fecha", "years"}]
        if not posibles_anio:
            raise ValueError("No se encontraron años: utiliza columnas 1985, 1986... o una columna Año/Year.")
        col_anio = posibles_anio[0]
        col_clases = {c: _tipo_natural_antropico(c) for c in columnas if c != col_anio}
        ancha = {c: k for c, k in col_clases.items() if k is not None}
        if {"Natural", "Antrópica"}.issubset(set(ancha.values())):
            cols = [c for c in ancha if ancha[c] in {"Natural", "Antrópica"}]
            datos = tabla.melt(id_vars=[col_anio], value_vars=cols, var_name="Tipo", value_name="Valor")
            datos["Clase"] = datos["Tipo"].map(ancha)
            datos = datos.rename(columns={col_anio: "Año"})[["Año", "Clase", "Valor"]]
        else:
            columnas_cat = [c for c in columnas if c != col_anio]
            puntos = {c: tabla[c].map(_tipo_natural_antropico).notna().sum() for c in columnas_cat}
            categoria = max(puntos, key=puntos.get) if puntos else None
            if categoria is None or puntos[categoria] == 0:
                raise ValueError("No se identificaron las categorías Natural y Antrópica en el CSV.")
            candidatas = [c for c in columnas if c not in {col_anio, categoria}]
            if not candidatas:
                raise ValueError("Falta una columna con el área o valor de cada categoría.")
            # Prioriza la columna de área/valor; ignora otras columnas de atributos.
            preferencias = ("area", "superficie", "valor", "hectarea", "ha", "porcentaje", "participacion", "percent", "pct")
            candidatas.sort(key=lambda c: (not any(k in columnas_norm[c] for k in preferencias), columnas.index(c)))
            col_valor = candidatas[0]
            if unit is None:
                if "ha" in columnas_norm[col_valor].split("_") or "hectarea" in columnas_norm[col_valor]:
                    unit = "ha"
                elif "porcentaje" in columnas_norm[col_valor] or "pct" in columnas_norm[col_valor]:
                    unit = "%"
            datos = tabla[[col_anio, categoria, col_valor]].copy()
            datos.columns = ["Año", "Categoría", "Valor"]
            datos["Clase"] = datos["Categoría"].map(_tipo_natural_antropico)
            datos = datos[["Año", "Clase", "Valor"]]

    datos["Año"] = pd.to_numeric(datos["Año"], errors="coerce")
    datos["Valor"] = datos["Valor"].map(_numero_antnat)
    datos = datos.dropna(subset=["Año", "Clase", "Valor"])
    datos = datos[datos["Año"].between(1900, 2100) & (datos["Valor"] >= 0)].copy()
    if datos.empty:
        raise ValueError("No hay filas con año, categoría y valor numérico válidos.")
    datos["Año"] = datos["Año"].astype(int)
    datos = (datos.groupby(["Año", "Clase"], as_index=False)["Valor"]
             .sum().sort_values(["Año", "Clase"]).reset_index(drop=True))
    if set(datos["Clase"]) != {"Natural", "Antrópica"}:
        raise ValueError("Se necesita al menos un registro para Natural y otro para Antrópica.")
    return datos, {"unidad": unit, "archivo": ruta.name}

def mostrar_analisis_natural_antropico(nombre_territorio: str, codigo: str) -> None:
    """Una sola lectura Natural/Antrópica, sin duplicar por Nivel 1 y Nivel 2.

    Las exportaciones nativas de MapBiomas incluyen subtotales y desglose por
    subclase. Para esta sección, usamos SOLO los totales naturales y antrópicos
    del archivo Ant-Nat, de modo que cada área se contabiliza una única vez.
    """
    zona = COBERTURAS_POR_TERRITORIO[nombre_territorio]["zonas"][codigo]
    clave = f"antnat_{normalizar_etiqueta(nombre_territorio)}_{codigo}"
    asignados, ambiguos = buscar_csv_natural_antropico(nombre_territorio, codigo)
    rutas = asignados + ambiguos

    mostrar_presentacion_cobertura_mapbiomas(nombre_territorio, "Natural / antrópico", zona)
    st.markdown("#### Estadísticas de cobertura natural y antrópica")

    if not rutas:
        st.info(
            f"No se encontró un CSV MapBiomas Ant-Nat para {zona} dentro de "
            f"Coberturas_MapBiomas/{COBERTURAS_POR_TERRITORIO[nombre_territorio]['carpeta']}."
        )
        return

    # San Andrés isla y San Andrés Costa deben permanecer diferenciados.
    if len(rutas) == 1 and nombre_territorio != "San Andrés":
        ruta = rutas[0]
    elif len(asignados) == 1:
        ruta = asignados[0]
    else:
        st.warning(
            "Elige qué CSV corresponde a esta zona. Puedes añadir SA (isla) "
            "o SAC (costa) al nombre para identificarlo automáticamente."
            if nombre_territorio == "San Andrés"
            else "Se encontraron varios CSV Ant-Nat: selecciona el correcto."
        )
        nombres = [r.name for r in rutas]
        elegido = st.selectbox(
            f"CSV Ant-Nat de {zona}", ["Seleccionar archivo..."] + nombres,
            key=f"{clave}_elegir_csv",
        )
        if elegido == "Seleccionar archivo...":
            return
        ruta = next(r for r in rutas if r.name == elegido)

    try:
        datos, metadatos = cargar_csv_natural_antropico(str(ruta), ruta.stat().st_mtime_ns)
    except Exception as error:
        st.error(f"No se pudo interpretar `{ruta.name}`: {error}")
        return

    unidad = metadatos.get("unidad", "ha")
    etiqueta_superficie = f"Superficie ({unidad})" if unidad in {"ha", "km²"} else "Cobertura (%)"
    if metadatos.get("discrepancias"):
        st.warning(
            "Los subtotales del CSV presentan diferencias respecto a los totales en: "
            + ", ".join(metadatos["discrepancias"][:6])
            + ". Se utilizan los totales originales sin sumarlos de nuevo."
        )

    pivot = datos.pivot(index="Año", columns="Clase", values="Valor").sort_index()
    completos = pivot.dropna(subset=["Natural", "Antrópica"]).copy()
    if completos.empty:
        st.info("No hay años que tengan simultáneamente superficies naturales y antrópicas.")
        st.dataframe(datos, hide_index=True, use_container_width=True)
        return

    completos["Total"] = completos["Natural"] + completos["Antrópica"]
    completos["Natural (%)"] = 100 * completos["Natural"] / completos["Total"].where(completos["Total"].ne(0))
    completos["Antrópica (%)"] = 100 * completos["Antrópica"] / completos["Total"].where(completos["Total"].ne(0))
    anios = completos.index.to_list()
    anio = st.selectbox(
        "Año de consulta · Natural/Antrópica", anios, index=len(anios) - 1,
        key=f"{clave}_anio",
    )
    fila = completos.loc[anio]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Superficie natural", f"{fila['Natural']:,.2f} {unidad}")
    c2.metric("Superficie antrópica", f"{fila['Antrópica']:,.2f} {unidad}")
    c3.metric("Participación natural", f"{fila['Natural (%)']:.1f} %" if pd.notna(fila["Natural (%)"]) else "—")
    c4.metric("Periodo disponible", f"{anios[0]}–{anios[-1]}")

    sin_clasificar = metadatos.get("sin_clasificar", {})
    if sin_clasificar.get(int(anio), 0) > 0:
        st.caption(
            f"Superficie no clasificada en {anio}: {sin_clasificar[int(anio)]:,.2f} {unidad}; "
            "no se incluye en los porcentajes de Natural y Antrópica."
        )

    t_dist, t_evol, t_comp, t_datos = st.tabs([
        "Distribución anual", "Evolución histórica", "Cambios entre años", "Datos y descargas",
    ])
    colores = {"Natural": "#208b47", "Antrópica": "#df9454"}

    with t_dist:
        actual = pd.DataFrame({
            "Clase": ["Natural", "Antrópica"],
            "Valor": [fila["Natural"], fila["Antrópica"]],
            "Participación (%)": [fila["Natural (%)"], fila["Antrópica (%)"]],
        })
        visibles = actual.loc[actual["Valor"] > 0]
        if not visibles.empty:
            fig = px.pie(
                visibles, names="Clase", values="Valor", color="Clase", hole=0.56,
                color_discrete_map=colores,
                title=f"Cobertura natural y antrópica · {zona} · {anio}",
            )
            fig.update_traces(
                textinfo="percent",
                hovertemplate="%{label}<br>Superficie: %{value:,.2f}<br>%{percent}<extra></extra>",
            )
            fig.update_layout(height=480, margin=dict(l=10, r=10, t=60, b=20))
            st.plotly_chart(fig, use_container_width=True, key=f"{clave}_distribucion")
        else:
            st.info("No se reportan superficies naturales ni antrópicas para el año elegido.")
        st.dataframe(
            actual.rename(columns={"Valor": etiqueta_superficie}).round(2),
            hide_index=True, use_container_width=True,
        )

    with t_evol:
        modo = st.radio(
            "Visualizar", [etiqueta_superficie, "Participación (%)"],
            horizontal=True, key=f"{clave}_modo",
        )
        if modo == etiqueta_superficie:
            largo = completos.reset_index().melt(
                id_vars="Año", value_vars=["Natural", "Antrópica"],
                var_name="Clase", value_name="Valor",
            )
            fig = px.area(
                largo, x="Año", y="Valor", color="Clase", color_discrete_map=colores,
                title=f"Evolución de superficies · {zona}",
            )
            fig.update_yaxes(title=etiqueta_superficie)
        else:
            largo = completos.reset_index().melt(
                id_vars="Año", value_vars=["Natural (%)", "Antrópica (%)"],
                var_name="Clase", value_name="Participación (%)",
            )
            largo["Clase"] = largo["Clase"].str.replace(" (%)", "", regex=False)
            fig = px.line(
                largo, x="Año", y="Participación (%)", color="Clase", markers=True,
                color_discrete_map=colores, title=f"Participación histórica · {zona}",
            )
            fig.update_yaxes(range=[0, 100])
        fig.update_xaxes(range=[anios[0], anios[-1]], rangeslider_visible=True)
        fig.update_layout(height=490, hovermode="x unified", margin=dict(l=15, r=15, t=60, b=15))
        st.plotly_chart(fig, use_container_width=True, key=f"{clave}_evolucion")

    with t_comp:
        c_ini, c_fin = st.columns(2)
        with c_ini:
            inicio = st.selectbox("Año inicial", anios, index=0, key=f"{clave}_inicio")
        with c_fin:
            fin = st.selectbox("Año final", anios, index=len(anios) - 1, key=f"{clave}_fin")
        if inicio > fin:
            st.warning("Selecciona un año final igual o posterior al inicial.")
        else:
            comparacion = pd.DataFrame({
                "Clase": ["Natural", "Antrópica"],
                f"Superficie inicial ({inicio})": completos.loc[inicio, ["Natural", "Antrópica"]].to_numpy(),
                f"Superficie final ({fin})": completos.loc[fin, ["Natural", "Antrópica"]].to_numpy(),
                "Participación inicial (%)": completos.loc[inicio, ["Natural (%)", "Antrópica (%)"]].to_numpy(),
                "Participación final (%)": completos.loc[fin, ["Natural (%)", "Antrópica (%)"]].to_numpy(),
            })
            col_ini = f"Superficie inicial ({inicio})"
            col_fin = f"Superficie final ({fin})"
            comparacion[f"Variación ({unidad})"] = comparacion[col_fin] - comparacion[col_ini]
            comparacion["Variación (puntos porcentuales)"] = (
                comparacion["Participación final (%)"] - comparacion["Participación inicial (%)"]
            )
            comparacion["Cambio relativo (%)"] = 100 * (
                comparacion[f"Variación ({unidad})"] /
                comparacion[col_ini].replace(0, float("nan"))
            )
            st.dataframe(comparacion.round(2), hide_index=True, use_container_width=True)
            fig = px.bar(
                comparacion, x="Clase", y=f"Variación ({unidad})", color="Clase",
                color_discrete_map=colores, title=f"Cambio de superficie · {inicio}–{fin}",
            )
            fig.update_layout(height=420, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key=f"{clave}_comparacion")
            st.caption(
                "La variación neta entre años no identifica directamente qué clases "
                "se transformaron: para eso se requiere una matriz de transiciones."
            )
            st.download_button(
                "Descargar comparación CSV",
                data=comparacion.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"MapBiomas_AntNat_Cambios_{codigo}_{inicio}_{fin}.csv",
                mime="text/csv", key=f"{clave}_desc_comparacion",
            )

    with t_datos:
        st.write(f"**Archivo fuente:** `{ruta.name}`")
        st.dataframe(
            datos.rename(columns={"Valor": etiqueta_superficie}),
            hide_index=True, use_container_width=True,
        )
        st.download_button(
            "Descargar serie Natural/Antrópica",
            data=datos.rename(columns={"Valor": etiqueta_superficie}).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"MapBiomas_AntNat_Serie_{codigo}.csv",
            mime="text/csv", key=f"{clave}_desc_serie",
        )
        st.download_button(
            "Descargar CSV original",
            data=ruta.read_bytes(), file_name=ruta.name,
            mime="text/csv", key=f"{clave}_desc_fuente",
        )
        st.caption("Se usan los totales por categoría del archivo sin sumar dos veces las subclases.")

@st.cache_data(show_spinner=False)
def cargar_csv_cobertura(ruta_texto: str, marca_archivo: int = 0) -> pd.DataFrame:
    """Valida los CSV exportados. marca_archivo invalida la caché al editar el CSV."""
    try:
        df = pd.read_csv(ruta_texto, encoding="utf-8-sig", sep=None, engine="python")
    except UnicodeDecodeError:
        df = pd.read_csv(ruta_texto, encoding="cp1252", sep=None, engine="python")
    df.columns = [str(columna).strip() for columna in df.columns]
    if df.columns.duplicated().any():
        raise ValueError("El CSV tiene columnas repetidas.")
    equivalencias = {normalizar_etiqueta(c): c for c in df.columns}
    if not {"nivel_1", "nivel_2"}.issubset(equivalencias):
        raise ValueError("El CSV debe contener las columnas Nivel 1 y Nivel 2.")
    df = df.rename(columns={equivalencias["nivel_1"]: "Nivel 1", equivalencias["nivel_2"]: "Nivel 2"})
    anios = sorted(c for c in df.columns if len(c) == 4 and c.isdigit())
    if not anios:
        raise ValueError("No se encontraron columnas de años en el CSV.")
    df = df[["Nivel 1", "Nivel 2", *anios]].copy()
    for columna in ("Nivel 1", "Nivel 2"):
        df[columna] = df[columna].fillna("").astype(str).str.strip()
    df = df.loc[df["Nivel 1"].ne("")].copy()
    if df.empty:
        raise ValueError("El CSV no contiene clases de cobertura.")
    if df.duplicated(["Nivel 1", "Nivel 2"]).any():
        raise ValueError("Hay clases repetidas en el CSV; revisa la exportación.")
    for anio in anios:
        df[anio] = pd.to_numeric(df[anio], errors="coerce")
        if df[anio].isna().any() or (df[anio] < 0).any() or not df[anio].map(math.isfinite).all():
            raise ValueError(f"La columna {anio} contiene áreas faltantes, negativas o no numéricas.")
    return df.reset_index(drop=True)

def preparar_cobertura_nivel(df: pd.DataFrame, nivel: str) -> pd.DataFrame:
    """Usa totales de Nivel 1 o subclases de Nivel 2, evitando doble conteo."""
    anios = [c for c in df.columns if len(c) == 4 and c.isdigit()]
    padres = df["Nivel 2"].eq("")
    if nivel == "Nivel 1":
        datos = df.loc[padres].copy()
        if datos.empty:
            datos = df.groupby("Nivel 1", as_index=False)[anios].sum()
        datos["Clase"] = datos["Nivel 1"]
    else:
        datos = df.loc[~padres].copy()
        if datos.empty:
            raise ValueError("Este CSV no contiene subclases de Nivel 2.")
        datos["Clase"] = datos["Nivel 2"]
        repetidas = datos["Clase"].duplicated(keep=False)
        datos.loc[repetidas, "Clase"] = datos.loc[repetidas, "Nivel 2"] + " · " + datos.loc[repetidas, "Nivel 1"]
    return datos[["Clase", "Nivel 1", *anios]].reset_index(drop=True)

def comparar_coberturas(datos: pd.DataFrame, inicial: int, final: int) -> pd.DataFrame:
    """El porcentaje es relativo al área inicial; crecimiento desde cero queda sin % definido."""
    if inicial > final:
        raise ValueError("El año final debe ser igual o posterior al inicial.")
    cambio = datos[["Clase", str(inicial), str(final)]].copy() if inicial != final else datos[["Clase", str(inicial)]].copy()
    cambio = cambio.rename(columns={str(inicial): "Área inicial (ha)"})
    if inicial == final:
        cambio["Área final (ha)"] = cambio["Área inicial (ha)"]
    else:
        cambio = cambio.rename(columns={str(final): "Área final (ha)"})
    cambio["Cambio (ha)"] = cambio["Área final (ha)"] - cambio["Área inicial (ha)"]
    denominador = cambio["Área inicial (ha)"].where(cambio["Área inicial (ha)"].ne(0))
    cambio["Cambio (%)"] = 100 * cambio["Cambio (ha)"] / denominador
    ambas_cero = cambio["Área inicial (ha)"].eq(0) & cambio["Área final (ha)"].eq(0)
    cambio.loc[ambas_cero, "Cambio (%)"] = 0.0
    return cambio

def mostrar_resumen_coberturas(anio, total, dominante, primer_anio, ultimo_anio) -> None:
    """Tarjetas con texto ajustable, sin depender del ancho de st.metric."""
    tarjetas = [
        (f"Superficie clasificada · {anio}", f"{total:,.1f} ha", "numero"),
        ("Clase dominante", dominante["Clase"] if total else "Sin superficie", "texto"),
        ("Participación dominante", f"{dominante['Participación (%)']:.1f} %" if total else "—", "numero"),
        ("Periodo disponible", f"{primer_anio}–{ultimo_anio}", "numero"),
    ]
    estilo = """<style>
    .cobertura-resumen {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        width: 100%;
        min-width: 0;
        margin: 0.75rem 0 1.25rem;
        align-items: stretch;
    }
    .cobertura-resumen-tarjeta {
        box-sizing: border-box;
        min-width: 0;
        max-width: 100%;
        min-height: 106px;
        padding: 1rem 1.15rem;
        border: 1px solid var(--siams-borde, rgba(128,128,128,0.28));
        border-radius: 16px;
        background: var(--secondary-background-color);
        color: var(--text-color);
        box-shadow: var(--siams-sombra, 0 6px 18px rgba(0,0,0,0.08));
    }
    .cobertura-resumen-etiqueta,
    .cobertura-resumen-valor {
        display: block;
        box-sizing: border-box;
        width: 100%;
        min-width: 0;
        max-width: 100%;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: normal !important;
        color: var(--text-color) !important;
    }
    .cobertura-resumen-etiqueta {
        font-size: 0.86rem;
        line-height: 1.35;
        margin-bottom: 0.55rem;
        opacity: 0.82;
    }
    .cobertura-resumen-valor {
        font-size: clamp(1.15rem, 1.6vw, 1.45rem);
        line-height: 1.3;
        font-weight: 650;
    }
    .cobertura-resumen-valor.texto {
        font-size: 1.08rem;
        line-height: 1.45;
    }
    </style>"""
    contenido = "".join(
        '<div class="cobertura-resumen-tarjeta">'
        f'<div class="cobertura-resumen-etiqueta">{escape(str(etiqueta))}</div>'
        f'<div class="cobertura-resumen-valor {tipo}">{escape(str(valor))}</div>'
        '</div>'
        for etiqueta, valor, tipo in tarjetas
    )
    st.markdown(estilo + '<div class="cobertura-resumen">' + contenido + '</div>', unsafe_allow_html=True)

def mostrar_analisis_coberturas_nivel(nombre_territorio: str, codigo: str, nivel: str) -> None:
    """Muestra el GIF y las estadísticas del nivel dentro de su propia pestaña."""
    config = COBERTURAS_POR_TERRITORIO[nombre_territorio]
    zona = config["zonas"][codigo]
    clave = f"cob_{normalizar_etiqueta(nombre_territorio)}_{codigo}_{normalizar_etiqueta(nivel)}"

    mostrar_presentacion_cobertura_mapbiomas(nombre_territorio, nivel, zona)

    archivos = encontrar_csv_coberturas(nombre_territorio, codigo)
    if any(len(rutas) > 1 for rutas in archivos.values()):
        st.warning(
            "Hay más de un CSV del mismo tipo para esta zona. "
            "Conserva una exportación anual y una serie temporal por zona."
        )
        for tipo, rutas in archivos.items():
            if len(rutas) > 1:
                st.caption(f"Archivos de {tipo}: " + ", ".join(r.name for r in rutas))
        return
    if not archivos["serie"]:
        st.info(
            f"Todavía no se encontró la serie temporal de coberturas generales "
            f"para {zona}."
        )
        st.caption(f"Ubicación: Coberturas_MapBiomas/{config['carpeta']} · CSV que termina en {codigo}.")
        return
    ruta_serie = archivos["serie"][0]
    ruta_anual = archivos["anual"][0] if archivos["anual"] else None
    try:
        historico = cargar_csv_cobertura(str(ruta_serie), ruta_serie.stat().st_mtime_ns)
        anual = cargar_csv_cobertura(str(ruta_anual), ruta_anual.stat().st_mtime_ns) if ruta_anual else None
    except Exception as error:
        st.error(f"No se pudieron leer las coberturas generales de {zona}: {error}")
        return

    anios = sorted(int(c) for c in historico.columns if len(c) == 4 and c.isdigit())
    if anual is not None:
        comunes = [str(a) for a in anios if str(a) in anual.columns]
        for anio in comunes:
            comprobacion = historico[["Nivel 1", "Nivel 2", anio]].merge(
                anual[["Nivel 1", "Nivel 2", anio]], on=["Nivel 1", "Nivel 2"], how="outer", suffixes=("_serie", "_anual"), indicator=True,
            )
            dif = (comprobacion[f"{anio}_serie"] - comprobacion[f"{anio}_anual"]).abs()
            tolerancia = 1e-5 + 1e-8 * comprobacion[f"{anio}_serie"].abs()
            if comprobacion["_merge"].ne("both").any() or (dif > tolerancia).any():
                st.warning(f"El CSV anual y la serie no coinciden en {anio}. La distribución usa el CSV anual; las tendencias y cambios usan la serie. Revisa que ambos correspondan al mismo recorte.")
    st.markdown(f"#### Estadísticas · {nivel}")
    st.caption(f"Exportaciones MapBiomas aportadas al proyecto · {anios[0]}–{anios[-1]} · superficie en hectáreas (ha).")
    st.caption("Los CSV contienen áreas por clase; la zona analizada corresponde al recorte de la descarga y puede ser mayor que el campus. No contienen geometría para dibujar un mapa.")
    anio = st.selectbox("Año de distribución", anios, index=len(anios) - 1, key=f"{clave}_anio")
    try:
        datos = preparar_cobertura_nivel(historico, nivel)
        fuente_anual = anual if anual is not None and str(anio) in anual.columns else historico
        distribucion = preparar_cobertura_nivel(fuente_anual, nivel)[["Clase", "Nivel 1", str(anio)]].rename(columns={str(anio): "Área (ha)"})
    except ValueError as error:
        st.error(str(error))
        return
    total = distribucion["Área (ha)"].sum()
    distribucion["Participación (%)"] = 100 * distribucion["Área (ha)"] / total if total else 0.0
    dominante = distribucion.loc[distribucion["Área (ha)"].idxmax()]
    mostrar_resumen_coberturas(anio, total, dominante, anios[0], anios[-1])
    if nivel == "Nivel 2":
        colores = {fila["Clase"]: COLORES_COBERTURAS.get(fila["Nivel 1"], "#78909c") for _, fila in datos.iterrows()}
    else:
        colores = COLORES_COBERTURAS
    t_anual, t_serie, t_cambio, t_datos = st.tabs(["Distribución anual", "Evolución histórica", "Cambios entre años", "Datos y descargas"])
    with t_anual:
        visibles = distribucion[distribucion["Área (ha)"] > 0]
        if visibles.empty:
            st.info("No hay superficie clasificada para este año.")
        else:
            fig = px.pie(visibles, names="Clase", values="Área (ha)", hole=0.55, color="Clase", color_discrete_map=colores, hover_data=["Participación (%)"], title=f"Distribución de coberturas · {zona} · {anio}")
            fig.update_traces(textinfo="percent", hovertemplate="%{label}<br>Área: %{value:,.2f} ha<br>Participación: %{percent}<extra></extra>")
            fig.update_layout(height=520, margin=dict(l=20, r=20, t=60, b=30))
            st.plotly_chart(fig, use_container_width=True, key=f"{clave}_dona")
        st.dataframe(distribucion.sort_values("Área (ha)", ascending=False).round(2), hide_index=True, use_container_width=True)
    with t_serie:
        activas = datos.loc[datos[[str(a) for a in anios]].sum(axis=1) > 0, "Clase"].tolist()
        seleccion = st.multiselect("Clases que se muestran", activas, default=activas, key=f"{clave}_clases")
        modo = st.radio("Unidad del gráfico", ["Superficie (ha)", "Participación (%)"], horizontal=True, key=f"{clave}_unidad")
        largo = datos.melt(id_vars=["Clase", "Nivel 1"], var_name="Año", value_name="Área (ha)")
        largo["Año"] = largo["Año"].astype(int)
        totales = largo.groupby("Año")["Área (ha)"].transform("sum")
        largo["Participación (%)"] = 100 * largo["Área (ha)"] / totales.where(totales.ne(0))
        largo.loc[totales.eq(0), "Participación (%)"] = 0.0
        largo = largo[largo["Clase"].isin(seleccion)].sort_values("Año")
        if not seleccion:
            st.info("Selecciona al menos una clase para ver la evolución.")
        else:
            eje = "Área (ha)" if modo == "Superficie (ha)" else "Participación (%)"
            fig = px.area(largo, x="Año", y=eje, color="Clase", color_discrete_map=colores, title=f"Evolución de coberturas · {zona}")
            fig.update_layout(height=520, hovermode="x unified", margin=dict(l=20, r=20, t=60, b=30))
            fig.update_xaxes(range=[anios[0], anios[-1]], dtick=5 if len(anios) > 15 else 1, rangeslider_visible=True)
            st.plotly_chart(fig, use_container_width=True, key=f"{clave}_serie")
            if modo == "Participación (%)":
                st.caption("El porcentaje se calcula respecto a todas las clases del año. Ocultar una clase no recalcula el denominador.")
    with t_cambio:
        c1, c2 = st.columns(2)
        with c1:
            inicial = st.selectbox("Año inicial", anios, index=0, key=f"{clave}_inicio")
        with c2:
            final = st.selectbox("Año final", anios, index=len(anios) - 1, key=f"{clave}_fin")
        if inicial > final:
            st.warning("Elige un año final igual o posterior al año inicial.")
        else:
            cambio = comparar_coberturas(datos, inicial, final)
            cambio["Periodo"] = f"{inicial}–{final}"
            st.dataframe(cambio.round(2), hide_index=True, use_container_width=True)
            barras = cambio[(cambio["Área inicial (ha)"] > 0) | (cambio["Área final (ha)"] > 0)].sort_values("Cambio (ha)")
            if not barras.empty:
                fig = px.bar(barras, x="Cambio (ha)", y="Clase", orientation="h", color="Clase", color_discrete_map=colores, title=f"Cambio neto de superficie · {inicial}–{final}")
                fig.update_layout(height=max(360, 32 * len(barras)), showlegend=False, margin=dict(l=20, r=20, t=60, b=30))
                fig.add_vline(x=0, line_color="#78909c", line_width=1)
                st.plotly_chart(fig, use_container_width=True, key=f"{clave}_cambio")
            if (cambio["Cambio (ha)"].abs() > 1e-6).any():
                aumento = cambio.loc[cambio["Cambio (ha)"].idxmax()]
                perdida = cambio.loc[cambio["Cambio (ha)"].idxmin()]
                frases = []
                if aumento["Cambio (ha)"] > 0:
                    frases.append(f"El mayor aumento corresponde a {aumento['Clase']}: {aumento['Cambio (ha)']:,.1f} ha.")
                if perdida["Cambio (ha)"] < 0:
                    frases.append(f"La mayor disminución corresponde a {perdida['Clase']}: {abs(perdida['Cambio (ha)']):,.1f} ha.")
                st.info(f"Entre {inicial} y {final}, " + " ".join(frases))
            else:
                st.info("Las superficies no presentan cambios entre los años elegidos.")
            st.caption("Cambio (%) = 100 × (área final − área inicial) / área inicial. Si se pasa de cero a un área positiva, el porcentaje queda sin definir. El cambio neto no identifica qué clases se transformaron en otras.")
            st.download_button("Descargar comparación CSV", data=cambio.to_csv(index=False).encode("utf-8-sig"), file_name=f"Cambios_cobertura_{codigo}_{inicial}_{final}.csv", mime="text/csv", key=f"{clave}_descarga_cambios")
    with t_datos:
        st.write(f"**Serie histórica:** {ruta_serie.name}")
        if ruta_anual:
            st.write(f"**Distribución anual:** {ruta_anual.name}")
        else:
            st.caption("No se encontró el CSV anual; la distribución se calcula con la serie histórica.")
        st.dataframe(datos, hide_index=True, use_container_width=True)
        for etiqueta, ruta in (("serie histórica original", ruta_serie), ("distribución anual original", ruta_anual)):
            if ruta:
                st.download_button(f"Descargar {etiqueta}", data=ruta.read_bytes(), file_name=ruta.name, mime="text/csv", key=f"{clave}_original_{etiqueta}")
        st.caption("Las superficies se obtienen del nivel seleccionado, evitando contar dos veces categorías y subcategorías.")

def mostrar_coberturas_mapbiomas(nombre_territorio: str) -> None:
    """Navegación principal única: Nivel 1 | Nivel 2 | Natural/Antrópico.

    GIF, métricas, gráficas y tablas de cada categoría se muestran juntos,
    sin repetir ni mezclar las estadísticas Ant/Nat con los niveles generales.
    """
    config = COBERTURAS_POR_TERRITORIO.get(nombre_territorio)
    if config is None:
        st.info("Todavía no se han incorporado coberturas MapBiomas para esta sede.")
        return

    st.markdown("### 🗺️ Coberturas de la tierra · MapBiomas")
    st.caption(
        "Explora las coberturas generales en dos niveles de detalle y la "
        "síntesis Natural/Antrópico, cada una con su animación y sus estadísticas."
    )
    codigos = list(config["zonas"])
    if len(codigos) > 1:
        codigo = st.selectbox(
            "Zona de análisis", codigos,
            format_func=lambda c: config["zonas"][c],
            key=f"cob_zona_{normalizar_etiqueta(nombre_territorio)}",
        )
        st.caption("SA = San Andrés · SAC = San Andrés Costa. Las estadísticas se consultan por zona.")
    else:
        codigo = codigos[0]

    tab_uno, tab_dos, tab_antnat = st.tabs([
        "🌳 Nivel 1", "🧩 Nivel 2", "🌿 Natural / antrópico",
    ])
    with tab_uno:
        mostrar_analisis_coberturas_nivel(nombre_territorio, codigo, "Nivel 1")
    with tab_dos:
        mostrar_analisis_coberturas_nivel(nombre_territorio, codigo, "Nivel 2")
    with tab_antnat:
        mostrar_analisis_natural_antropico(nombre_territorio, codigo)

__all__ = ['CARPETA_COBERTURAS', 'COBERTURAS_POR_TERRITORIO', 'COLORES_COBERTURAS', 'encontrar_csv_coberturas', 'MAPBIOMAS_GIFS_POR_TERRITORIO', 'MAPBIOMAS_GIFS_NOMBRES_ANTIGUOS', 'buscar_gif_mapbiomas', '_mostrar_gif_mapbiomas', 'mostrar_presentacion_cobertura_mapbiomas', 'buscar_csv_natural_antropico', '_tipo_natural_antropico', '_numero_antnat', 'cargar_csv_natural_antropico', 'mostrar_analisis_natural_antropico', 'cargar_csv_cobertura', 'preparar_cobertura_nivel', 'comparar_coberturas', 'mostrar_resumen_coberturas', 'mostrar_analisis_coberturas_nivel', 'mostrar_coberturas_mapbiomas']
