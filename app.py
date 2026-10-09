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

# Dependencias del módulo de agua subterránea.
# La aplicación sigue abriendo aunque todavía no estén instaladas;
# en ese caso la propia sección indica qué falta.
try:
    import numpy as np
    import xarray as xr
except ImportError:
    np = None
    xr = None

VERSION_APP = "PROTOTIPO-SIAMS-V36-LOGO-COMPACTO-2026-10-09"
FECHA_ACTUALIZACION = "9 de octubre de 2026"

# =========================================================
# CONFIGURACIÓN GENERAL Y LOGO SIAMS
# =========================================================
# Se aprovecha el icono existente al lado de app.py; si todavía no
# se subió a GitHub, la aplicación sigue funcionando con 💧.
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

# =========================================================
# ESTILOS
# =========================================================

st.markdown(
    """

    <style>
    /* =========================================================
       SIAMS - ESTILOS RESPONSIVOS Y COMPATIBLES LIGHT / DARK
       ========================================================= */

    :root {
        --siams-verde-oscuro: #0b3d36;
        --siams-verde: #146c5c;
        --siams-verde-2: #1f7f6c;
        --siams-borde: rgba(128, 128, 128, 0.28);
        --siams-sombra: 0 6px 18px rgba(0, 0, 0, 0.08);
    }

    .stApp {
        background: var(--background-color);
        color: var(--text-color);
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stHorizontalBlock"] > div,
    [data-testid="column"],
    [data-testid="stVerticalBlock"],
    [data-testid="stVerticalBlockBorderWrapper"] {
        min-width: 0 !important;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b3d36 0%, #124f45 100%);
    }

    /* Identidad compacta: evita ampliar un JPEG que puede tener baja resolución. */
    .siams-sidebar-brand {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin: 0.25rem 0 1.4rem 0;
        padding: 0.4rem 0;
        min-width: 0;
    }
    .siams-sidebar-brand__logo {
        flex: 0 0 56px;
        width: 56px;
        height: 56px;
        border-radius: 12px;
        overflow: hidden;
        background: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
    }
    .siams-sidebar-brand__logo img {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: contain;
        image-rendering: auto;
    }
    .siams-sidebar-brand__fallback {
        font-size: 1.7rem;
        line-height: 1;
    }
    .siams-sidebar-brand__label {
        flex: 1;
        min-width: 0;
    }
    .siams-sidebar-brand__label strong {
        display: block;
        font-size: 1.45rem;
        font-weight: 800;
        line-height: 1.2;
        letter-spacing: 0.02em;
        color: #ffffff !important;
    }
    .siams-sidebar-brand__label small {
        display: block;
        margin-top: 0.2rem;
        font-size: 0.82rem;
        line-height: 1.3;
        color: #d4ece6 !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] small {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background: var(--secondary-background-color) !important;
        border-radius: 10px !important;
        border-color: var(--siams-borde) !important;
    }

    [data-testid="stSidebar"] div[data-baseweb="select"] > div *,
    [data-testid="stSidebar"] div[data-baseweb="select"] input {
        color: var(--text-color) !important;
    }

    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stSelectbox label {
        font-weight: 650;
    }

    /* HERO */
    .hero {
        padding: clamp(1.6rem, 4vw, 3.2rem);
        border-radius: 24px;
        color: #ffffff !important;
        background:
            linear-gradient(90deg, rgba(7, 53, 49, 0.98), rgba(18, 112, 91, 0.84));
        margin-bottom: 1.5rem;
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.15);
        overflow: hidden;
        overflow-wrap: anywhere;
        word-break: normal;
    }

    .hero * {
        color: #ffffff !important;
    }

    .hero h1 {
        font-size: clamp(2rem, 5vw, 3.2rem);
        line-height: 1.08;
        margin: 0.35rem 0 0.8rem 0;
    }

    .hero p {
        max-width: 900px;
        font-size: clamp(0.98rem, 1.5vw, 1.08rem);
        line-height: 1.7;
        margin-bottom: 0;
    }

    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.12rem;
        font-size: 0.80rem;
        font-weight: 800;
        opacity: 0.9;
    }

    .section-title {
        color: var(--text-color) !important;
        font-size: clamp(1.35rem, 3vw, 1.75rem);
        font-weight: 800;
        margin: 1.2rem 0 0.8rem 0;
    }

    /* TARJETAS Y CAJAS */
    .card,
    .status-card,
    .metadata-box,
    .soft-box,
    .warning-box,
    .interpretation-box {
        box-sizing: border-box;
        max-width: 100%;
        min-width: 0;
        height: auto;
        overflow: hidden;
        overflow-wrap: anywhere;
        word-break: normal;
        white-space: normal;
    }

    .card {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid var(--siams-borde);
        border-radius: 18px;
        padding: 1.25rem 1.35rem;
        min-height: 170px;
        box-shadow: var(--siams-sombra);
        margin-bottom: 0.8rem;
    }

    .card h3 {
        color: var(--primary-color) !important;
        margin-top: 0;
        margin-bottom: 0.6rem;
        line-height: 1.25;
        overflow-wrap: anywhere;
    }

    .card p {
        color: var(--text-color) !important;
        line-height: 1.62;
        margin-bottom: 0;
    }

    .soft-box {
        background: color-mix(in srgb, var(--primary-color) 10%, var(--background-color));
        color: var(--text-color);
        border-left: 5px solid var(--primary-color);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin: 0.8rem 0 1rem 0;
    }

    .warning-box {
        background: color-mix(in srgb, #d99a1b 13%, var(--background-color));
        color: var(--text-color);
        border-left: 5px solid #d99a1b;
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin: 0.8rem 0 1rem 0;
    }

    .interpretation-box {
        background: color-mix(in srgb, #386fa4 12%, var(--background-color));
        color: var(--text-color);
        border-left: 5px solid #386fa4;
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin: 0.8rem 0 1rem 0;
    }

    .soft-box *,
    .warning-box *,
    .interpretation-box *,
    .metadata-box * {
        color: var(--text-color) !important;
    }

    .metadata-box {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid var(--siams-borde);
        border-radius: 14px;
        padding: 0.9rem 1rem;
        margin: 0.75rem 0 1rem 0;
        font-size: 0.94rem;
        line-height: 1.55;
    }

    /* ESTADO / SEMÁFORO */
    .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 0.85rem;
        margin: 0.9rem 0 1.4rem 0;
    }

    .status-card {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid var(--siams-borde);
        border-radius: 16px;
        padding: 1rem 1.05rem;
        box-shadow: var(--siams-sombra);
    }

    .status-card h4 {
        color: var(--text-color) !important;
        margin: 0 0 0.45rem 0;
        font-size: 1rem;
        line-height: 1.25;
    }

    .status-card > div {
        color: var(--text-color) !important;
        line-height: 1.45;
    }

    .status-pill {
        display: inline-block;
        border-radius: 999px;
        padding: 0.22rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 800;
        margin-bottom: 0.45rem;
        white-space: normal;
    }

    .status-completo { background: #daf3e7; color: #126447 !important; }
    .status-proceso { background: #fff0c7; color: #8a5a00 !important; }
    .status-pendiente { background: #eceff1; color: #52606d !important; }
    .status-nodatos { background: #f8dfe1; color: #9c2631 !important; }

    /* MÉTRICAS */
    div[data-testid="stMetric"] {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid var(--siams-borde);
        border-radius: 16px;
        padding: 0.95rem 1rem;
        box-shadow: var(--siams-sombra);
        min-width: 0 !important;
        height: 100%;
    }

    div[data-testid="stMetric"] * {
        max-width: 100%;
    }

    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] p,
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] > div {
        color: var(--text-color) !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: normal !important;
        text-overflow: unset !important;
        overflow: visible !important;
    }

    div[data-testid="stMetricLabel"] p {
        font-size: clamp(0.78rem, 1vw, 0.95rem) !important;
        line-height: 1.22 !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: clamp(1rem, 1.5vw, 1.45rem) !important;
        line-height: 1.18 !important;
    }

    /* RESULTADO DE TENDENCIAS - evita recorte del texto en st.metric */
    .trend-result-card {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid var(--siams-borde);
        border-radius: 16px;
        padding: 0.95rem 1rem;
        box-shadow: var(--siams-sombra);
        min-height: 96px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        overflow: visible;
    }

    .trend-result-card .trend-label {
        color: var(--text-color) !important;
        font-size: 0.88rem;
        line-height: 1.2;
        opacity: 0.78;
        margin-bottom: 0.45rem;
    }

    .trend-result-card .trend-value {
        color: var(--text-color) !important;
        font-size: clamp(1.02rem, 1.45vw, 1.35rem);
        line-height: 1.25;
        font-weight: 750;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        overflow-wrap: anywhere !important;
    }

    /* TABS, EXPANDERS, BOTONES E INPUTS */
    div[data-testid="stTabs"] button {
        font-size: 0.96rem;
        font-weight: 700;
        color: var(--text-color) !important;
        white-space: normal !important;
        height: auto !important;
        min-height: 2.7rem;
        line-height: 1.25;
    }

    div[data-testid="stExpander"] details {
        background: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--siams-borde) !important;
        border-radius: 12px !important;
    }

    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary * {
        color: var(--text-color) !important;
    }

    .stDownloadButton button,
    .stButton button {
        background: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--siams-borde) !important;
        border-radius: 10px !important;
        white-space: normal !important;
        min-height: 2.5rem;
    }

    .stDownloadButton button *,
    .stButton button * {
        color: var(--text-color) !important;
    }

    .stDownloadButton button:hover,
    .stButton button:hover {
        border-color: var(--primary-color) !important;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"] > div,
    input,
    textarea {
        color: var(--text-color) !important;
    }

    ul[role="listbox"],
    ul[role="listbox"] li,
    div[role="option"] {
        background: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
    }

    div[role="option"] * {
        color: var(--text-color) !important;
    }

    /* ALERTAS / TABLAS / CÓDIGO */
    [data-testid="stAlertContainer"],
    [data-testid="stAlertContainer"] * {
        color: var(--text-color) !important;
    }

    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }

    pre,
    code {
        white-space: pre-wrap !important;
        overflow-wrap: anywhere !important;
    }

    /* IMÁGENES */
    [data-testid="stImage"] img {
        max-width: 100% !important;
        height: auto !important;
        object-fit: contain;
    }

    /* NAVEGADOR DE UBICACIÓN · SEDE BOGOTÁ */
    .location-shell {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid var(--siams-borde);
        border-radius: 20px;
        padding: 1rem 1.1rem 1.15rem 1.1rem;
        box-shadow: var(--siams-sombra);
        margin: 0.8rem 0 1rem 0;
    }

    .location-progress {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin: 0.55rem 0 1rem 0;
    }

    .location-step {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 30px;
        height: 30px;
        padding: 0 0.55rem;
        border-radius: 999px;
        border: 1px solid var(--siams-borde);
        background: var(--secondary-background-color);
        color: var(--text-color) !important;
        font-size: 0.78rem;
        font-weight: 800;
    }

    .location-step.active {
        background: color-mix(in srgb, var(--primary-color) 18%, var(--secondary-background-color));
        border-color: var(--primary-color);
    }

    .location-arrow {
        opacity: 0.55;
        color: var(--text-color) !important;
        font-weight: 800;
    }

    .location-caption {
        color: var(--text-color) !important;
        opacity: 0.78;
        font-size: 0.92rem;
        line-height: 1.5;
        margin-top: 0.35rem;
    }

    /* RESPONSIVE */
    @media (max-width: 900px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .hero {
            border-radius: 18px;
        }

        .status-grid {
            grid-template-columns: 1fr;
        }

        .card {
            min-height: auto;
        }
    }

    @media (max-width: 600px) {
        .hero {
            padding: 1.4rem 1.2rem;
        }

        .card,
        .status-card,
        .metadata-box,
        .soft-box,
        .warning-box,
        .interpretation-box {
            padding-left: 0.95rem;
            padding-right: 0.95rem;
        }

        div[data-testid="stMetric"] {
            padding: 0.8rem 0.9rem;
        }
    }


    /* MAPA INSTITUCIONAL DEL INICIO */
    [data-testid="stPlotlyChart"] {
        border-radius: 18px;
        overflow: hidden;
    }

    [data-testid="stPlotlyChart"] > div {
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.08);
    }

    footer {
        visibility: hidden;
    }

    /* SENTINEL-2 · PANEL AUTÓNOMO */
    .sentinel-banner {
        background: linear-gradient(112deg, #092f37 0%, #146b61 58%, #267da0 100%);
        color: #ffffff !important;
        border-radius: 20px;
        padding: 1.45rem 1.8rem;
        margin: 0.6rem 0 1.1rem 0;
        box-shadow: 0 9px 25px rgba(5, 43, 48, .14);
    }
    .sentinel-banner h2 {
        color: #ffffff !important;
        margin: .35rem 0 .6rem 0;
        font-size: clamp(1.35rem, 3vw, 1.9rem);
        line-height: 1.2;
    }
    .sentinel-banner p {color: #f1fffa !important; margin: 0; line-height: 1.55;}
    .sentinel-kicker {font-size: .76rem; letter-spacing: .14rem; font-weight: 850; opacity: .9;}
    .sentinel-method-card {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid var(--siams-borde);
        border-radius: 14px;
        padding: .9rem 1rem;
        min-height: 142px;
        box-shadow: var(--siams-sombra);
        margin-bottom: .6rem;
    }
    .sentinel-method-title {font-weight: 850; font-size: 1.05rem; margin-bottom: .25rem;}
    .sentinel-method-tag {font-size: .78rem; font-weight: 700; opacity: .74;}
    .sentinel-method-card p {font-size: .91rem; line-height: 1.45; margin: .55rem 0 0 0;}
    @media (max-width: 700px) {
        .sentinel-banner {padding: 1.15rem; border-radius: 14px;}
        .sentinel-method-card {min-height: auto;}
    }


    /* QGIS - fichas cartográficas bajo cada PDF de ubicación */
    .qgis-metadata-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: var(--text-color);
        margin: 1.1rem 0 0.5rem 0;
    }
    .qgis-metadata-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.4rem 0 0.8rem 0;
    }
    .qgis-metadata-card {
        background: var(--secondary-background-color);
        border: 1px solid var(--siams-borde);
        border-radius: 14px;
        padding: 0.9rem 1rem;
        color: var(--text-color);
        min-width: 0;
        overflow-wrap: anywhere;
        line-height: 1.5;
    }
    .qgis-metadata-card h4 {
        margin: 0 0 0.45rem 0;
        color: var(--primary-color) !important;
        font-size: 0.96rem;
    }
    .qgis-metadata-card p { margin: 0; font-size: 0.87rem; }
    .qgis-metadata-note {
        opacity: .82;
        font-size: .83rem;
        line-height: 1.5;
        margin: .35rem 0 1.3rem;
        color: var(--text-color);
    }
    @media (max-width: 950px) {
        .qgis-metadata-grid { grid-template-columns: 1fr; }
    }

    </style>

""",
    unsafe_allow_html=True,
)

# =========================================================
# DATOS DE PROTOTIPO
# Reemplazar luego por datos reales
# =========================================================

MESES = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
]



# =========================================================
# RED DE SEDES UNAL PARA EL MAPA DE INICIO
# =========================================================

UNAL_SEDES = pd.DataFrame([
    {
        "Sede": "Bogotá",
        "Ciudad": "Bogotá D.C.",
        "lat": 4.6386,
        "lon": -74.0841,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Bogotá, incorporada al prototipo con un piloto cartográfico de ubicación por niveles.",
        "Tamano": 16,
    },
    {
        "Sede": "Medellín",
        "Ciudad": "Medellín, Antioquia",
        "lat": 6.260650,
        "lon": -75.579592,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Medellín, incorporada al prototipo con cartografía y climatología.",
        "Tamano": 16,
    },
    {
        "Sede": "Manizales",
        "Ciudad": "Manizales, Caldas",
        "lat": 5.070353,
        "lon": -75.513816,
        "Estado": "Otra sede UNAL (contexto)",
        "Descripcion": "Sede Manizales de la Universidad Nacional de Colombia.",
        "Tamano": 11,
    },
    {
        "Sede": "Palmira",
        "Ciudad": "Palmira, Valle del Cauca",
        "lat": 3.512231,
        "lon": -76.307211,
        "Estado": "Otra sede UNAL (contexto)",
        "Descripcion": "Sede Palmira de la Universidad Nacional de Colombia.",
        "Tamano": 11,
    },
    {
        "Sede": "Amazonia",
        "Ciudad": "Leticia, Amazonas",
        "lat": -4.193717,
        "lon": -69.941001,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Amazonia, trabajada en SIAMS como territorio Leticia.",
        "Tamano": 16,
    },
    {
        "Sede": "Caribe",
        "Ciudad": "San Andrés Isla",
        "lat": 12.536552,
        "lon": -81.707935,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Caribe, representada en SIAMS con información de San Andrés.",
        "Tamano": 16,
    },
    {
        "Sede": "Orinoquía",
        "Ciudad": "Arauca, Arauca",
        "lat": 7.012222763876252,
        "lon": -70.74338825990411,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Orinoquía, incorporada al prototipo como territorio Arauca.",
        "Tamano": 16,
    },
    {
        "Sede": "Tumaco",
        "Ciudad": "Tumaco, Nariño",
        "lat": 1.610206,
        "lon": -78.720520,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede Tumaco, trabajada en SIAMS con cartografía y datos hidroclimáticos.",
        "Tamano": 16,
    },
    {
        "Sede": "La Paz",
        "Ciudad": "La Paz, Cesar",
        "lat": 10.390218033322455,
        "lon": -73.20038917337925,
        "Estado": "Territorio integrado en SIAMS",
        "Descripcion": "Sede de La Paz, incorporada al prototipo SIAMS.",
        "Tamano": 16,
    },
])
TERRITORIOS = {
    "Bogotá": {
        "region": "Región Andina",
        "departamento": "Bogotá D.C.",
        "sede": "Universidad Nacional de Colombia – Sede Bogotá",
        "lat": 4.6386,
        "lon": -74.0841,
        "area_principal": "Campus Ciudad Universitaria",
        "contexto": "Bogotá D.C. y entorno metropolitano",
        "fuente_clima": "Pendiente de integración",
        "estado_datos": "Piloto cartográfico de ubicación habilitado",
        "descripcion": (
            "La Sede Bogotá se incorpora al prototipo SIAMS mediante un módulo de ubicación "
            "multiescala que permite pasar de Colombia a Bogotá, luego al campus y finalmente "
            "a una vista web interactiva de la Ciudad Universitaria."
        ),
        "precipitacion": [],
        "temperatura": [],
        "humedad": [],
        "hallazgo": (
            "La ubicación de la sede se presenta como una secuencia cartográfica de tres escalas "
            "complementada con un mapa interactivo para navegación, zoom y consulta espacial."
        ),
    },
    "Leticia": {
        "region": "Amazonía colombiana",
        "departamento": "Amazonas",
        "sede": "Universidad Nacional de Colombia – Sede Amazonia",
        "lat": -4.193717,
        "lon": -69.941001,
        "area_principal": "15 km",
        "contexto": "Municipio de Leticia",
        "fuente_clima": "NASA POWER",
        "estado_datos": "IDEAM con disponibilidad limitada",
        "descripcion": (
            "Leticia se ubica en el extremo sur de Colombia, junto al río Amazonas. "
            "El territorio presenta alta humedad, abundante precipitación y una fuerte "
            "relación entre los ecosistemas amazónicos, los sistemas fluviales y las "
            "dinámicas urbanas transfronterizas."
        ),
        "precipitacion": [260, 275, 320, 335, 310, 245, 190, 175, 205, 250, 280, 300],
        "temperatura": [26.0, 26.1, 25.8, 25.6, 25.5, 25.2, 25.0, 25.4, 26.0, 26.3, 26.2, 26.1],
        "humedad": [86, 86, 88, 89, 89, 88, 86, 84, 84, 85, 86, 86],
        "hallazgo": (
            "La disponibilidad de series IDEAM continuas es limitada, por lo que "
            "NASA POWER se plantea como fuente climática principal para el prototipo."
        ),
    },
    "Tumaco": {
        "region": "Pacífico colombiano",
        "departamento": "Nariño",
        "sede": "Universidad Nacional de Colombia – Sede Tumaco",
        "lat": 1.610206,
        "lon": -78.720520,
        "area_principal": "25 km",
        "contexto": "Hasta 50 km",
        "fuente_clima": "IDEAM + NASA POWER",
        "estado_datos": "Series parciales complementadas",
        "descripcion": (
            "Tumaco se localiza en la costa pacífica colombiana. El territorio se "
            "caracteriza por elevada precipitación, alta humedad y una interacción "
            "permanente entre sistemas continentales, costeros, estuarinos y marinos."
        ),
        "precipitacion": [310, 285, 330, 390, 430, 360, 280, 240, 265, 315, 345, 330],
        "temperatura": [26.2, 26.4, 26.3, 26.1, 25.9, 25.7, 25.6, 25.7, 25.8, 26.0, 26.1, 26.2],
        "humedad": [84, 84, 85, 86, 87, 86, 85, 84, 84, 85, 85, 84],
        "hallazgo": (
            "En Tumaco existen algunas series IDEAM útiles, aunque su continuidad "
            "debe evaluarse y complementarse con NASA POWER."
        ),
    },
    "Medellín": {
        "region": "Región Andina",
        "departamento": "Antioquia",
        "sede": "Universidad Nacional de Colombia – Sede Medellín",
        "lat": 6.262190,
        "lon": -75.576968,
        "area_principal": "Entorno urbano y regional",
        "contexto": "Valle de Aburrá",
        "fuente_clima": "NASA POWER",
        "estado_datos": "Climatología NASA POWER incorporada",
        "descripcion": (
            "La Sede Medellín se localiza en el Valle de Aburrá, un territorio urbano-andino "
            "con fuertes contrastes topográficos, una red de quebradas tributarias del río Medellín "
            "y condicionantes geológicos, ecológicos y de amenaza por inundación."
        ),
        "precipitacion": [], "temperatura": [], "humedad": [],
        "hallazgo": (
            "Para esta versión se prioriza la integración cartográfica: geología regional, "
            "estructura ecológica principal y amenaza por inundación."
        ),
    },
    "San Andrés": {
        "region": "Caribe insular colombiano",
        "departamento": "San Andrés, Providencia y Santa Catalina",
        "sede": "Universidad Nacional de Colombia – Sede Caribe",
        "lat": 12.536552,
        "lon": -81.707935,
        "area_principal": "Isla de San Andrés",
        "contexto": "Territorio insular y acuífero",
        "fuente_clima": "NASA POWER",
        "estado_datos": "Climatología NASA POWER + cartografía hidrogeológica",
        "descripcion": (
            "San Andrés es un territorio insular del Caribe colombiano donde la disponibilidad "
            "de agua dulce depende estrechamente de la lluvia y de los acuíferos de la isla. "
            "La vulnerabilidad del acuífero y la calidad de las aguas subterráneas son componentes "
            "centrales para la lectura hidroambiental del territorio."
        ),
        "precipitacion": [], "temperatura": [], "humedad": [],
        "hallazgo": (
            "La cartografía de CORALINA permite integrar geología, vulnerabilidad del acuífero, "
            "nitratos y microcuencas/arroyos estacionales en una misma lectura territorial."
        ),
    },
    "Arauca": {
        "region": "Orinoquía colombiana",
        "departamento": "Arauca",
        "sede": "Universidad Nacional de Colombia – Sede Orinoquía",
        "lat": 7.012222763876252,
        "lon": -70.74338825990411,
        "area_principal": "Entorno de la Sede Orinoquía",
        "contexto": "Municipio de Arauca y llanura aluvial",
        "fuente_clima": "IDEAM + NASA POWER",
        "estado_datos": "IDEAM procesado + NASA POWER; ambas fuentes se comparan sin fusionar series",
        "descripcion": (
            "Arauca se localiza en la Orinoquía colombiana, en un territorio de llanura con "
            "fuerte influencia de los sistemas fluviales y marcada estacionalidad hidroclimática. "
            "La Sede Orinoquía se incorpora al prototipo para ampliar la comparación entre regiones."
        ),
        "precipitacion": [], "temperatura": [], "humedad": [],
        "hallazgo": (
            "IDEAM se utiliza como referencia terrestre para precipitación y temperatura; "
            "NASA POWER se conserva para comparación y para viento, presión y radiación."
        ),
    },
    "La Paz": {
        "region": "Caribe continental",
        "departamento": "Cesar",
        "sede": "Universidad Nacional de Colombia – Sede de La Paz",
        "lat": 10.390218033322455,
        "lon": -73.20038917337925,
        "area_principal": "Entorno de la Sede de La Paz",
        "contexto": "Municipio de La Paz y valle del Cesar",
        "fuente_clima": "NASA POWER",
        "estado_datos": "Módulo territorial habilitado; clima se activa al detectar el Excel procesado",
        "descripcion": (
            "La Paz se localiza en el departamento del Cesar, en el Caribe continental colombiano. "
            "Su incorporación permite ampliar el análisis hidroambiental hacia un territorio con "
            "condiciones climáticas y geológicas distintas a las demás sedes priorizadas."
        ),
        "precipitacion": [], "temperatura": [], "humedad": [],
        "hallazgo": (
            "El territorio queda preparado para integrar clima, cartografía y el análisis regional "
            "de anomalías de almacenamiento de agua subterránea mediante GRACE/GLDAS."
        ),
    },
}


# =========================================================
# ESTADO DEL PROTOTIPO Y METADATOS
# =========================================================

ESTADO_COMPONENTES = {
    "Bogotá": [
        ("Identificación y contexto", "Completo", "Sede, coordenadas y contexto territorial incorporados."),
        ("Cartografía e hidrología", "En proceso", "Piloto de ubicación multiescala incorporado; hidrología temática queda para una fase posterior."),
        ("Clima", "Pendiente", "No se ha integrado todavía una base climática específica para Bogotá."),
        ("Geología", "Pendiente", "No se ha incorporado todavía cartografía geológica específica."),
        ("Cobertura y relieve", "Pendiente", "No se han incorporado aún capas temáticas de cobertura o relieve."),
        ("Estaciones y calidad", "Pendiente", "Inventario de estaciones y control de datos por consolidar."),
        ("Hidrogeología", "Pendiente", "Componente por desarrollar."),
        ("IRCA", "Pendiente", "Componente por desarrollar."),
        ("Hidrogeoquímica", "Pendiente", "Componente por desarrollar."),
        ("Monitoreo", "Sin datos", "No se han incorporado series validadas de monitoreo."),
    ],
    "Leticia": [
        ("Identificación y contexto", "Completo", "Sede, localización y síntesis territorial incorporadas."),
        ("Cartografía e hidrología", "Completo", "Mapas regionales de hidrografía, humedales e inundación."),
        ("Clima", "Completo", "NASA POWER procesado como fuente continua principal."),
        ("Geología", "Completo", "Mapa regional del Trapecio Sur incorporado."),
        ("Cobertura y relieve", "Completo", "Coberturas y geomorfología disponibles como referencia."),
        ("Estaciones y calidad", "En proceso", "IDEAM documentado, pero con continuidad insuficiente para la climatología principal."),
        ("Hidrogeología", "En proceso", "Existe referencia académica de pozos; falta consolidar unidades y atributos."),
        ("IRCA", "En proceso", "Mapa académico disponible; faltan series oficiales consolidadas por periodo."),
        ("Hidrogeoquímica", "Pendiente", "No hay una base completa con coordenadas, unidades e iones mayoritarios."),
        ("Monitoreo", "Sin datos", "No se han incorporado series validadas de sondas o nivel."),
    ],
    "Tumaco": [
        ("Identificación y contexto", "Completo", "Sede, localización y síntesis territorial incorporadas."),
        ("Cartografía e hidrología", "Completo", "Hidrografía, manglares e inundación regional incorporados."),
        ("Clima", "Completo", "IDEAM y NASA POWER integrados sin fusionar las series."),
        ("Geología", "Completo", "Mapa geológico regional del POMCA del río Mira."),
        ("Cobertura y relieve", "Completo", "Coberturas y pendientes del contexto regional."),
        ("Estaciones y calidad", "Completo", "Completitud, periodos, estaciones y decisión por variable documentados."),
        ("Hidrogeología", "En proceso", "Falta consolidar unidades hidrogeológicas y pozos georreferenciados."),
        ("IRCA", "Pendiente", "No se ha localizado una base georreferenciada equivalente a la de Leticia."),
        ("Hidrogeoquímica", "Pendiente", "Faltan muestras completas con ubicación, fecha, unidades e iones."),
        ("Monitoreo", "Sin datos", "No se han incorporado series validadas de sondas o nivel."),
    ],    "Medellín": [
        ("Identificación y contexto", "Completo", "Sede, localización y síntesis territorial incorporadas."),
        ("Cartografía e hidrología", "Completo", "Amenaza por inundación incorporada desde el POT de Medellín."),
        ("Clima", "Completo", "NASA POWER procesado e incorporado como fuente climática continua."),
        ("Geología", "Completo", "Plancha 228 del Servicio Geológico Colombiano incorporada."),
        ("Cobertura y relieve", "En proceso", "Estructura Ecológica Principal incorporada como contexto ambiental."),
        ("Estaciones y calidad", "En proceso", "NASA POWER documentado; estaciones IDEAM locales quedan como ampliación futura."),
        ("Hidrogeología", "Pendiente", "No se ha incorporado aún cartografía hidrogeológica específica."),
        ("IRCA", "Pendiente", "No se ha incorporado una base georreferenciada de calidad del agua."),
        ("Hidrogeoquímica", "Pendiente", "No hay muestras hidrogeoquímicas integradas en esta versión."),
        ("Monitoreo", "Sin datos", "No se han incorporado series validadas de sondas o nivel."),
    ],
    "San Andrés": [
        ("Identificación y contexto", "Completo", "Sede Caribe, localización y contexto insular incorporados."),
        ("Cartografía e hidrología", "Completo", "Microcuencas y arroyos estacionales incorporados desde CORALINA."),
        ("Clima", "Completo", "NASA POWER procesado e incorporado como fuente climática continua."),
        ("Geología", "Completo", "Conformación geológica de la isla incorporada."),
        ("Cobertura y relieve", "Pendiente", "No se incluyó aún una capa específica de cobertura o relieve."),
        ("Estaciones y calidad", "En proceso", "NASA POWER documentado; falta consolidar estaciones terrestres locales por variable."),
        ("Hidrogeología", "Completo", "Vulnerabilidad de las rocas que conforman los acuíferos incorporada."),
        ("IRCA", "Pendiente", "No se ha incorporado aún una serie IRCA georreferenciada."),
        ("Hidrogeoquímica", "En proceso", "Mapa de concentraciones de nitratos incorporado como antecedente."),
        ("Monitoreo", "Sin datos", "No se han incorporado series validadas de sondas o nivel."),
    ],
    "Arauca": [
        ("Identificación y contexto", "Completo", "Sede Orinoquía, coordenadas y síntesis territorial incorporadas."),
        ("Cartografía e hidrología", "En proceso", "Se incorporan mapas IDEAM de oferta hídrica, demanda industrial y vertimientos como contexto regional y nacional."),
        ("Clima", "Completo", "IDEAM procesado y NASA POWER se integran como fuentes separadas y comparables."),
        ("Geología", "En proceso", "Mapa Geológico de Colombia 2023 incorporado como referencia regional; falta cartografía de mayor detalle para el entorno de la sede."),
        ("Cobertura y relieve", "Pendiente", "Faltan capas de cobertura, relieve o pendientes específicas para Arauca."),
        ("Estaciones y calidad", "En proceso", "Queda habilitado el inventario de datos y fuentes."),
        ("Hidrogeología", "En proceso", "Se incorporan el sistema acuífero Arauca-Arauquita, PEXAS y mapas IDEAM de puntos y concesiones; GWSa complementa la lectura regional."),
        ("IRCA", "Pendiente", "No se ha incorporado una base georreferenciada de calidad del agua."),
        ("Hidrogeoquímica", "Pendiente", "No hay muestras hidrogeoquímicas integradas en esta versión."),
        ("Monitoreo", "En proceso", "Queda preparado para integrar sondas y series validadas."),
    ],
    "La Paz": [
        ("Identificación y contexto", "Completo", "Sede de La Paz, coordenadas y síntesis territorial incorporadas."),
        ("Cartografía e hidrología", "Pendiente", "Falta incorporar cartografía temática regional validada."),
        ("Clima", "En proceso", "La sección NASA POWER se activa automáticamente al detectar el Excel procesado."),
        ("Geología", "Pendiente", "Falta incorporar cartografía geológica de referencia."),
        ("Cobertura y relieve", "Pendiente", "Faltan capas de cobertura, relieve o pendientes."),
        ("Estaciones y calidad", "En proceso", "Queda habilitado el inventario de datos y fuentes."),
        ("Hidrogeología", "En proceso", "Se incorpora GWSa satelital cuando está disponible el NetCDF GRACE/GLDAS."),
        ("IRCA", "Pendiente", "No se ha incorporado una base georreferenciada de calidad del agua."),
        ("Hidrogeoquímica", "Pendiente", "No hay muestras hidrogeoquímicas integradas en esta versión."),
        ("Monitoreo", "En proceso", "Queda preparado para integrar sondas y series validadas."),
    ],
}

METADATOS_MAPAS = {
    "Leticia": {
        "hidrografia": {
            "entidad": "Instituto SINCHI",
            "producto": "Mapa de hidrografía del municipio de Leticia",
            "alcance": "Municipal y regional",
            "actualidad": "Según el documento cartográfico original",
            "limitacion": "No representa exclusivamente el radio inmediato de la Sede Amazonia.",
        },
        "humedales": {
            "entidad": "Corpoamazonia",
            "producto": "Humedales de Leticia y Puerto Nariño",
            "alcance": "Regional",
            "actualidad": "Según el documento cartográfico original",
            "limitacion": "Incluye humedales ubicados fuera del área principal del prototipo.",
        },
        "inundacion": {
            "entidad": "Corpoamazonia",
            "producto": "Áreas de inundación en la zona urbana de Leticia",
            "alcance": "Zona urbana",
            "actualidad": "Según el documento cartográfico original",
            "limitacion": "Debe interpretarse con la escala y metodología de la fuente.",
        },
        "geologia": {
            "entidad": "Instituto SINCHI",
            "producto": "Unidades geológicas del Trapecio Sur",
            "alcance": "Regional",
            "actualidad": "Información geológica regional",
            "limitacion": "No corresponde a una cartografía detallada exclusiva de la sede.",
        },
        "cobertura": {
            "entidad": "Instituto SINCHI",
            "producto": "Coberturas de la tierra del municipio de Leticia",
            "alcance": "Municipal",
            "actualidad": "Consultar el año visible en el mapa original",
            "limitacion": "Se usa como referencia; no debe interpretarse automáticamente como cobertura actual.",
        },
        "relieve": {
            "entidad": "Instituto SINCHI",
            "producto": "Geomorfología del Trapecio Sur",
            "alcance": "Regional",
            "actualidad": "Según el documento cartográfico original",
            "limitacion": "No reemplaza un DEM ni un cálculo de pendientes alrededor de la sede.",
        },
        "pozos_irca": {
            "entidad": "SENA",
            "producto": "Recurso académico de pozos y calidad del agua",
            "alcance": "Municipio de Leticia",
            "actualidad": "Recurso académico consultado para el prototipo",
            "limitacion": "Los resultados representan puntos y periodos específicos; no todo el municipio.",
        },
    },
    "Tumaco": {
        "hidrografia": {
            "entidad": "Parques Nacionales Naturales de Colombia",
            "producto": "Sistemas hídricos de Tumaco y Bajo Mira",
            "alcance": "Regional y marino-costero",
            "actualidad": "Según el documento cartográfico original",
            "limitacion": "No representa únicamente el entorno de la Sede Tumaco.",
        },
        "manglares": {
            "entidad": "CORPONARIÑO y entidades participantes",
            "producto": "Distribución regional de manglares en Nariño",
            "alcance": "Departamental y regional",
            "actualidad": "Consultar el año visible en el mapa original",
            "limitacion": "Debe utilizarse como referencia histórica y regional.",
        },
        "inundacion": {
            "entidad": "CORPONARIÑO – POMCA Río Mira",
            "producto": "Amenaza por inundación en la cuenca del río Mira",
            "alcance": "Cuenca hidrográfica",
            "actualidad": "Según el POMCA consultado",
            "limitacion": "La amenaza depende de la metodología, escala y periodo del estudio.",
        },
        "geologia": {
            "entidad": "CORPONARIÑO – POMCA Río Mira",
            "producto": "Unidades geológicas de la cuenca del río Mira",
            "alcance": "Cuenca hidrográfica",
            "actualidad": "Según el POMCA consultado",
            "limitacion": "Es un contexto geológico regional, no una cartografía de detalle de la sede.",
        },
        "cobertura": {
            "entidad": "CORPONARIÑO – POMCA Río Mira",
            "producto": "Cobertura y uso actual de la tierra",
            "alcance": "Cuenca hidrográfica",
            "actualidad": "Consultar el año visible en el mapa original",
            "limitacion": "Incluye sectores de la cuenca fuera del área inmediata de Tumaco.",
        },
        "relieve": {
            "entidad": "CORPONARIÑO – POMCA Río Mira",
            "producto": "Pendientes de la cuenca hidrográfica del río Mira",
            "alcance": "Cuenca hidrográfica",
            "actualidad": "Según el POMCA consultado",
            "limitacion": "No reemplaza un DEM recortado específicamente a la sede.",
        },
    },
    "Medellín": {
        "geologia": {
            "entidad": "Servicio Geológico Colombiano (SGC)",
            "producto": "Plancha geológica 228 – Medellín",
            "alcance": "Regional, escala 1:100.000",
            "actualidad": "Según la edición de la plancha consultada",
            "limitacion": "Es cartografía regional y no reemplaza estudios geotécnicos o geológicos de detalle de la sede.",
        },
        "estructura_ecologica": {
            "entidad": "Alcaldía de Medellín – Plan de Ordenamiento Territorial (POT)",
            "producto": "Estructura Ecológica Principal",
            "alcance": "Municipio de Medellín",
            "actualidad": "Según el POT y la cartografía consultada",
            "limitacion": "Se utiliza como contexto ambiental municipal; no corresponde a una capa exclusiva de la sede.",
        },
        "inundacion": {
            "entidad": "Alcaldía de Medellín – Plan de Ordenamiento Territorial (POT)",
            "producto": "Amenaza por inundaciones",
            "alcance": "Municipio de Medellín",
            "actualidad": "Según el POT y la cartografía consultada",
            "limitacion": "La amenaza debe interpretarse según la escala, metodología y fecha de la fuente.",
        },
    },
    "San Andrés": {
        "geologia": {
            "entidad": "CORALINA",
            "producto": "Conformación geológica de la isla de San Andrés",
            "alcance": "Isla de San Andrés",
            "actualidad": "Figura 3 del documento de cuencas hidrográficas consultado",
            "limitacion": "La lectura debe respetar la escala y clasificación del documento original.",
        },
        "vulnerabilidad_acuifero": {
            "entidad": "CORALINA",
            "producto": "Vulnerabilidad de las rocas que conforman los acuíferos",
            "alcance": "Isla de San Andrés",
            "actualidad": "Figura 4 del documento consultado",
            "limitacion": "Representa vulnerabilidad hidrogeológica regional y no sustituye evaluación puntual del acuífero.",
        },
        "nitratos": {
            "entidad": "CORALINA",
            "producto": "Concentraciones de nitratos en aguas subterráneas",
            "alcance": "Cuenca / isla de San Andrés",
            "actualidad": "Figura 9 del documento consultado",
            "limitacion": "Los valores corresponden al periodo y puntos de muestreo de la fuente original.",
        },
        "microcuencas": {
            "entidad": "CORALINA",
            "producto": "Principales microcuencas y arroyos estacionales",
            "alcance": "Isla de San Andrés",
            "actualidad": "Figura 11 del documento consultado",
            "limitacion": "El mapa representa drenajes estacionales y límites de microcuenca según la fuente original.",
        },
    },
    "Arauca": {
        "demanda_industria": {
            "entidad": "IDEAM",
            "producto": "Demanda de agua de la industria manufacturera por departamento",
            "alcance": "Nacional, con lectura departamental",
            "actualidad": "2021",
            "limitacion": "Es un indicador departamental; no representa la demanda puntual del municipio ni de la Sede Orinoquía.",
        },
        "vertimientos_industria": {
            "entidad": "IDEAM",
            "producto": "Vertimientos de aguas residuales de la industria manufacturera",
            "alcance": "Nacional, con lectura departamental",
            "actualidad": "2021",
            "limitacion": "La información es agregada por departamento y debe interpretarse como contexto de presión sobre el recurso hídrico.",
        },
        "anomalia_oferta_alta": {
            "entidad": "IDEAM – Estudio Nacional del Agua",
            "producto": "Anomalía de la Oferta Hídrica Superficial en condiciones altas",
            "alcance": "Nacional por unidades hidrográficas",
            "actualidad": "ENA 2014",
            "limitacion": "Es una referencia histórica de escala nacional y no sustituye un análisis hidrológico local actualizado de Arauca.",
        },
        "puntos_agua_subterranea": {
            "entidad": "IDEAM – Estudio Nacional del Agua",
            "producto": "Distribución de puntos de agua subterránea por Autoridad Ambiental",
            "alcance": "Nacional por autoridad ambiental",
            "actualidad": "ENA 2014",
            "limitacion": "Representa el número de puntos inventariados por autoridad ambiental, no la ubicación individual de cada pozo o aljibe.",
        },
        "volumen_concesionado": {
            "entidad": "IDEAM – Estudio Nacional del Agua",
            "producto": "Volúmenes de agua subterránea concesionada objeto de cobro TUA",
            "alcance": "Nacional",
            "actualidad": "ENA 2014",
            "limitacion": "Es información histórica agregada; no equivale a extracción real actual ni a disponibilidad del acuífero.",
        },
        "criterio_hidrogeologico": {
            "entidad": "Servicio Geológico Colombiano – PEXAS",
            "producto": "Programa de Exploración de Aguas Subterráneas – criterio de demanda e hidrogeológico",
            "alcance": "Regional, con visualización sobre Arauca y departamentos vecinos",
            "actualidad": "2005",
            "limitacion": "La capa es de planificación y exploración regional y no reemplaza una caracterización hidrogeológica local del sistema acuífero.",
        },
        "geologia": {
            "entidad": "Servicio Geológico Colombiano (SGC)",
            "producto": "Mapa Geológico de Colombia 2023",
            "alcance": "Nacional",
            "actualidad": "2023",
            "limitacion": "La escala nacional sirve como contexto regional; para la sede se requiere cartografía geológica de mayor detalle.",
        },
        "sistema_acuifero": {
            "entidad": "IDEAM",
            "producto": "SAP3.3 Sistema Acuífero Arauca-Arauquita",
            "alcance": "Arauca-Arauquita",
            "actualidad": "Anexo 7 de Aguas Subterráneas consultado",
            "limitacion": "La propia ficha reporta información hidrogeológica local limitada y varios campos como NRI; debe presentarse como delimitación y antecedente, no como caracterización completa.",
        },
    },
}

FUENTES_CLIMATICAS = pd.DataFrame({
    "Variable": [
        "Precipitación", "Temperatura media", "Temperaturas extremas",
        "Humedad relativa", "Viento", "Presión", "Radiación",
    ],
    "Leticia": [
        "NASA POWER", "NASA POWER", "NASA POWER", "NASA POWER",
        "NASA POWER", "NASA POWER", "NASA POWER",
    ],
    "Tumaco": [
        "IDEAM principal; NASA compara",
        "IDEAM principal; NASA complementa",
        "IDEAM con cautela; NASA complementa",
        "NASA + contraste IDEAM parcial",
        "NASA POWER", "NASA POWER", "NASA POWER",
    ],
    "Medellín": [
        "NASA POWER", "NASA POWER", "NASA POWER", "NASA POWER",
        "NASA POWER", "NASA POWER", "NASA POWER",
    ],
    "San Andrés": [
        "NASA POWER", "NASA POWER", "NASA POWER", "NASA POWER",
        "NASA POWER", "NASA POWER", "NASA POWER",
    ],
})

# =========================================================
# AGUA SUBTERRÁNEA · GRACE / GLDAS
# =========================================================

def encontrar_archivo_gws():
    """Localiza el NetCDF de anomalías de almacenamiento subterráneo."""
    carpeta_codigo = Path(__file__).resolve().parent
    carpetas = [
        carpeta_codigo,
        carpeta_codigo / "DATOS GWS",
        carpeta_codigo / "datos",
        carpeta_codigo / "datos" / "gws",
        carpeta_codigo / "datos" / "agua_subterranea",
    ]

    for carpeta in carpetas:
        ruta = carpeta / "COL_GWS_estimations.nc"
        if ruta.exists() and ruta.is_file():
            return ruta

    for carpeta in carpetas:
        if carpeta.exists():
            coincidencias = sorted(carpeta.glob("COL_GWS_estimations*.nc"))
            if coincidencias:
                return coincidencias[0]
    return None


ARCHIVO_GWS = encontrar_archivo_gws()


@st.cache_resource(show_spinner=False)
def cargar_dataset_gws(ruta_texto: str):
    """Carga el NetCDF completo en memoria para evitar dejar el archivo abierto."""
    if xr is None:
        raise ImportError("Falta instalar xarray y un motor NetCDF (netCDF4 o h5netcdf).")
    with xr.open_dataset(ruta_texto) as ds:
        return ds.load()


def distancia_haversine_km(lat1, lon1, lat2, lon2):
    """Distancia geodésica aproximada en kilómetros, vectorizada con NumPy."""
    radio = 6371.0088
    lat1r = np.radians(lat1)
    lon1r = np.radians(lon1)
    lat2r = np.radians(lat2)
    lon2r = np.radians(lon2)
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1r) * np.cos(lat2r) * np.sin(dlon / 2.0) ** 2
    return 2.0 * radio * np.arcsin(np.sqrt(a))


@st.cache_data(show_spinner=False)
def extraer_gws_territorio(ruta_texto: str, lat_obj: float, lon_obj: float, radio_max_km: float = 120.0):
    """
    Extrae la serie del píxel válido más cercano.

    No usa simplemente ``method='nearest'`` porque algunos píxeles de borde del
    NetCDF están vacíos. También evita asignar a islas un píxel continental lejano.
    """
    if xr is None or np is None:
        raise ImportError("Faltan dependencias para leer el NetCDF.")

    ds = cargar_dataset_gws(ruta_texto)
    if "GWS_anom" not in ds.data_vars:
        raise KeyError("El NetCDF no contiene la variable GWS_anom.")

    da = ds["GWS_anom"]
    if not {"time", "lat", "lon"}.issubset(set(da.dims)):
        raise ValueError("GWS_anom no tiene las dimensiones esperadas: time, lat y lon.")

    latitudes = np.asarray(ds["lat"].values, dtype=float)
    longitudes = np.asarray(ds["lon"].values, dtype=float)
    lon_obj_norm = float(lon_obj)
    if np.nanmin(longitudes) >= 0 and lon_obj_norm < 0:
        lon_obj_norm = lon_obj_norm % 360

    validos = np.asarray(da.notnull().any(dim="time").values, dtype=bool)
    lat_grid, lon_grid = np.meshgrid(latitudes, longitudes, indexing="ij")
    distancias = distancia_haversine_km(lat_obj, lon_obj_norm, lat_grid, lon_grid)
    distancias = np.where(validos, distancias, np.inf)

    if not np.isfinite(distancias).any():
        return pd.DataFrame(), {"disponible": False, "motivo": "El archivo no contiene píxeles válidos."}

    indice = np.unravel_index(np.nanargmin(distancias), distancias.shape)
    i_lat, i_lon = int(indice[0]), int(indice[1])
    distancia_km = float(distancias[i_lat, i_lon])

    if distancia_km > radio_max_km:
        return pd.DataFrame(), {
            "disponible": False,
            "motivo": (
                f"El píxel válido más cercano está a {distancia_km:.0f} km. "
                "No se asigna porque sería una extrapolación espacial poco representativa."
            ),
            "distancia_km": distancia_km,
        }

    serie = da.isel(lat=i_lat, lon=i_lon)
    df = pd.DataFrame({
        "Fecha": pd.to_datetime(ds["time"].values),
        "GWSa (cm)": np.asarray(serie.values, dtype=float),
    }).dropna(subset=["GWSa (cm)"]).sort_values("Fecha").reset_index(drop=True)

    if df.empty:
        return df, {"disponible": False, "motivo": "La celda seleccionada no contiene observaciones válidas."}

    x_anios = (df["Fecha"] - df["Fecha"].min()).dt.total_seconds() / (365.25 * 24 * 3600)
    pendiente = float(np.polyfit(x_anios, df["GWSa (cm)"], 1)[0]) if len(df) >= 2 else float("nan")

    meta = {
        "disponible": True,
        "lat_pixel": float(latitudes[i_lat]),
        "lon_pixel": float(longitudes[i_lon]),
        "distancia_km": distancia_km,
        "fecha_inicial": df["Fecha"].min(),
        "fecha_final": df["Fecha"].max(),
        "registros": int(len(df)),
        "pendiente_cm_anio": pendiente,
    }
    return df, meta


def climatologia_gws(df: pd.DataFrame) -> pd.DataFrame:
    """Promedio multianual por mes de la GWSa extraída."""
    temporal = df.copy()
    temporal["Mes_num"] = temporal["Fecha"].dt.month
    salida = (
        temporal.groupby("Mes_num", as_index=False)["GWSa (cm)"]
        .mean()
        .sort_values("Mes_num")
    )
    salida["Mes"] = salida["Mes_num"].map(dict(enumerate(MESES, start=1)))
    return salida[["Mes_num", "Mes", "GWSa (cm)"]]


def calcular_ggdi(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Calcula el GRACE Groundwater Drought Index (GGDI) para la serie de una sede.

    Metodología implementada:
    1) climatología mensual de GWSa usando todos los años disponibles;
    2) GSD = GWSa observada - climatología del mismo mes;
    3) GGDI = GSD / desviación estándar de toda la serie GSD.

    El índice es adimensional. Valores positivos indican almacenamiento por encima
    de lo esperado para ese mes y valores negativos indican déficit relativo.
    """
    if np is None:
        raise ImportError("Falta NumPy para calcular GGDI.")
    if df is None or df.empty:
        return pd.DataFrame(), {"disponible": False, "motivo": "No hay datos GWSa."}

    temporal = df[["Fecha", "GWSa (cm)"]].copy()
    temporal["Fecha"] = pd.to_datetime(temporal["Fecha"], errors="coerce")
    temporal["GWSa (cm)"] = pd.to_numeric(temporal["GWSa (cm)"], errors="coerce")
    temporal = temporal.dropna(subset=["Fecha", "GWSa (cm)"]).sort_values("Fecha")

    if temporal.empty or temporal["Fecha"].dt.year.nunique() < 2:
        return pd.DataFrame(), {
            "disponible": False,
            "motivo": "Se requieren al menos dos años para construir una climatología mensual.",
        }

    temporal["Año"] = temporal["Fecha"].dt.year.astype(int)
    temporal["Mes_num"] = temporal["Fecha"].dt.month.astype(int)
    temporal["Mes"] = temporal["Mes_num"].map(dict(enumerate(MESES, start=1)))

    climatologia = (
        temporal.groupby("Mes_num")["GWSa (cm)"]
        .mean()
        .rename("GWSa climatológica (cm)")
    )
    temporal = temporal.join(climatologia, on="Mes_num")

    temporal["GSD (cm)"] = (
        temporal["GWSa (cm)"] - temporal["GWSa climatológica (cm)"]
    )

    sigma_gsd = float(temporal["GSD (cm)"].std(ddof=1))
    if not np.isfinite(sigma_gsd) or sigma_gsd <= 0:
        return pd.DataFrame(), {
            "disponible": False,
            "motivo": "La desviación estándar de GSD es nula o no válida.",
        }

    temporal["GGDI"] = temporal["GSD (cm)"] / sigma_gsd
    temporal["Condición GGDI"] = np.where(
        temporal["GGDI"] < 0,
        "Déficit respecto a lo normal del mes",
        np.where(
            temporal["GGDI"] > 0,
            "Por encima de lo normal del mes",
            "Condición mensual normal",
        ),
    )

    meta = {
        "disponible": True,
        "sigma_gsd_cm": sigma_gsd,
        "registros": int(len(temporal)),
        "anios": int(temporal["Año"].nunique()),
        "fecha_inicial": temporal["Fecha"].min(),
        "fecha_final": temporal["Fecha"].max(),
        "ggdi_min": float(temporal["GGDI"].min()),
        "ggdi_max": float(temporal["GGDI"].max()),
        "porcentaje_deficit": float((temporal["GGDI"] < 0).mean() * 100.0),
    }

    columnas = [
        "Fecha", "Año", "Mes_num", "Mes",
        "GWSa (cm)", "GWSa climatológica (cm)",
        "GSD (cm)", "GGDI", "Condición GGDI",
    ]
    return temporal[columnas].reset_index(drop=True), meta



# =========================================================
# ANÁLISIS DE TENDENCIAS · MANN-KENDALL + SEN
# =========================================================

VARIABLES_TENDENCIA = {
    "Precipitación": {
        "unidad": "mm",
        "agregacion": "sum",
        "aliases": [
            "precipitacion_mm_dia", "precipitacion", "precipitation",
            "prectotcorr", "prectot", "rainfall",
        ],
    },
    "Temperatura media": {
        "unidad": "°C",
        "agregacion": "mean",
        "aliases": ["temperatura_media_c", "temperatura_media", "t2m", "temperature_mean"],
    },
    "Temperatura máxima": {
        "unidad": "°C",
        "agregacion": "mean",
        "aliases": ["temperatura_maxima_c", "temperatura_maxima", "t2m_max", "t2mmax", "temperature_max"],
    },
    "Temperatura mínima": {
        "unidad": "°C",
        "agregacion": "mean",
        "aliases": ["temperatura_minima_c", "temperatura_minima", "t2m_min", "t2mmin", "temperature_min"],
    },
    "Humedad relativa": {
        "unidad": "%",
        "agregacion": "mean",
        "aliases": ["humedad_relativa_pct", "humedad_relativa", "rh2m", "relative_humidity"],
    },
    "Viento a 2 m": {
        "unidad": "m/s",
        "agregacion": "mean",
        "aliases": ["viento_2m_m_s", "viento_2m", "ws2m", "wind_speed_2m", "wind_speed"],
    },
    "Presión superficial": {
        "unidad": "kPa",
        "agregacion": "mean",
        "aliases": ["presion_superficie_kpa", "presion_superficie", "ps", "surface_pressure"],
    },
    "Radiación solar": {
        "unidad": "kWh/m²/día",
        "agregacion": "mean",
        "aliases": [
            "radiacion_solar_kwh_m2_dia", "radiacion_solar", "allsky_sfc_sw_dwn",
            "solar_radiation", "radiation",
        ],
    },
}


def normalizar_etiqueta(texto) -> str:
    """Normaliza nombres de columnas sin depender de tildes, espacios o símbolos."""
    base = unicodedata.normalize("NFKD", str(texto))
    base = "".join(c for c in base if not unicodedata.combining(c)).casefold()
    salida = []
    for c in base:
        salida.append(c if c.isalnum() else "_")
    return "_".join(parte for parte in "".join(salida).split("_") if parte)


def _fechas_desde_dataframe(df: pd.DataFrame):
    """Busca fecha directa o columnas YEAR/MO/DY en una hoja de cálculo."""
    mapa = {normalizar_etiqueta(c): c for c in df.columns}

    for alias in ("fecha", "date", "datetime", "time"):
        if alias in mapa:
            serie = df[mapa[alias]]
            if pd.api.types.is_numeric_dtype(serie):
                numeros = pd.to_numeric(serie, errors="coerce")
                mediana = numeros.dropna().median() if numeros.notna().any() else float("nan")
                if pd.notna(mediana) and 20000 <= mediana <= 60000:
                    return pd.Timestamp("1899-12-30") + pd.to_timedelta(numeros, unit="D")
            return pd.to_datetime(serie, errors="coerce")

    year_col = next((mapa[a] for a in ("year", "ano", "anio") if a in mapa), None)
    month_col = next((mapa[a] for a in ("mo", "month", "mes") if a in mapa), None)
    day_col = next((mapa[a] for a in ("dy", "day", "dia") if a in mapa), None)

    if year_col is not None and month_col is not None:
        anio = pd.to_numeric(df[year_col], errors="coerce")
        mes = pd.to_numeric(df[month_col], errors="coerce")
        dia = pd.to_numeric(df[day_col], errors="coerce") if day_col is not None else 1
        return pd.to_datetime(
            {"year": anio, "month": mes, "day": dia},
            errors="coerce",
        )
    return None


def _buscar_columna_variable(df: pd.DataFrame, aliases) -> str | None:
    """Encuentra una variable usando coincidencia exacta normalizada y luego parcial."""
    columnas = [(c, normalizar_etiqueta(c)) for c in df.columns]
    aliases_norm = [normalizar_etiqueta(a) for a in aliases]

    # Primero coincidencia exacta para evitar confundir T2M con T2M_MAX/T2M_MIN.
    for alias in aliases_norm:
        for original, norm in columnas:
            if norm == alias:
                return original

    # Después coincidencia contenida para nombres descriptivos más largos.
    for alias in aliases_norm:
        if len(alias) < 4:
            continue
        for original, norm in columnas:
            if alias in norm:
                return original
    return None


@st.cache_data(show_spinner=False)
def extraer_series_historicas_excel(ruta_texto: str):
    """
    Busca automáticamente series históricas dentro de un Excel procesado.

    Se ignoran hojas de climatología/regímenes porque sus 12 meses NO constituyen
    una serie temporal apropiada para Mann-Kendall. Se priorizan hojas con fechas
    reales o con columnas YEAR/MO/DY.
    """
    ruta = Path(ruta_texto)
    if not ruta.exists():
        return {}

    resultados = {}
    xls = pd.ExcelFile(ruta)
    excluir = ("regimen", "climatologia", "indicador", "control", "fuente", "resumen")

    for hoja in xls.sheet_names:
        hoja_norm = normalizar_etiqueta(hoja)
        if any(token in hoja_norm for token in excluir):
            continue
        try:
            df = pd.read_excel(ruta, sheet_name=hoja)
        except Exception:
            continue
        if df.empty or len(df.columns) < 2:
            continue

        fechas = _fechas_desde_dataframe(df)
        if fechas is None:
            continue
        fechas = pd.Series(fechas, index=df.index)
        validas = fechas.notna()
        if validas.sum() < 20:
            continue
        if fechas[validas].dt.year.nunique() < 3:
            continue

        for nombre, cfg in VARIABLES_TENDENCIA.items():
            columna = _buscar_columna_variable(df, cfg["aliases"])
            if columna is None:
                continue
            valores = pd.to_numeric(df[columna], errors="coerce")
            serie = pd.DataFrame({"Fecha": fechas, "Valor": valores}).dropna()
            serie = serie.sort_values("Fecha").drop_duplicates(subset=["Fecha"], keep="last")
            if len(serie) < 20 or serie["Fecha"].dt.year.nunique() < 3:
                continue

            actual = resultados.get(nombre)
            if actual is None or len(serie) > len(actual["serie"]):
                resultados[nombre] = {
                    "serie": serie.reset_index(drop=True),
                    "unidad": cfg["unidad"],
                    "agregacion": cfg["agregacion"],
                    "hoja": hoja,
                }
    return resultados


def agregar_serie_anual(serie: pd.DataFrame, agregacion: str) -> pd.DataFrame:
    """Agrega una serie a escala anual y elimina años claramente incompletos."""
    df = serie[["Fecha", "Valor"]].copy().dropna()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha", "Valor"])
    if df.empty:
        return pd.DataFrame(columns=["Año", "Valor", "N"])

    df["Año"] = df["Fecha"].dt.year
    conteos = df.groupby("Año")["Valor"].count()
    if conteos.empty:
        return pd.DataFrame(columns=["Año", "Valor", "N"])

    # El número típico de observaciones por año permite trabajar tanto con datos
    # diarios (~365) como mensuales (~12) sin fijar una frecuencia a mano.
    positivos = conteos[conteos > 0]
    esperado = float(positivos.median()) if not positivos.empty else 1.0
    umbral = max(1.0, 0.75 * esperado)
    anios_validos = conteos[conteos >= umbral].index
    df = df[df["Año"].isin(anios_validos)]

    if agregacion == "sum":
        valores = df.groupby("Año")["Valor"].sum(min_count=1)
    else:
        valores = df.groupby("Año")["Valor"].mean()
    n = df.groupby("Año")["Valor"].count()

    salida = pd.DataFrame({"Año": valores.index.astype(int), "Valor": valores.values, "N": n.values})
    return salida.dropna(subset=["Valor"]).sort_values("Año").reset_index(drop=True)


def mann_kendall(valores, alpha: float = 0.05) -> dict:
    """Prueba Mann-Kendall bilateral con corrección por empates, sin dependencias extra."""
    y = np.asarray(valores, dtype=float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < 5:
        raise ValueError("Mann-Kendall requiere al menos 5 observaciones válidas.")

    s = 0
    for i in range(n - 1):
        s += int(np.sign(y[i + 1:] - y[i]).sum())

    _, conteos = np.unique(y, return_counts=True)
    empates = conteos[conteos > 1]
    var_s = (
        n * (n - 1) * (2 * n + 5)
        - np.sum(empates * (empates - 1) * (2 * empates + 5))
    ) / 18.0

    if var_s <= 0:
        z = 0.0
    elif s > 0:
        z = (s - 1) / math.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s)
    else:
        z = 0.0

    # erfc entrega directamente la probabilidad bilateral de una normal estándar.
    p = math.erfc(abs(z) / math.sqrt(2.0))
    tau = s / (0.5 * n * (n - 1))
    significativa = p < alpha

    if significativa and tau > 0:
        tendencia = "Creciente significativa"
    elif significativa and tau < 0:
        tendencia = "Decreciente significativa"
    else:
        tendencia = "Sin tendencia significativa"

    return {
        "n": n,
        "S": float(s),
        "var_S": float(var_s),
        "Z": float(z),
        "p": float(p),
        "tau": float(tau),
        "significativa": bool(significativa),
        "tendencia": tendencia,
        "alpha": float(alpha),
    }


def pendiente_sen(anios, valores) -> dict:
    """Pendiente de Sen y ordenada robusta para una serie anual."""
    x = np.asarray(anios, dtype=float)
    y = np.asarray(valores, dtype=float)
    mascara = np.isfinite(x) & np.isfinite(y)
    x, y = x[mascara], y[mascara]
    if len(y) < 2:
        return {"pendiente": float("nan"), "intercepto": float("nan")}

    pendientes = []
    for i in range(len(y) - 1):
        dx = x[i + 1:] - x[i]
        validos = dx != 0
        if validos.any():
            pendientes.extend(((y[i + 1:][validos] - y[i]) / dx[validos]).tolist())

    if not pendientes:
        return {"pendiente": float("nan"), "intercepto": float("nan")}
    pendiente = float(np.median(pendientes))
    intercepto = float(np.median(y - pendiente * x))
    return {"pendiente": pendiente, "intercepto": intercepto}


def analizar_serie_tendencia(serie: pd.DataFrame, agregacion: str, alpha: float = 0.05):
    anual = agregar_serie_anual(serie, agregacion)
    if len(anual) < 5:
        return anual, None
    mk = mann_kendall(anual["Valor"].values, alpha=alpha)
    sen = pendiente_sen(anual["Año"].values, anual["Valor"].values)
    resultado = {**mk, **sen}
    return anual, resultado


def series_tendencia_territorio(nombre_territorio: str, info_territorio: dict):
    """Reúne todas las series históricas reales disponibles para el territorio."""
    disponibles = {}

    # 1) NASA POWER: conserva la serie histórica diaria en los Excel procesados.
    archivo_clima = archivo_nasa_territorio(nombre_territorio)
    if archivo_clima is not None and Path(archivo_clima).exists():
        try:
            clima = extraer_series_historicas_excel(str(archivo_clima))
            for variable, paquete in clima.items():
                disponibles[variable] = {
                    **paquete,
                    "fuente": "NASA POWER",
                    "archivo": Path(archivo_clima).name,
                }
        except Exception:
            pass

    # 2) IDEAM: se intenta priorizar cuando el Excel conserva series históricas completas.
    # El archivo compacto de Arauca puede no incluir hojas diarias; en ese caso NASA se mantiene.
    archivo_ideam = ARCHIVOS_IDEAM.get(nombre_territorio)
    if archivo_ideam is not None and Path(archivo_ideam).exists():
        try:
            ideam = extraer_series_historicas_excel(str(archivo_ideam))
            for variable in (
                "Precipitación", "Temperatura media", "Temperatura máxima",
                "Temperatura mínima", "Humedad relativa"
            ):
                if variable in ideam:
                    disponibles[variable] = {
                        **ideam[variable],
                        "fuente": "IDEAM",
                        "archivo": Path(archivo_ideam).name,
                    }
        except Exception:
            pass

    # 3) GWSa GRACE/GLDAS.
    if ARCHIVO_GWS is not None and xr is not None and np is not None:
        try:
            df_gws, meta = extraer_gws_territorio(
                str(ARCHIVO_GWS), info_territorio["lat"], info_territorio["lon"]
            )
            if meta.get("disponible", False) and not df_gws.empty:
                disponibles["GWSa"] = {
                    "serie": df_gws.rename(columns={"GWSa (cm)": "Valor"})[["Fecha", "Valor"]],
                    "unidad": "cm",
                    "agregacion": "mean",
                    "fuente": "GRACE/GRACE-FO + GLDAS",
                    "archivo": Path(ARCHIVO_GWS).name,
                    "hoja": "NetCDF",
                }
        except Exception:
            pass

    return disponibles

# =========================================================
# FUNCIONES
# =========================================================


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

# =========================================================
# IMPORT DE SEGURIDAD PARA RUTAS
# =========================================================
# Se repite aquí intencionalmente para evitar NameError si
# al copiar/reemplazar el archivo se pierde la primera línea.
from pathlib import Path

def archivo_disponible(ruta) -> str:
    return "Disponible" if ruta is not None and Path(ruta).exists() else "No encontrado"

# Nombres de las imágenes tal como aparecen en tu carpeta.
# No es necesario escribir la extensión: el código prueba PNG, JPG, JPEG y WEBP.
MAPAS_LETICIA = {
    "cobertura": "mapa_coberturas_leticia",
    "geologia": "mapa_geologia_trapecio_sur",
    "relieve": "mapa_geomorfologia_relieve_leticia",
    "hidrografia": "mapa_hidrografia_leticia",
    "humedales": "mapa_humedales_leticia_puerto_narino",
    "inundacion": "mapa_inundacion_urbana_leticia",
    "pozos_irca": "mapa_pozos_irca_leticia",
}

MAPAS_TUMACO = {
    "cobertura": "mapa_coberturas_tumaco",
    "geologia": "mapa_geologia_tumaco",
    "relieve": "mapa_relieve_tumaco",
    "hidrografia": "mapa_hidrografia_tumaco",
    "manglares": "mapa_manglares_tumaco",
    "inundacion": "mapa_inundacion_tumaco",
}

MAPAS_MEDELLIN = {
    "geologia": "mapa_geologia_medellin_plancha_228",
    "estructura_ecologica": "mapa_estructura_ecologica_medellin",
    "inundacion": "mapa_amenaza_inundacion_medellin",
}

MAPAS_SAN_ANDRES = {
    "geologia": "mapa_geologia_san_andres",
    "vulnerabilidad_acuifero": "mapa_vulnerabilidad_acuifero_san_andres",
    "nitratos": "mapa_nitratos_aguas_subterraneas_san_andres",
    "microcuencas": "mapa_microcuencas_arroyos_san_andres",
}

MAPAS_ARAUCA = {
    "demanda_industria": "mapa_demanda_agua_industria_manufacturera_arauca_2021",
    "vertimientos_industria": "mapa_vertimientos_industria_manufacturera_arauca_2021",
    "anomalia_oferta_alta": "mapa_anomalia_oferta_hidrica_superficial_arauca_ena2014",
    "puntos_agua_subterranea": "mapa_puntos_agua_subterranea_arauca_ena2014",
    "volumen_concesionado": "mapa_volumen_agua_subterranea_concesionada_arauca_ena2014",
    "criterio_hidrogeologico": "mapa_criterio_demanda_hidrogeologico_arauca_pexas_2005",
    "geologia": "mapa_geologico_colombia_2023_arauca",
    "sistema_acuifero": "mapa_sistema_acuifero_arauca_arauquita",
}

# Mapas QGIS de ubicación multiescala.
# Los nombres se dejan como aparecen en la carpeta ``Mapas Qgis``.
MAPAS_BOGOTA = {
    "ubicacion_colombia": "Bogotá 1-10000000.pdf",
    "ubicacion_region": "Bogotá 1- 1500000.pdf",
    "ubicacion_campus": "Bogotá 1- 10000.pdf",
}

MAPAS_UBICACION_QGIS = {
    "Bogotá": [
        {
            "paso": "Colombia",
            "archivo": "Bogotá 1-10000000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Bogotá D.C. dentro del contexto nacional.",
            "escala": "1:10.000.000",
        },
        {
            "paso": "Bogotá",
            "archivo": "Bogotá 1- 1500000.pdf",
            "titulo": "Nivel 2 · Bogotá y contexto regional",
            "detalle": "Acercamiento al Distrito Capital y su entorno regional.",
            "escala": "1:1.500.000",
        },
        {
            "paso": "Campus",
            "archivo": "Bogotá 1- 10000.pdf",
            "titulo": "Nivel 3 · Campus Ciudad Universitaria",
            "detalle": "Detalle de la Sede Bogotá y su entorno inmediato.",
            "escala": "1:10.000",
        },
    ],
    "Arauca": [
        {
            "paso": "Colombia",
            "archivo": "Arauca 1-10000000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Arauca dentro del contexto nacional.",
            "escala": "1:10.000.000",
        },
        {
            "paso": "Arauca",
            "archivo": "Arauca 1-1500000.pdf",
            "titulo": "Nivel 2 · Arauca y contexto regional",
            "detalle": "Acercamiento regional al territorio de la Sede Orinoquía.",
            "escala": "1:1.500.000",
        },
        {
            "paso": "Sede",
            "archivo": "Arauca 1-1500.pdf",
            "titulo": "Nivel 3 · Entorno de la Sede Orinoquía",
            "detalle": "Detalle cartográfico del entorno inmediato de la sede.",
            "escala": "1:1.500",
        },
    ],
    "Medellín": [
        {
            "paso": "Colombia",
            "archivo": "Medellín 1-10000000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Medellín dentro del contexto nacional.",
            "escala": "1:10.000.000",
        },
        {
            "paso": "Medellín",
            "archivo": "Medellín 1-250000.pdf",
            "titulo": "Nivel 2 · Medellín y contexto regional",
            "detalle": "Acercamiento al Valle de Aburrá y al entorno urbano de Medellín.",
            "escala": "1:250.000",
        },
        {
            "paso": "Sede",
            "archivo": "Medellín 1-5000.pdf",
            "titulo": "Nivel 3 · Entorno de la Sede Medellín",
            "detalle": "Detalle cartográfico del entorno inmediato de la sede.",
            "escala": "1:5.000",
        },
    ],
    "San Andrés": [
        {
            "paso": "Colombia",
            "archivo": "San Andrés 1 - 10000000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación del archipiélago de San Andrés en el contexto nacional.",
            "escala": "1:10.000.000",
        },
        {
            "paso": "Isla",
            "archivo": "San Andrés 1 - 75000.pdf",
            "titulo": "Nivel 2 · Isla de San Andrés",
            "detalle": "Aproximación cartográfica al entorno insular de San Andrés.",
            "escala": "1:75.000",
        },
    ],
    "Tumaco": [
        {
            "paso": "Colombia",
            "archivo": "Tumaco 1 - 10000000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Tumaco dentro del contexto nacional.",
            "escala": "1:10.000.000",
        },
        {
            "paso": "Región",
            "archivo": "Tumaco 1 - 1500000.pdf",
            "titulo": "Nivel 2 · Pacífico nariñense",
            "detalle": "Contexto regional del territorio de Tumaco y la costa pacífica de Nariño.",
            "escala": "1:1.500.000",
        },
        {
            "paso": "Sede",
            "archivo": "Tumaco 1- 1500.pdf",
            "titulo": "Nivel 3 · Entorno de la Sede Tumaco",
            "detalle": "Detalle cartográfico de la Sede Tumaco y su entorno inmediato.",
            "escala": "1:1.500",
        },
    ],
    "Leticia": [
        {
            "paso": "Colombia",
            "archivo": "Leticia 1-8250000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Leticia dentro del territorio nacional.",
            "escala": "1:8.250.000",
        },
        {
            "paso": "Amazonas",
            "archivo": "Leticia 1-5300000.pdf",
            "titulo": "Nivel 2 · Contexto amazónico",
            "detalle": "Aproximación territorial intermedia presentada en la cartografía QGIS.",
            "escala": "1:5.300.000",
        },
        {
            "paso": "Sede",
            "archivo": "Leticia 1-1400.pdf",
            "titulo": "Nivel 3 · Entorno de la Sede Amazonia",
            "detalle": "Ubicación de detalle del entorno inmediato de la sede.",
            "escala": "1:1.400",
        },
    ],
    "La Paz": [
        {
            "paso": "Colombia",
            "archivo": "La Paz 1-7500000.pdf",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de La Paz, Cesar, dentro del territorio nacional.",
            "escala": "1:7.500.000",
        },
        {
            "paso": "Cesar",
            "archivo": "La Paz 1-2750000.pdf",
            "titulo": "Nivel 2 · La Paz y contexto regional",
            "detalle": "Aproximación regional al territorio de La Paz.",
            "escala": "1:2.750.000",
        },
        {
            "paso": "Sede",
            "archivo": "La Paz 1-3000.pdf",
            "titulo": "Nivel 3 · Entorno de la Sede de La Paz",
            "detalle": "Detalle cartográfico del entorno inmediato de la sede.",
            "escala": "1:3.000",
        },
    ],
}


# Información de referencia del proyecto QGIS mostrado en las capturas.
# NO equivale a certificar el SRC interno ni las fuentes de TODOS los PDF.
# Ajustar estos campos si los layouts cartográficos usan otro SRC o fuentes.
FICHA_QGIS_REFERENCIA = {
    "src": "MAGNA-SIRGAS 2018 / Origen-Nacional (EPSG:9377)",
    "proyeccion": "Transversa de Mercator",
    "unidades": "Metros",
    "fuentes": "OpenStreetMap (2024) · Esri World Imagery (2023)",
    "elaboracion": "Semillero SIAMS · Cartografía académica elaborada en QGIS",
    "fecha": "2026",
}



MAPAS_POR_TERRITORIO = {
    "Bogotá": MAPAS_BOGOTA,
    "Leticia": MAPAS_LETICIA,
    "Tumaco": MAPAS_TUMACO,
    "Medellín": MAPAS_MEDELLIN,
    "San Andrés": MAPAS_SAN_ANDRES,
    "Arauca": MAPAS_ARAUCA,
    "La Paz": {},
}


def encontrar_carpeta_mapas() -> Path:
    """Devuelve la carpeta principal de mapas temáticos.

    Los mapas antiguos del proyecto están dentro de ``SIAMS MAPAS``.
    Los PDF del piloto de Bogotá pueden estar directamente junto a ``app.py``.
    El buscador de mapas revisa ambas ubicaciones para mantener compatibilidad.
    """
    carpeta_codigo = Path(__file__).resolve().parent
    carpeta_siams = carpeta_codigo / "SIAMS MAPAS"

    if carpeta_siams.exists() and carpeta_siams.is_dir():
        return carpeta_siams

    return carpeta_codigo


CARPETA_PROYECTO = Path(__file__).resolve().parent
CARPETA_DATOS_HIDRO = CARPETA_PROYECTO / "Analisis Hidro"
CARPETA_MAPAS_QGIS = CARPETA_PROYECTO / "Mapas Qgis"
CARPETA_MAPAS = encontrar_carpeta_mapas()

# =========================================================
# ANIMACIONES SWOT · GIF
# =========================================================
# Los GIF se guardan en una carpeta llamada ``Gif`` al mismo nivel de app.py.
CARPETA_GIFS = CARPETA_PROYECTO / "Gif"

GIFS_SWOT_POR_TERRITORIO = {
    "Leticia": [
        {
            "titulo": "Río Amazonas · variación temporal del ancho",
            "archivo": "R_o_Amazonas_Leticia_SWOT_Ancho.gif",
            "descripcion": "Animación temporal del ancho observado por SWOT en reaches seleccionados del río Amazonas.",
        },
    ],
    "Tumaco": [
        {
            "titulo": "Río Rosario · variación temporal del ancho",
            "archivo": "R_o_Rosario_Tumaco_SWOT_Ancho.gif",
            "descripcion": "Animación temporal del ancho observado por SWOT en reaches seleccionados del río Rosario.",
        },
        {
            "titulo": "Río Mira · variación temporal del ancho",
            "archivo": "R_o_Mira_Tumaco_SWOT_Ancho.gif",
            "descripcion": "Animación temporal del ancho observado por SWOT en reaches seleccionados del río Mira.",
        },
    ],
    "Medellín": [
        {
            "titulo": "Río Medellín · variación temporal del ancho",
            "archivo": "R_o_Medell_n_Medell_n_SWOT_Ancho.gif",
            "descripcion": "Animación temporal del ancho observado por SWOT en reaches seleccionados del río Medellín.",
        },
    ],
    "Arauca": [
        {
            "titulo": "Río Arauca · variación temporal del ancho",
            "archivo": "Rio_Arauca_SWOT_Profesional.gif",
            "descripcion": "Animación temporal del ancho observado por SWOT en reaches seleccionados del río Arauca.",
        },
    ],
}


def buscar_gif_swot(nombre_archivo: str):
    """Localiza un GIF SWOT dentro de la carpeta ``Gif``.

    Primero usa el nombre exacto configurado y luego intenta una coincidencia
    tolerante a mayúsculas/minúsculas para evitar errores simples al subir archivos.
    """
    if not CARPETA_GIFS.exists() or not CARPETA_GIFS.is_dir():
        return None

    ruta_directa = CARPETA_GIFS / nombre_archivo
    if ruta_directa.exists() and ruta_directa.is_file():
        return ruta_directa

    objetivo = Path(nombre_archivo).name.casefold()
    for archivo in CARPETA_GIFS.iterdir():
        if archivo.is_file() and archivo.suffix.casefold() == ".gif":
            if archivo.name.casefold() == objetivo:
                return archivo
    return None


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
                    f"No se encontró `{item['archivo']}` dentro de la carpeta `Gif`."
                )
                st.caption(f"Ruta esperada: {CARPETA_GIFS / item['archivo']}")
                continue

            st.markdown(f"### {item['titulo']}")
            st.image(
                str(ruta),
                caption=f"{item['descripcion']} · Fuente: HydroWeb / SWOT",
                use_container_width=True,
            )
            st.caption(f"Archivo: Gif/{ruta.name}")

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


# =========================================================
# TARJETAS TÉCNICAS SWOT · PNG
# =========================================================
# Las tarjetas se guardan en una carpeta llamada exactamente
# ``Tarjeta Tecnica Swot`` al mismo nivel de app.py.
CARPETA_TARJETAS_SWOT = CARPETA_PROYECTO / "Tarjeta Tecnica Swot"

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


def buscar_tarjeta_swot(nombre_archivo: str):
    """Localiza una tarjeta técnica SWOT dentro de ``Tarjeta Tecnica Swot``.

    Además del nombre exacto, compara el nombre normalizado para tolerar diferencias
    menores de mayúsculas, tildes, guiones bajos y espacios.
    """
    if not CARPETA_TARJETAS_SWOT.exists() or not CARPETA_TARJETAS_SWOT.is_dir():
        return None

    ruta_directa = CARPETA_TARJETAS_SWOT / nombre_archivo
    if ruta_directa.exists() and ruta_directa.is_file():
        return ruta_directa

    objetivo = normalizar_etiqueta(Path(nombre_archivo).stem)
    for archivo in CARPETA_TARJETAS_SWOT.iterdir():
        if not archivo.is_file() or archivo.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        if normalizar_etiqueta(archivo.stem) == objetivo:
            return archivo
    return None


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
                    f"No se encontró `{nombre_archivo}` dentro de `Tarjeta Tecnica Swot`."
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
            st.caption(f"Archivo: Tarjeta Tecnica Swot/{ruta.name}")


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

# Cartografía temática, PDF de QGIS y compatibilidad con archivos en la raíz.
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


# =========================================================
# ARCHIVO CLIMÁTICO DE LETICIA
# =========================================================

def encontrar_archivo_excel(prefijos, nombres_preferidos, subcarpetas):
    """Busca primero en Analisis Hidro y después en las ubicaciones anteriores."""
    carpetas = []
    for carpeta in (
        CARPETA_DATOS_HIDRO,
        CARPETA_PROYECTO,
        *(CARPETA_PROYECTO / sub for sub in subcarpetas),
    ):
        if carpeta.is_dir() and carpeta not in carpetas:
            carpetas.append(carpeta)

    # Los nombres completos tienen prioridad sobre copias con (1), (2), etc.
    # Se ignoran tildes y mayúsculas, sin modificar los archivos originales.
    for carpeta in carpetas:
        archivos = sorted(
            (archivo for archivo in carpeta.iterdir()
             if archivo.is_file() and archivo.suffix.casefold() == ".xlsx"
             and not archivo.name.startswith("~$")),
            key=lambda archivo: archivo.name.casefold(),
        )
        for nombre in nombres_preferidos:
            objetivo = normalizar_etiqueta(nombre)
            for archivo in archivos:
                if normalizar_etiqueta(archivo.name) == objetivo:
                    return archivo
        for prefijo in prefijos:
            objetivo = normalizar_etiqueta(prefijo)
            for archivo in archivos:
                stem = normalizar_etiqueta(archivo.stem)
                if stem == objetivo or stem.startswith(objetivo + "_"):
                    return archivo
    return None


def encontrar_archivo_clima_leticia():
    """Localiza NASA POWER de Leticia en la carpeta de análisis hidrológico."""
    return encontrar_archivo_excel(
        prefijos=["NASA_POWER_LETICIA"],
        nombres_preferidos=[
            "NASA_POWER_LETICIA_FINAL.xlsx",
            "NASA_POWER_LETICIA_FINAL (3).xlsx",
        ],
        subcarpetas=["DATOS CLIMA", "datos", "datos/leticia", "datos/leticia/clima"],
    )


ARCHIVO_CLIMA_LETICIA = encontrar_archivo_clima_leticia()


def convertir_fecha_excel(valor):
    """Convierte fechas de texto, datetime o serial real de Excel."""
    if valor is None or pd.isna(valor):
        return None

    if isinstance(valor, pd.Timestamp):
        return valor

    # Los seriales de Excel suelen estar entre 20.000 y 60.000 para fechas modernas.
    if pd.api.types.is_number(valor):
        numero = float(valor)
        if 20000 <= numero <= 60000:
            return pd.Timestamp("1899-12-30") + pd.to_timedelta(numero, unit="D")

    fecha = pd.to_datetime(valor, errors="coerce")
    if pd.notna(fecha):
        return pd.Timestamp(fecha)
    return None


@st.cache_data(show_spinner=False)
def cargar_clima_leticia(ruta_texto: str):
    """Lee los regímenes mensuales y los indicadores del Excel procesado."""
    ruta = Path(ruta_texto)

    p = pd.read_excel(ruta, sheet_name="Regimen_P")
    t = pd.read_excel(ruta, sheet_name="Regimen_T")
    hr = pd.read_excel(ruta, sheet_name="Regimen_HR")
    clim = pd.read_excel(ruta, sheet_name="Climatologia_mensual")
    indicadores_df = pd.read_excel(ruta, sheet_name="Indicadores")

    # Regimen_P contiene el total mensual climatológico, aunque la columna
    # conserve el nombre original de la variable diaria.
    p = p.rename(columns={"precipitacion_mm_dia": "Precipitación mensual (mm)"})
    t = t.rename(columns={
        "temperatura_media_C": "Temperatura media (°C)",
        "temperatura_maxima_C": "Temperatura máxima (°C)",
        "temperatura_minima_C": "Temperatura mínima (°C)",
    })
    hr = hr.rename(columns={"humedad_relativa_pct": "Humedad relativa (%)"})

    otras = clim[[
        "mes",
        "viento_2m_m_s",
        "presion_superficie_kPa",
        "radiacion_solar_kWh_m2_dia",
    ]].rename(columns={
        "viento_2m_m_s": "Viento a 2 m (m/s)",
        "presion_superficie_kPa": "Presión superficial (kPa)",
        "radiacion_solar_kWh_m2_dia": "Radiación solar (kWh/m²/día)",
    })

    df = p.merge(t, on="mes", how="inner")
    df = df.merge(hr, on="mes", how="inner")
    df = df.merge(otras, on="mes", how="inner")
    df = df.sort_values("mes").reset_index(drop=True)
    df["Mes"] = df["mes"].map(dict(enumerate(MESES, start=1)))
    df = df.drop(columns="mes")

    columnas = [
        "Mes",
        "Precipitación mensual (mm)",
        "Temperatura media (°C)",
        "Temperatura máxima (°C)",
        "Temperatura mínima (°C)",
        "Humedad relativa (%)",
        "Viento a 2 m (m/s)",
        "Presión superficial (kPa)",
        "Radiación solar (kWh/m²/día)",
    ]
    df = df[columnas]

    indicadores = dict(
        zip(indicadores_df["Indicador"].astype(str), indicadores_df["Valor"])
    )

    for clave in ("Fecha inicial", "Fecha final"):
        if clave in indicadores:
            indicadores[clave] = convertir_fecha_excel(indicadores[clave])

    return df, indicadores


# =========================================================
# ARCHIVOS CLIMÁTICOS DE TUMACO: NASA POWER + IDEAM
# =========================================================

ARCHIVO_NASA_TUMACO = encontrar_archivo_excel(
    prefijos=["NASA_POWER_TUMACO"],
    nombres_preferidos=[
        "NASA_POWER_TUMACO_FINAL.xlsx",
        "NASA_POWER_TUMACO_FINAL (3).xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA",
        "datos",
        "datos/tumaco",
        "datos/tumaco/clima",
    ],
)

ARCHIVO_IDEAM_TUMACO = encontrar_archivo_excel(
    prefijos=["ANALISIS_HIDROMETEOROLOGICO_Tumaco", "ANALISIS_HIDROMETEOROLOGICO_TUMACO"],
    nombres_preferidos=[
        "ANALISIS_HIDROMETEOROLOGICO_Tumaco.xlsx",
        "ANALISIS_HIDROMETEOROLOGICO_Tumaco (2).xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA",
        "datos",
        "datos/tumaco",
        "datos/tumaco/clima",
    ],
)

ARCHIVO_IDEAM_ARAUCA = encontrar_archivo_excel(
    prefijos=["ANALISIS_HIDROMETEOROLOGICO_Arauca", "ANALISIS_HIDROMETEOROLOGICO_ARAUCA"],
    nombres_preferidos=[
        "ANALISIS_HIDROMETEOROLOGICO_Arauca.xlsx",
        "ANALISIS_HIDROMETEOROLOGICO_ARAUCA.xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA",
        "datos",
        "datos/arauca",
        "datos/arauca/clima",
    ],
)


ARCHIVO_CLIMA_MEDELLIN = encontrar_archivo_excel(
    prefijos=[
        "NASA_POWER_MEDELLÍN",
        "NASA_POWER_MEDELLIN",
        "NASA_POWER_Medellín",
        "NASA_POWER_Medellin",
    ],
    nombres_preferidos=[
        "NASA_POWER_MEDELLÍN_FINAL.xlsx",
        "NASA_POWER_MEDELLIN_FINAL.xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA",
        "datos",
        "datos/medellin",
        "datos/medellin/clima",
        "datos/medellín",
        "datos/medellín/clima",
    ],
)

ARCHIVO_CLIMA_SAN_ANDRES = encontrar_archivo_excel(
    prefijos=[
        "NASA_POWER_SAN_ANDRES",
        "NASA_POWER_SAN ANDRES",
        "NASA_POWER_SAN_ANDRÉS",
    ],
    nombres_preferidos=[
        "NASA_POWER_SAN_ANDRES_FINAL.xlsx",
        "NASA_POWER_SAN_ANDRÉS_FINAL.xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA",
        "datos",
        "datos/san_andres",
        "datos/san_andres/clima",
        "datos/san andres",
        "datos/san andres/clima",
    ],
)

ARCHIVO_CLIMA_ARAUCA = encontrar_archivo_excel(
    prefijos=["NASA_POWER_ARAUCA"],
    nombres_preferidos=[
        "NASA_POWER_ARAUCA_FINAL.xlsx",
        "NASA_POWER_ARAUCA_FINAL (1).xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA", "datos", "datos/arauca", "datos/arauca/clima",
    ],
)

ARCHIVO_CLIMA_LA_PAZ = encontrar_archivo_excel(
    prefijos=["NASA_POWER_LA_PAZ", "NASA_POWER_LAPAZ", "NASA_POWER_LA PAZ"],
    nombres_preferidos=[
        "NASA_POWER_LA_PAZ_FINAL.xlsx",
        "NASA_POWER_LAPAZ_FINAL.xlsx",
    ],
    subcarpetas=[
        "DATOS CLIMA", "datos", "datos/la_paz", "datos/la_paz/clima",
        "datos/la paz", "datos/la paz/clima",
    ],
)

ARCHIVOS_CLIMA_NASA = {
    "Bogotá": None,
    "Leticia": ARCHIVO_CLIMA_LETICIA,
    "Medellín": ARCHIVO_CLIMA_MEDELLIN,
    "San Andrés": ARCHIVO_CLIMA_SAN_ANDRES,
    "Arauca": ARCHIVO_CLIMA_ARAUCA,
    "La Paz": ARCHIVO_CLIMA_LA_PAZ,
}

# Alias de compatibilidad para la sección de comparación.
ARCHIVOS_NASA = ARCHIVOS_CLIMA_NASA

# IDEAM procesado disponible por territorio. La Paz queda deliberadamente solo con NASA POWER.
ARCHIVOS_IDEAM = {
    "Tumaco": ARCHIVO_IDEAM_TUMACO,
    "Arauca": ARCHIVO_IDEAM_ARAUCA,
}

def archivo_nasa_territorio(nombre_territorio: str):
    """Devuelve el Excel NASA POWER asociado a cada territorio."""
    if nombre_territorio == "Tumaco":
        return ARCHIVO_NASA_TUMACO
    return ARCHIVOS_CLIMA_NASA.get(nombre_territorio)


@st.cache_data(show_spinner=False)
def cargar_nasa_tumaco(ruta_texto: str):
    """Lee la climatología mensual y los indicadores NASA POWER de Tumaco."""
    ruta = Path(ruta_texto)

    p = pd.read_excel(ruta, sheet_name="Regimen_P").rename(
        columns={"precipitacion_mm_dia": "Precipitación NASA (mm)"}
    )
    t = pd.read_excel(ruta, sheet_name="Regimen_T").rename(columns={
        "temperatura_media_C": "Temperatura media NASA (°C)",
        "temperatura_maxima_C": "Temperatura máxima NASA (°C)",
        "temperatura_minima_C": "Temperatura mínima NASA (°C)",
    })
    hr = pd.read_excel(ruta, sheet_name="Regimen_HR").rename(
        columns={"humedad_relativa_pct": "Humedad NASA (%)"}
    )
    clim = pd.read_excel(ruta, sheet_name="Climatologia_mensual")
    indicadores_df = pd.read_excel(ruta, sheet_name="Indicadores")

    otras = clim[[
        "mes",
        "viento_2m_m_s",
        "presion_superficie_kPa",
        "radiacion_solar_kWh_m2_dia",
    ]].rename(columns={
        "viento_2m_m_s": "Viento a 2 m NASA (m/s)",
        "presion_superficie_kPa": "Presión NASA (kPa)",
        "radiacion_solar_kWh_m2_dia": "Radiación NASA (kWh/m²/día)",
    })

    df = p.merge(t, on="mes", how="inner")
    df = df.merge(hr, on="mes", how="inner")
    df = df.merge(otras, on="mes", how="inner")
    df = df.sort_values("mes").reset_index(drop=True)
    df["Mes"] = df["mes"].map(dict(enumerate(MESES, start=1)))
    df = df.drop(columns="mes")

    indicadores = dict(zip(
        indicadores_df["Indicador"].astype(str),
        indicadores_df["Valor"],
    ))
    for clave in ("Fecha inicial", "Fecha final"):
        if clave in indicadores:
            indicadores[clave] = convertir_fecha_excel(indicadores[clave])

    return df, indicadores


@st.cache_data(show_spinner=False)
def cargar_ideam_tumaco(ruta_texto: str):
    """Lee climatología, fuentes y control de calidad del archivo IDEAM de Tumaco."""
    ruta = Path(ruta_texto)

    clim = pd.read_excel(ruta, sheet_name="Climatologia").rename(columns={
        "Precipitacion_media_mensual": "Precipitación IDEAM (mm)",
        "Temperatura_media": "Temperatura media IDEAM (°C)",
        "Temperatura_maxima": "Temperatura máxima IDEAM (°C)",
        "Temperatura_minima": "Temperatura mínima IDEAM (°C)",
        "Humedad_relativa": "Humedad IDEAM (%)",
    })
    clim = clim[[
        "mes",
        "Mes",
        "Precipitación IDEAM (mm)",
        "Temperatura media IDEAM (°C)",
        "Temperatura máxima IDEAM (°C)",
        "Temperatura mínima IDEAM (°C)",
        "Humedad IDEAM (%)",
    ]].sort_values("mes").reset_index(drop=True)
    clim["Mes"] = clim["mes"].map(dict(enumerate(MESES, start=1)))
    clim = clim.drop(columns="mes")

    indicadores_df = pd.read_excel(ruta, sheet_name="Indicadores")
    control = pd.read_excel(ruta, sheet_name="Control_faltantes")
    fuentes = pd.read_excel(ruta, sheet_name="Fuentes")

    indicadores = dict(zip(
        indicadores_df["Indicador"].astype(str),
        indicadores_df["Valor"],
    ))
    for clave in ("Fecha inicial global", "Fecha final global"):
        if clave in indicadores:
            indicadores[clave] = convertir_fecha_excel(indicadores[clave])

    for columna in ("Fecha inicial", "Fecha final"):
        if columna in control.columns:
            control[columna] = control[columna].apply(convertir_fecha_excel)
    for columna in ("Fecha_inicial", "Fecha_final"):
        if columna in fuentes.columns:
            fuentes[columna] = fuentes[columna].apply(convertir_fecha_excel)

    return clim, indicadores, control, fuentes


def decisiones_climaticas_ideam(control: pd.DataFrame, nombre_territorio: str) -> pd.DataFrame:
    """Decisión de uso por variable para territorios con IDEAM + NASA POWER."""
    completitud = {}
    if control is not None and not control.empty:
        for _, fila in control.iterrows():
            completitud[str(fila.get("Variable", ""))] = fila.get("Completitud [%]")

    def pct(clave):
        valor = completitud.get(clave)
        return f"{float(valor):.2f} %" if pd.notna(valor) else "—"

    if nombre_territorio == "Arauca":
        fuente_principal = [
            "IDEAM",
            "IDEAM derivada",
            "IDEAM",
            "IDEAM",
            "IDEAM con advertencia",
            "NASA POWER",
            "NASA POWER",
            "NASA POWER",
        ]
        uso_otra = [
            "NASA POWER para comparación; no reemplaza la lluvia observada",
            "NASA POWER como contraste continuo; Tmedia IDEAM = (Tmax + Tmin) / 2",
            "NASA POWER como comparación",
            "NASA POWER como comparación",
            "NASA POWER como contraste; validar la HR mínima inferida antes de publicación definitiva",
            "IDEAM no disponible en el archivo procesado",
            "IDEAM no disponible en el archivo procesado",
            "IDEAM no disponible en el archivo procesado",
        ]
    else:
        fuente_principal = [
            "IDEAM",
            "IDEAM",
            "IDEAM con cautela",
            "IDEAM con cautela",
            "NASA POWER + contraste IDEAM",
            "NASA POWER",
            "NASA POWER",
            "NASA POWER",
        ]
        uso_otra = [
            "NASA POWER para comparación; no reemplaza la lluvia observada",
            "NASA POWER como serie continua complementaria",
            "NASA POWER como apoyo por faltantes IDEAM",
            "NASA POWER como apoyo por faltantes IDEAM",
            "IDEAM como observación local parcial",
            "Sin contraste IDEAM en el archivo",
            "Sin contraste IDEAM en el archivo",
            "Sin contraste IDEAM en el archivo",
        ]

    return pd.DataFrame({
        "Variable": [
            "Precipitación", "Temperatura media", "Temperatura máxima",
            "Temperatura mínima", "Humedad relativa", "Viento", "Presión", "Radiación",
        ],
        "Completitud IDEAM": [
            pct("precipitacion"), pct("temperatura_media"), pct("temperatura_maxima"),
            pct("temperatura_minima"), pct("humedad_relativa"),
            "No disponible", "No disponible", "No disponible",
        ],
        "Fuente principal": fuente_principal,
        "Uso de la otra fuente": uso_otra,
    })


def decisiones_climaticas_tumaco(control: pd.DataFrame) -> pd.DataFrame:
    return decisiones_climaticas_ideam(control, "Tumaco")

def periodo_texto(inicio, fin):
    if hasattr(inicio, "strftime") and hasattr(fin, "strftime"):
        return f"{inicio:%Y-%m-%d} a {fin:%Y-%m-%d}"
    return "—"


def clima_prototipo(info: dict) -> pd.DataFrame:
    """Respaldo para territorios que todavía no tienen Excel procesado."""
    return pd.DataFrame({
        "Mes": MESES,
        "Precipitación mensual (mm)": info["precipitacion"],
        "Temperatura media (°C)": info["temperatura"],
        "Humedad relativa (%)": info["humedad"],
    })


def buscar_mapa(nombre_base: str):
    """Busca los mapas donde estaban y los PDF de Bogotá en Mapas Qgis."""
    objetivo = Path(nombre_base).name.casefold()
    objetivo_stem = Path(nombre_base).stem.casefold()

    for carpeta in CARPETAS_BUSQUEDA_MAPAS:
        if not carpeta.exists() or not carpeta.is_dir():
            continue

        # Nombre completo, útil cuando nombre_base ya incluye .pdf/.png.
        ruta_directa = carpeta / nombre_base
        if ruta_directa.exists() and ruta_directa.is_file():
            return ruta_directa

        # Nombre base sin extensión.
        for extension in EXTENSIONES_MAPA:
            ruta = carpeta / f"{nombre_base}{extension}"
            if ruta.exists() and ruta.is_file():
                return ruta

        # Coincidencia tolerante a mayúsculas/minúsculas.
        for archivo in carpeta.iterdir():
            if not archivo.is_file():
                continue
            if archivo.name.casefold() == objetivo:
                return archivo
            if (
                archivo.stem.casefold() == objetivo_stem
                and archivo.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
            ):
                return archivo

        # Coincidencia normalizada: ignora tildes, espacios, puntos y guiones.
        # Esto evita que cambios como ``Bogotá 1- 10000.pdf`` rompan el visor.
        objetivo_normalizado = normalizar_etiqueta(Path(nombre_base).stem)
        for archivo in carpeta.iterdir():
            if not archivo.is_file():
                continue
            if archivo.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".webp", ".pdf"}:
                continue
            if normalizar_etiqueta(archivo.stem) == objetivo_normalizado:
                return archivo

    return None



def mostrar_pdf_mapa(ruta_pdf: Path, altura: int = 900) -> None:
    """Muestra un PDF de una sola página sin depender de un iframe del navegador.

    Se conserva el PDF original como fuente. Para visualizarlo dentro de Streamlit,
    primero se intenta el visor nativo ``st.pdf``. Si no está disponible, la primera
    página se rasteriza temporalmente en memoria (PyMuPDF, pypdfium2 o pdftoppm).
    Así se evita el cuadro blanco que algunos navegadores muestran con PDF embebidos.
    """
    ruta_pdf = Path(ruta_pdf)

    # 1) Visor PDF nativo de Streamlit, cuando está disponible.
    if hasattr(st, "pdf"):
        try:
            st.pdf(str(ruta_pdf), height=altura)
            return
        except Exception:
            pass

    imagen_png = None
    errores = []

    # 2) PyMuPDF / fitz.
    try:
        import fitz

        documento = fitz.open(str(ruta_pdf))
        pagina = documento.load_page(0)
        # ~200 ppp para que el mapa siga siendo legible al ampliar.
        matriz = fitz.Matrix(2.8, 2.8)
        pix = pagina.get_pixmap(matrix=matriz, alpha=False)
        imagen_png = pix.tobytes("png")
        documento.close()
    except Exception as error:
        errores.append(f"PyMuPDF: {error}")

    # 3) pypdfium2, si está instalado.
    if imagen_png is None:
        try:
            import io
            import pypdfium2 as pdfium

            documento = pdfium.PdfDocument(str(ruta_pdf))
            pagina = documento[0]
            bitmap = pagina.render(scale=2.8)
            pil_image = bitmap.to_pil()
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            imagen_png = buffer.getvalue()
            pagina.close()
            documento.close()
        except Exception as error:
            errores.append(f"pypdfium2: {error}")

    # 4) Poppler/pdftoppm, disponible en muchos Codespaces Linux.
    if imagen_png is None:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                salida_base = Path(tmp) / "mapa_bogota"
                subprocess.run(
                    [
                        "pdftoppm",
                        "-png",
                        "-f", "1",
                        "-singlefile",
                        "-r", "200",
                        str(ruta_pdf),
                        str(salida_base),
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                salida_png = salida_base.with_suffix(".png")
                if salida_png.exists():
                    imagen_png = salida_png.read_bytes()
        except Exception as error:
            errores.append(f"pdftoppm: {error}")

    if imagen_png is not None:
        st.image(
            imagen_png,
            caption=f"{ruta_pdf.name} · vista generada directamente desde el PDF original",
            use_container_width=True,
        )
        st.caption(
            "El archivo fuente sigue siendo PDF. La página se convierte temporalmente solo para "
            "mostrarla correctamente dentro del prototipo."
        )
    else:
        st.error(
            "El PDF sí fue encontrado, pero este Codespace no tiene un visor/rasterizador de PDF disponible."
        )
        st.code(
            'python -m pip install "streamlit[pdf]" pymupdf',
            language="bash",
        )
        with open(ruta_pdf, "rb") as archivo_pdf:
            st.download_button(
                "Abrir / descargar PDF original",
                data=archivo_pdf.read(),
                file_name=ruta_pdf.name,
                mime="application/pdf",
                key=f"pdf_bogota_{ruta_pdf.name}",
            )
        with st.expander("Ver diagnóstico del visor PDF", expanded=False):
            st.code("\n".join(errores) if errores else "Sin diagnóstico adicional", language=None)


def _circulo_geografico(lat_centro: float, lon_centro: float, radio_km: float, puntos: int = 96):
    """Genera un círculo geográfico aproximado para visualizar un radio de contexto."""
    latitudes = []
    longitudes = []
    radio_tierra_km = 6371.0088
    lat0 = math.radians(lat_centro)
    lon0 = math.radians(lon_centro)
    distancia_angular = radio_km / radio_tierra_km

    for i in range(puntos + 1):
        rumbo = 2 * math.pi * i / puntos
        lat = math.asin(
            math.sin(lat0) * math.cos(distancia_angular)
            + math.cos(lat0) * math.sin(distancia_angular) * math.cos(rumbo)
        )
        lon = lon0 + math.atan2(
            math.sin(rumbo) * math.sin(distancia_angular) * math.cos(lat0),
            math.cos(distancia_angular) - math.sin(lat0) * math.sin(lat),
        )
        latitudes.append(math.degrees(lat))
        longitudes.append(math.degrees(lon))

    return latitudes, longitudes


def mostrar_mapa_interactivo_bogota() -> None:
    """Mapa web navegable de la Sede Bogotá sin requerir token de Mapbox."""
    lat_sede = TERRITORIOS["Bogotá"]["lat"]
    lon_sede = TERRITORIOS["Bogotá"]["lon"]

    c1, c2, c3 = st.columns([1.05, 1.05, 1.4])
    with c1:
        vista = st.selectbox(
            "Vista inicial",
            ["Campus", "Bogotá", "Región"],
            key="bogota_vista_interactiva",
        )
    with c2:
        estilo_nombre = st.selectbox(
            "Mapa base",
            ["Claro", "OpenStreetMap", "Oscuro"],
            key="bogota_estilo_interactivo",
        )
    with c3:
        radio_km = st.slider(
            "Radio de contexto",
            min_value=0.5,
            max_value=10.0,
            value=1.5,
            step=0.5,
            format="%.1f km",
            key="bogota_radio_interactivo",
        )

    zoom_por_vista = {
        "Campus": 14.6,
        "Bogotá": 10.4,
        "Región": 7.7,
    }
    estilos = {
        "Claro": "carto-positron",
        "OpenStreetMap": "open-street-map",
        "Oscuro": "carto-darkmatter",
    }

    lat_circulo, lon_circulo = _circulo_geografico(
        lat_sede, lon_sede, radio_km
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scattermap(
            lat=lat_circulo,
            lon=lon_circulo,
            mode="lines",
            name=f"Radio de contexto: {radio_km:.1f} km",
            hoverinfo="skip",
            line=dict(width=2),
        )
    )

    fig.add_trace(
        go.Scattermap(
            lat=[lat_sede],
            lon=[lon_sede],
            mode="markers",
            name="Sede Bogotá",
            marker=dict(size=18),
            text=[
                "Universidad Nacional de Colombia<br>"
                "Sede Bogotá · Ciudad Universitaria"
            ],
            hovertemplate="<b>%{text}</b><br>Lat: %{lat:.5f}<br>Lon: %{lon:.5f}<extra></extra>",
        )
    )

    fig.update_layout(
        map=dict(
            style=estilos[estilo_nombre],
            center=dict(lat=lat_sede, lon=lon_sede),
            zoom=zoom_por_vista[vista],
        ),
        height=650,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.85)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "scrollZoom": True,
            "displaylogo": False,
        },
        key="mapa_interactivo_sede_bogota",
    )

    st.caption(
        "Mapa web interactivo del piloto: permite mover, acercar, alejar y consultar la sede. "
        "El radio es únicamente una ayuda visual de contexto y no representa un límite oficial del campus."
    )



def mostrar_mapa_interactivo_territorio(nombre_territorio: str, info_territorio: dict) -> None:
    """Mapa web interactivo reutilizable para las sedes SIAMS distintas de Bogotá.

    Bogotá conserva su piloto multiescala con los PDF originales. Esta función
    usa las coordenadas ya definidas en TERRITORIOS para Leticia, Tumaco,
    Medellín, San Andrés, Arauca y La Paz.
    """
    lat_sede = float(info_territorio["lat"])
    lon_sede = float(info_territorio["lon"])

    # Zoom ajustado por territorio para que la sede, la ciudad y la región
    # se vean con una escala razonable desde el primer momento.
    zoom_por_territorio = {
        "Leticia": {
            "Sede": 14.2,
            "Ciudad / municipio": 11.0,
            "Región": 8.0,
        },
        "Tumaco": {
            "Sede": 14.0,
            "Ciudad / municipio": 11.0,
            "Región": 8.0,
        },
        "Medellín": {
            "Sede": 14.0,
            "Ciudad / municipio": 10.5,
            "Región": 8.3,
        },
        "San Andrés": {
            "Sede": 14.0,
            "Ciudad / municipio": 11.2,
            "Región": 9.4,
        },
        "Arauca": {
            "Sede": 14.0,
            "Ciudad / municipio": 11.0,
            "Región": 8.0,
        },
        "La Paz": {
            "Sede": 14.0,
            "Ciudad / municipio": 11.0,
            "Región": 8.2,
        },
    }

    zooms = zoom_por_territorio.get(
        nombre_territorio,
        {
            "Sede": 14.0,
            "Ciudad / municipio": 10.5,
            "Región": 8.0,
        },
    )

    radios_default = {
        "Leticia": 5.0,
        "Tumaco": 5.0,
        "Medellín": 3.0,
        "San Andrés": 3.0,
        "Arauca": 5.0,
        "La Paz": 5.0,
    }

    c1, c2, c3 = st.columns([1.05, 1.05, 1.4])

    with c1:
        vista = st.selectbox(
            "Vista inicial",
            ["Sede", "Ciudad / municipio", "Región"],
            key=f"vista_interactiva_{nombre_territorio}",
        )

    with c2:
        estilo_nombre = st.selectbox(
            "Mapa base",
            ["Claro", "OpenStreetMap", "Oscuro"],
            key=f"estilo_interactivo_{nombre_territorio}",
        )

    with c3:
        radio_km = st.slider(
            "Radio de contexto",
            min_value=1.0,
            max_value=50.0,
            value=float(radios_default.get(nombre_territorio, 5.0)),
            step=1.0,
            format="%.0f km",
            key=f"radio_interactivo_{nombre_territorio}",
        )

    estilos = {
        "Claro": "carto-positron",
        "OpenStreetMap": "open-street-map",
        "Oscuro": "carto-darkmatter",
    }

    lat_circulo, lon_circulo = _circulo_geografico(
        lat_sede,
        lon_sede,
        radio_km,
    )

    fig = go.Figure()

    # Radio de contexto visual.
    fig.add_trace(
        go.Scattermap(
            lat=lat_circulo,
            lon=lon_circulo,
            mode="lines",
            name=f"Radio: {radio_km:.0f} km",
            hoverinfo="skip",
            line=dict(width=2),
        )
    )

    # Punto de la sede.
    fig.add_trace(
        go.Scattermap(
            lat=[lat_sede],
            lon=[lon_sede],
            mode="markers",
            name=nombre_territorio,
            marker=dict(size=19),
            text=[
                f"<b>{info_territorio['sede']}</b><br>"
                f"{nombre_territorio} · {info_territorio['departamento']}<br>"
                f"Latitud: {lat_sede:.6f}<br>"
                f"Longitud: {lon_sede:.6f}"
            ],
            hovertemplate="%{text}<extra></extra>",
        )
    )

    fig.update_layout(
        map=dict(
            style=estilos[estilo_nombre],
            center=dict(lat=lat_sede, lon=lon_sede),
            zoom=zooms[vista],
        ),
        height=650,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.85)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "scrollZoom": True,
            "displaylogo": False,
        },
        key=f"mapa_interactivo_{nombre_territorio}",
    )

    st.caption(
        "Puedes mover el mapa, acercar o alejar y consultar el punto de la sede. "
        "El círculo es únicamente una referencia visual del radio seleccionado; "
        "no representa un límite oficial de la sede ni del área de estudio."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        mostrar_tarjeta(
            "Sede de referencia",
            info_territorio["sede"],
            "📍",
        )

    with c2:
        mostrar_tarjeta(
            "Coordenadas",
            f"{lat_sede:.6f}, {lon_sede:.6f}",
            "🧭",
        )

    with c3:
        mostrar_tarjeta(
            "Contexto",
            info_territorio["contexto"],
            "🌎",
        )


def mostrar_ficha_tecnica_qgis(nombre_territorio: str, cfg: dict) -> None:
    """Ficha de referencia bajo cada mapa QGIS; no presume metadatos embebidos en el PDF."""
    base = FICHA_QGIS_REFERENCIA
    campo = lambda valor: escape(str(valor))
    st.markdown(
        '<div class="qgis-metadata-title">🧭 Información cartográfica del mapa</div>'
        '<div class="qgis-metadata-grid">'
        '<div class="qgis-metadata-card">'
        '<h4>📐 Sistema de coordenadas</h4>'
        f'<p><strong>SRC de referencia:</strong> {campo(base["src"])}<br>'
        f'<strong>Proyección:</strong> {campo(base["proyeccion"])}<br>'
        f'<strong>Unidades:</strong> {campo(base["unidades"])}</p>'
        '</div>'
        '<div class="qgis-metadata-card">'
        '<h4>🗺️ Fuentes de información</h4>'
        f'<p>{campo(base["fuentes"])}<br>'
        'Referencias declaradas en la ficha modelo aportada.</p>'
        '</div>'
        '<div class="qgis-metadata-card">'
        '<h4>🎓 Elaboración</h4>'
        f'<p>{campo(base["elaboracion"])}<br>'
        f'<strong>Año de elaboración:</strong> {campo(base["fecha"])}<br>'
        f'<strong>Sede:</strong> {campo(nombre_territorio)}<br>'
        f'<strong>Escala del mapa:</strong> {campo(cfg.get("escala", "Por verificar"))}</p>'
        '</div>'
        '</div>'
        '<p class="qgis-metadata-note">'
        'El SRC EPSG:9377 corresponde al proyecto QGIS mostrado en la captura. '
        'No se ha comprobado el SRC de exportación de cada PDF; '
        'Las fuentes indicadas proceden de la ficha de ejemplo y deben verificarse '
        'en cada mapa. Año de elaboración de los mapas SIAMS: 2026.'
        '</p>',
        unsafe_allow_html=True,
    )


def mostrar_navegador_ubicacion_bogota() -> None:
    """Navegador por niveles: Colombia → Bogotá → Campus → mapa interactivo."""
    st.markdown(
        dedent("""
        <div class="soft-box">
            <strong>Piloto de ubicación multiescala.</strong>
            Usa los botones para pasar de la ubicación nacional a la regional, después al campus
            y finalmente a una vista web interactiva. Los tres primeros niveles corresponden a
            los mapas cartográficos preparados en QGIS.
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

    if "nivel_ubicacion_bogota" not in st.session_state:
        st.session_state["nivel_ubicacion_bogota"] = "Colombia"

    botones = [
        ("🇨🇴 Colombia", "Colombia"),
        ("🏙️ Bogotá", "Bogotá"),
        ("🏫 Campus", "Campus"),
        ("🌎 Interactivo", "Interactivo"),
    ]
    columnas = st.columns(4)

    for columna, (etiqueta, valor) in zip(columnas, botones):
        with columna:
            if st.button(
                etiqueta,
                use_container_width=True,
                key=f"btn_ubicacion_bogota_{valor}",
            ):
                st.session_state["nivel_ubicacion_bogota"] = valor

    nivel = st.session_state["nivel_ubicacion_bogota"]

    pasos = ["Colombia", "Bogotá", "Campus", "Interactivo"]
    piezas = []
    for i, paso in enumerate(pasos):
        clase = "location-step active" if paso == nivel else "location-step"
        piezas.append(f'<span class="{clase}">{i + 1}. {paso}</span>')
        if i < len(pasos) - 1:
            piezas.append('<span class="location-arrow">→</span>')

    st.markdown(
        '<div class="location-progress">' + "".join(piezas) + "</div>",
        unsafe_allow_html=True,
    )

    configuracion = {
        "Colombia": {
            "clave": "ubicacion_colombia",
            "titulo": "Nivel 1 · Colombia",
            "detalle": "Ubicación de Bogotá D.C. dentro del contexto nacional.",
            "escala": "Escala cartográfica: 1:10.000.000",
        },
        "Bogotá": {
            "clave": "ubicacion_region",
            "titulo": "Nivel 2 · Bogotá y contexto regional",
            "detalle": "Acercamiento al Distrito Capital y su entorno regional.",
            "escala": "Escala cartográfica: 1:1.500.000",
        },
        "Campus": {
            "clave": "ubicacion_campus",
            "titulo": "Nivel 3 · Campus Ciudad Universitaria",
            "detalle": "Detalle de la Sede Bogotá y su entorno inmediato.",
            "escala": "Escala cartográfica: 1:10.000",
        },
    }

    st.markdown('<div class="location-shell">', unsafe_allow_html=True)

    if nivel == "Interactivo":
        st.markdown("### 🌎 Explorador interactivo de la Sede Bogotá")
        mostrar_mapa_interactivo_bogota()
    else:
        cfg = configuracion[nivel]
        st.markdown(f"### {cfg['titulo']}")
        st.caption(f"{cfg['detalle']} · {cfg['escala']}")

        nombre_archivo = MAPAS_BOGOTA[cfg["clave"]]
        ruta = buscar_mapa(nombre_archivo)

        if ruta is None:
            st.warning(
                f"No se encontró `{nombre_archivo}` en `Mapas Qgis`."
            )
            st.code(str(CARPETA_MAPAS), language=None)
            st.info(
                "Pon los tres PDF originales dentro de `Mapas Qgis`, conservando exactamente "
                "los nombres con los que los exportaste desde QGIS."
            )
        else:
            if ruta.suffix.casefold() == ".pdf":
                mostrar_pdf_mapa(ruta, altura=900)
            else:
                st.image(
                    str(ruta),
                    caption=f"{cfg['titulo']} · {cfg['escala']}",
                    use_container_width=True,
                )
            st.caption(f"Archivo: {ruta.name} · {cfg['escala']}")
            mostrar_ficha_tecnica_qgis("Bogotá", cfg)


    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        mostrar_tarjeta(
            "Sede",
            "Universidad Nacional de Colombia – Sede Bogotá.",
            "📍",
        )
    with c2:
        mostrar_tarjeta(
            "Navegación",
            "Colombia → Bogotá → Campus → explorador interactivo.",
            "🧭",
        )
    with c3:
        mostrar_tarjeta(
            "Uso del piloto",
            "Ubicación institucional y contexto espacial; no sustituye cartografía temática oficial.",
            "🗺️",
        )



def mostrar_navegador_ubicacion_qgis(nombre_territorio: str, info_territorio: dict) -> None:
    """Navegador multiescala QGIS para territorios con mapas disponibles."""
    niveles = MAPAS_UBICACION_QGIS.get(nombre_territorio, [])
    if not niveles:
        mostrar_mapa_interactivo_territorio(nombre_territorio, info_territorio)
        return

    st.markdown(
        dedent(f"""
        <div class="soft-box">
            <strong>Ubicación multiescala en QGIS.</strong>
            Explora los mapas cartográficos disponibles —desde el contexto nacional
            hasta la sede— y después abre el explorador interactivo de
            <strong>{escape(str(nombre_territorio))}</strong>.
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

    clave_estado = f"nivel_ubicacion_qgis_{normalizar_etiqueta(nombre_territorio)}"
    opciones = [nivel["paso"] for nivel in niveles] + ["Interactivo"]
    if clave_estado not in st.session_state or st.session_state[clave_estado] not in opciones:
        st.session_state[clave_estado] = opciones[0]

    etiquetas = []
    for i, nivel in enumerate(niveles):
        if i == 0:
            icono = "🇨🇴"
        elif i == len(niveles) - 1:
            icono = "🏫"
        else:
            icono = "🧭"
        etiquetas.append((f"{icono} {nivel['paso']}", nivel["paso"]))
    etiquetas.append(("🌎 Interactivo", "Interactivo"))

    columnas = st.columns(len(etiquetas))
    for columna, (etiqueta, valor) in zip(columnas, etiquetas):
        with columna:
            if st.button(
                etiqueta,
                use_container_width=True,
                key=f"btn_qgis_{normalizar_etiqueta(nombre_territorio)}_{normalizar_etiqueta(valor)}",
            ):
                st.session_state[clave_estado] = valor

    nivel_activo = st.session_state[clave_estado]
    piezas = []
    for i, paso in enumerate(opciones):
        clase = "location-step active" if paso == nivel_activo else "location-step"
        piezas.append(f'<span class="{clase}">{i + 1}. {escape(str(paso))}</span>')
        if i < len(opciones) - 1:
            piezas.append('<span class="location-arrow">→</span>')

    st.markdown(
        '<div class="location-progress">' + "".join(piezas) + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="location-shell">', unsafe_allow_html=True)

    if nivel_activo == "Interactivo":
        st.markdown(f"### 🌎 Explorador interactivo de {nombre_territorio}")
        if nombre_territorio == "Bogotá":
            mostrar_mapa_interactivo_bogota()
        else:
            mostrar_mapa_interactivo_territorio(nombre_territorio, info_territorio)
    else:
        cfg = next(n for n in niveles if n["paso"] == nivel_activo)
        st.markdown(f"### {cfg['titulo']}")
        st.caption(f"{cfg['detalle']} · Escala cartográfica: {cfg['escala']}")

        ruta = buscar_mapa(cfg["archivo"])
        if ruta is None:
            st.warning(f"No se encontró `{cfg['archivo']}` dentro de `Mapas Qgis`.")
            st.caption(f"Ruta esperada: {CARPETA_MAPAS_QGIS / cfg['archivo']}")
        elif ruta.suffix.casefold() == ".pdf":
            mostrar_pdf_mapa(ruta, altura=900)
            st.caption(f"Archivo: {ruta.name} · Escala {cfg['escala']}")
            mostrar_ficha_tecnica_qgis(nombre_territorio, cfg)
        else:
            st.image(
                str(ruta),
                caption=f"{cfg['titulo']} · Escala {cfg['escala']}",
                use_container_width=True,
            )
            mostrar_ficha_tecnica_qgis(nombre_territorio, cfg)

    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        mostrar_tarjeta("Sede de referencia", info_territorio["sede"], "📍")
    with c2:
        mostrar_tarjeta(
            "Navegación",
            " → ".join(opciones),
            "🧭",
        )
    with c3:
        mostrar_tarjeta(
            "Uso del visor",
            "Ubicación institucional y contexto espacial; no sustituye cartografía temática oficial.",
            "🗺️",
        )

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


# =========================================================
# COBERTURAS MAPBIOMAS · CSV POR SEDE
# =========================================================
CARPETA_COBERTURAS = CARPETA_PROYECTO / "Coberturas MapBio"
COBERTURAS_POR_TERRITORIO = {
    "Arauca": {"carpeta": "ARAUCA", "zonas": {"A": "Arauca"}},
    "La Paz": {"carpeta": "LA PAZ", "zonas": {"LP": "La Paz"}},
    "Leticia": {"carpeta": "LETICIA", "zonas": {"L": "Leticia"}},
    "Medellín": {"carpeta": "MEDELLIN", "zonas": {"M": "Medellín"}},
    "San Andrés": {
        "carpeta": "SAN ANDRES",
        "zonas": {"SA": "San Andrés", "SAC": "San Andrés Costa"},
    },
    "Tumaco": {"carpeta": "TUMACO", "zonas": {"T": "Tumaco"}},
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
    carpeta = CARPETA_COBERTURAS / config["carpeta"]
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
        "Nivel 1": "MapBiomas Gif Arauca.gif",
        "Nivel 2": "MapBiomas Gif Arauca 2.gif",
        "Natural / antrópico": "MapBiomas Gif Arauca AntNat.gif",
    },
    "La Paz": {
        "Nivel 1": "MapBiomas Gif La Paz.gif",
        "Nivel 2": "MapBiomas Gif La Paz 2.gif",
        "Natural / antrópico": "MapBiomas Gif La Paz AntNat.gif",
    },
    "Leticia": {
        "Nivel 1": "MapBiomas Gif Leticia.gif",
        "Nivel 2": "MapBiomas Gif Leticia 2.gif",
        "Natural / antrópico": "MapBiomas Gif Leticia AntNat.gif",
    },
    "Medellín": {
        "Nivel 1": "MapBiomas Gif Medellin.gif",
        "Nivel 2": "MapBiomas Gif Medellin 2.gif",
        "Natural / antrópico": "MapBiomas Gif Medellin AntNat.gif",
    },
    "San Andrés": {
        "Nivel 1": "MapBiomas Gif San Andres.gif",
        "Nivel 2": "MapBiomas Gif San Andres 2.gif",
        "Natural / antrópico": "MapBiomas Gif San Andres AntNat.gif",
    },
    "Tumaco": {
        "Nivel 1": "MapBiomas Gif Tumaco.gif",
        "Nivel 2": "MapBiomas Gif Tumaco 2.gif",
        "Natural / antrópico": "MapBiomas Gif Tumaco AntNat.gif",
    },
}


def buscar_gif_mapbiomas(nombre_territorio: str, nombre_archivo: str):
    """Busca un GIF MapBiomas dentro de la carpeta de la sede, tolerando tildes y espacios."""
    config = COBERTURAS_POR_TERRITORIO.get(nombre_territorio)
    if config is None:
        return None

    carpeta = CARPETA_COBERTURAS / config["carpeta"]
    if not carpeta.is_dir():
        return None

    ruta_directa = carpeta / nombre_archivo
    if ruta_directa.exists() and ruta_directa.is_file():
        return ruta_directa

    objetivo = normalizar_etiqueta(Path(nombre_archivo).stem)
    for archivo in sorted(carpeta.iterdir(), key=lambda p: p.name.casefold()):
        if not archivo.is_file() or archivo.suffix.casefold() != ".gif":
            continue
        if normalizar_etiqueta(archivo.stem) == objetivo:
            return archivo
    return None


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
                st.caption(f"Archivo esperado: Coberturas MapBio/{COBERTURAS_POR_TERRITORIO[nombre_territorio]['carpeta']}/{archivo}")
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


# =========================================================
# MAPBIOMAS · ESTADÍSTICAS DE COBERTURA NATURAL Y ANTRÓPICA
# =========================================================
# Este producto usa CSV independientes de los de Nivel 1 y Nivel 2.
# No clasifica por su cuenta las clases de MapBiomas: respeta la
# clasificación natural/antrópica ya contenida en cada archivo fuente.

def buscar_csv_natural_antropico(nombre_territorio: str, codigo: str):
    """Localiza CSV Ant-Nat sin confundirlos con las series de Nivel 1/2."""
    cfg = COBERTURAS_POR_TERRITORIO.get(nombre_territorio)
    if not cfg or codigo not in cfg["zonas"]:
        return [], []
    carpeta = CARPETA_COBERTURAS / cfg["carpeta"]
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
            f"Coberturas MapBio/{COBERTURAS_POR_TERRITORIO[nombre_territorio]['carpeta']}."
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
        st.caption(f"Ubicación: Coberturas MapBio/{config['carpeta']} · CSV que termina en {codigo}.")
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



# =========================================================
# LANDSAT · SERIES DE COBERTURAS POR FECHA DISPONIBLE
# =========================================================
# Carpeta esperada: Landsat/<sede>/{GIF_Landsat_*.gif,
#   Areas_coberturas_por_fecha.csv, Control_escenas.csv}
# Descubre los nombres de los GIF y los años sin renombrarlos.
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


def actualizar_estado_coberturas() -> None:
    """Actualiza solo el componente de cobertura; el relieve sigue en proceso."""
    for nombre, config in COBERTURAS_POR_TERRITORIO.items():
        disponibles = [codigo for codigo in config["zonas"] if len(encontrar_csv_coberturas(nombre, codigo)["serie"]) == 1]
        if not disponibles:
            continue
        nota = "CSV de coberturas detectados para " + ", ".join(config["zonas"][codigo] for codigo in disponibles) + "; la cartografía de relieve conserva su estado previo."
        ESTADO_COMPONENTES[nombre] = [
            (componente, "En proceso", nota) if componente == "Cobertura y relieve" else (componente, estado, texto)
            for componente, estado, texto in ESTADO_COMPONENTES[nombre]
        ]


actualizar_estado_coberturas()


def actualizar_estado_landsat() -> None:
    """Reconoce series Landsat como producto exploratorio, sin considerarlas validadas."""
    for nombre_territorio in TERRITORIOS:
        inv = inventario_landsat(nombre_territorio)
        if not inv["gifs"]:
            continue
        detalle = (
            "Landsat: animación por fechas disponibles"
            + (", CSV de áreas" if inv["areas"] else "")
            + (" y control de escenas" if inv["control"] else "")
            + ". Producto exploratorio pendiente de validación."
        )
        ESTADO_COMPONENTES[nombre_territorio] = [
            (componente, "En proceso", detalle if estado == "Pendiente"
             else f"{nota} {detalle}")
            if componente == "Cobertura y relieve" else (componente, estado, nota)
            for componente, estado, nota in ESTADO_COMPONENTES[nombre_territorio]
        ]


actualizar_estado_landsat()


# =========================================================
# SENTINEL-2 · ANIMACIONES NDVI / MNDWI / SCL POR TERRITORIO
# =========================================================
# Estructura: Sentinel/Leticia/animacion_NDVI_2025 Leticia.gif
# El lector también reconoce variantes de mayúsculas, espacios y tildes.
CARPETA_SENTINEL = CARPETA_PROYECTO / "Sentinel"

CARPETAS_SENTINEL_POR_TERRITORIO = {
    "Arauca": "Arauca",
    "La Paz": "La Paz",
    "Leticia": "Leticia",
    "Medellín": "Medellin",
    "San Andrés": "San Andres",
    "Tumaco": "Tumaco",
}

# Los nombres exactos de las animaciones ya entregadas se conservan.
# Si después se suben nuevos años, el explorador los detecta automáticamente.
SENTINEL_ARCHIVOS_POR_TERRITORIO = {
    "Leticia": {
        2025: {
            "NDVI": "animacion_NDVI_2025 Leticia.gif",
            "MNDWI": "animacion_MNDWI_2025 Leticia.gif",
            "SCL": "animacion_SCL_2025 Leticia.gif",
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


# =========================================================
# BARRA LATERAL CON SUBMENÚS
# =========================================================

# El archivo original sigue sirviendo como favicon. En la barra lateral se muestra
# como isotipo pequeño junto a texto nítido, sin agrandarlo a 110 px.
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
    )

st.sidebar.divider()
st.sidebar.caption("Prototipo académico. Información sujeta a revisión.")
st.sidebar.success(f"Versión activa: {VERSION_APP}")
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
    st.write("**Excel detectados en Analisis Hidro:**")
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
    for config_cob in COBERTURAS_POR_TERRITORIO.values():
        carpeta_cob = CARPETA_COBERTURAS / config_cob["carpeta"]
        if carpeta_cob.is_dir():
            csv_detectados.extend(str(p.relative_to(CARPETA_COBERTURAS)) for p in carpeta_cob.iterdir() if p.is_file() and p.suffix.casefold() == ".csv")
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

# =========================================================
# INICIO
# =========================================================

if seccion == "Inicio":
    mostrar_encabezado(
        "Plataforma hidroambiental SIAMS",
        "Un espacio para explorar información climática, hidrológica, geológica, "
        "hidrogeológica y de calidad del agua de los territorios estudiados por el semillero.",
    )

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

    st.markdown(
        '<div class="section-title">Estado rápido de los territorios</div>',
        unsafe_allow_html=True,
    )

    fila1 = st.columns(3)
    fila2 = st.columns(3)
    fila3 = st.columns(3)

    tarjetas_territorio = [
        (fila1[0], "Bogotá", "<strong>Piloto de ubicación</strong><br>Mapas por niveles + explorador interactivo.", "📍"),
        (fila1[1], "Leticia", "<strong>Clima completo</strong><br>Cartografía ambiental avanzada.", "🌿"),
        (fila1[2], "Tumaco", "<strong>Clima completo</strong><br>IDEAM + NASA POWER y cartografía regional.", "🌊"),
        (fila2[0], "Medellín", "<strong>Clima completo</strong><br>Geología, estructura ecológica e inundación.", "🏙️"),
        (fila2[1], "San Andrés", "<strong>Clima completo</strong><br>Hidrogeología y calidad del agua destacadas.", "🏝️"),
        (fila2[2], "Arauca", "<strong>Clima + cartografía en proceso</strong><br>IDEAM, NASA POWER, geología e hidrogeología regional.", "🌾"),
        (fila3[0], "La Paz", "<strong>Territorio habilitado</strong><br>GWSa GRACE y módulos para ampliar datos.", "⛰️"),
    ]
    for columna, nombre, texto_tarjeta, icono in tarjetas_territorio:
        with columna:
            mostrar_tarjeta(nombre, texto_tarjeta, icono)

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

        prefijo_ideam = (
            "ANALISIS_HIDROMETEOROLOGICO_Tumaco*.xlsx"
            if territorio == "Tumaco"
            else "ANALISIS_HIDROMETEOROLOGICO_Arauca*.xlsx"
        )
        prefijo_nasa = f"NASA_POWER_{territorio.upper()}*.xlsx"

        faltantes = []
        if archivo_ideam is None:
            faltantes.append(prefijo_ideam)
        if archivo_nasa is None:
            faltantes.append(prefijo_nasa)

        if faltantes:
            st.error(
                f"Faltan archivos climáticos de {territorio} en `Analisis Hidro`: "
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
                        "Radiación solar": "Radiación NASA (kWh/m²/día)",
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
                f"Ponlo dentro de `Analisis Hidro` con un nombre que comience por "
                f"`{prefijos.get(territorio, 'NASA_POWER')}`."
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
                    "Radiación solar (kWh/m²/día)",
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
    st.caption("Mann-Kendall + pendiente de Sen · series históricas reales")

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
                    resumen_tendencias.append({
                        "Variable": variable,
                        "Fuente": paquete["fuente"],
                        "Periodo": f"{int(anual['Año'].min())}–{int(anual['Año'].max())}",
                        "Años": len(anual),
                        "Tau": res["tau"],
                        "p-value": res["p"],
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

                st.subheader("Resumen de tendencias disponibles")
                tabla_tend = df_resumen_tend.copy()
                tabla_tend["Tau"] = tabla_tend["Tau"].map(lambda x: f"{x:+.3f}")
                tabla_tend["p-value"] = tabla_tend["p-value"].map(lambda x: f"{x:.4f}")
                tabla_tend["Pendiente Sen"] = tabla_tend["Pendiente Sen"].map(lambda x: f"{x:+.4f}")
                st.dataframe(tabla_tend, use_container_width=True, hide_index=True)

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

                st.markdown(dedent("""
                    <div class="warning-box">
                        <strong>Limitaciones:</strong> Mann-Kendall identifica tendencias monotónicas,
                        pero no demuestra su causa. La significancia puede verse afectada por
                        autocorrelación, cambios de instrumento, vacíos de información o cambios en
                        la fuente. Para estudios definitivos conviene revisar homogeneidad y, cuando
                        corresponda, aplicar variantes que corrijan autocorrelación.
                    </div>
                    """).strip(), unsafe_allow_html=True)

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
            "No se encontró `COL_GWS_estimations.nc`. Pon el archivo junto a `app.py` "
            "o dentro de `datos/gws` o `datos/agua_subterranea`."
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
                    fig = px.line(
                        df_gws, x="Fecha", y="GWSa (cm)",
                        title=f"Anomalía de almacenamiento de agua subterránea · {territorio}",
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
                        "Valores positivos y negativos indican desviaciones respecto a la referencia; "
                        "por sí solos no equivalen a una clasificación de sostenibilidad."
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

                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df_ggdi["Fecha"],
                            y=df_ggdi["GGDI"],
                            mode="lines",
                            name="GGDI",
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

                        fig_comp = go.Figure()
                        fig_comp.add_trace(go.Scatter(
                            x=df_anio["Mes"],
                            y=df_anio["GWSa (cm)"],
                            mode="lines+markers",
                            name=f"GWSa observada {anio_sel}",
                        ))
                        fig_comp.add_trace(go.Scatter(
                            x=df_anio["Mes"],
                            y=df_anio["GWSa climatológica (cm)"],
                            mode="lines+markers",
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

# =========================================================
# HIDROGEOQUÍMICA
# =========================================================

elif seccion == "Hidrogeoquímica":
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
            pass

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
                    pass
            continue

        try:
            df_i, _, _, _ = cargar_ideam_tumaco(str(archivo_i))
            combinado = df_i.copy()

            if archivo_n is not None:
                try:
                    df_n, _ = cargar_nasa_tumaco(str(archivo_n))
                    combinado = combinado.merge(df_n, on="Mes", how="left")
                except Exception:
                    pass

            if nombre == "Arauca":
                humedad = (
                    combinado["Humedad IDEAM (%)"]
                    if "Humedad IDEAM (%)" in combinado.columns else pd.NA
                )
                fuente_hr = "IDEAM con advertencia + contraste NASA"
            else:
                humedad = (
                    combinado["Humedad NASA (%)"]
                    if "Humedad NASA (%)" in combinado.columns
                    else combinado.get("Humedad IDEAM (%)", pd.NA)
                )
                fuente_hr = "NASA POWER + contraste IDEAM"

            temporal = pd.DataFrame({
                "Mes": combinado["Mes"],
                "Precipitación mensual (mm)": combinado["Precipitación IDEAM (mm)"],
                "Temperatura media (°C)": combinado["Temperatura media IDEAM (°C)"],
                "Temperatura máxima (°C)": combinado.get("Temperatura máxima IDEAM (°C)", pd.NA),
                "Temperatura mínima (°C)": combinado.get("Temperatura mínima IDEAM (°C)", pd.NA),
                "Humedad relativa (%)": humedad,
                "Viento a 2 m (m/s)": combinado.get("Viento a 2 m NASA (m/s)", pd.NA),
                "Presión superficial (kPa)": combinado.get("Presión NASA (kPa)", pd.NA),
                "Radiación solar (kWh/m²/día)": combinado.get("Radiación NASA (kWh/m²/día)", pd.NA),
                "Territorio": nombre,
                "Fuente principal": "IDEAM + NASA POWER",
            })
            datasets.append(temporal)

            fuentes_resumen.append({
                "Territorio": nombre,
                "Precipitación": "IDEAM",
                "Temperatura": "IDEAM",
                "Humedad": fuente_hr,
                "Viento / presión / radiación": "NASA POWER",
            })
        except Exception:
            pass

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
                "Radiación solar": "Radiación solar (kWh/m²/día)",
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
                    Radiacion_media_kWh_m2_dia=("Radiación solar (kWh/m²/día)", "mean"),
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

# =========================================================
# PIE DE PÁGINA
# =========================================================

st.divider()

st.caption(
    f"SIAMS · Universidad Nacional de Colombia · Prototipo hidroambiental · "
    f"Territorio seleccionado: {territorio} · Actualización: {FECHA_ACTUALIZACION}"
)



