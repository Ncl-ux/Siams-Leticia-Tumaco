from pathlib import Path
from textwrap import dedent

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

VERSION_APP = "PROTOTIPO-SIAMS-V15-2026-09-02"
FECHA_ACTUALIZACION = "2 de septiembre de 2026"

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="SIAMS | Plataforma Hidroambiental",
    page_icon="💧",
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
        "Estado": "Otra sede UNAL (contexto)",
        "Descripcion": "Sede Bogotá de la Universidad Nacional de Colombia.",
        "Tamano": 11,
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
        "lat": 7.012223,
        "lon": -70.743388,
        "Estado": "Otra sede UNAL (contexto)",
        "Descripcion": "Sede Orinoquía de la Universidad Nacional de Colombia.",
        "Tamano": 11,
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
        "lat": 10.390218,
        "lon": -73.200389,
        "Estado": "Otra sede UNAL (contexto)",
        "Descripcion": "Sede de La Paz de la Universidad Nacional de Colombia.",
        "Tamano": 11,
    },
])
TERRITORIOS = {
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
}


# =========================================================
# ESTADO DEL PROTOTIPO Y METADATOS
# =========================================================

ESTADO_COMPONENTES = {
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


def interpretacion_tumaco(df: pd.DataFrame, control: pd.DataFrame) -> str:
    p_i = "Precipitación IDEAM (mm)"
    p_n = "Precipitación NASA (mm)"
    mes_pmax = df.loc[df[p_i].idxmax()]
    mes_pmin = df.loc[df[p_i].idxmin()]
    total_i = df[p_i].sum()
    total_n = df[p_n].sum()
    diferencia = (total_n / total_i - 1) * 100 if total_i else float('nan')
    fila = control.loc[control["Variable"].astype(str).eq("precipitacion")]
    comp = float(fila.iloc[0]["Completitud [%]"]) if not fila.empty else float('nan')
    return (
        f"La precipitación observada por IDEAM presenta su máximo mensual en <strong>{mes_pmax['Mes']}</strong> "
        f"({mes_pmax[p_i]:.1f} mm) y el mínimo en <strong>{mes_pmin['Mes']}</strong> "
        f"({mes_pmin[p_i]:.1f} mm). La serie de precipitación IDEAM tiene {comp:.2f} % de completitud. "
        f"NASA POWER registra un acumulado climatológico {abs(diferencia):.1f} % menor, por lo que no se adopta como "
        "fuente principal de lluvia. En temperatura, NASA funciona como complemento; en viento, presión y radiación, "
        "es la fuente disponible dentro del prototipo."
    )



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

MAPAS_POR_TERRITORIO = {
    "Leticia": MAPAS_LETICIA,
    "Tumaco": MAPAS_TUMACO,
    "Medellín": MAPAS_MEDELLIN,
    "San Andrés": MAPAS_SAN_ANDRES,
}


def encontrar_carpeta_mapas() -> Path:
    """Busca la carpeta de mapas tanto junto al código como en Documentos."""
    carpeta_codigo = Path(__file__).resolve().parent

    candidatas = [
        carpeta_codigo / "SIAMS MAPAS",
        carpeta_codigo / "mapas",
        carpeta_codigo / "datos" / "mapas",
        carpeta_codigo / "datos" / "leticia" / "mapas",
        carpeta_codigo / "datos" / "tumaco" / "mapas",
        Path.home() / "Documents" / "SIAMS MAPAS",
        Path.home() / "Documentos" / "SIAMS MAPAS",
    ]

    for carpeta in candidatas:
        if carpeta.exists() and carpeta.is_dir():
            return carpeta

    # Si ninguna existe, se devuelve la primera para mostrar una ruta clara en el aviso.
    return candidatas[0]


CARPETA_MAPAS = encontrar_carpeta_mapas()
EXTENSIONES_IMAGEN = (".png", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG", ".WEBP")


# =========================================================
# ARCHIVO CLIMÁTICO DE LETICIA
# =========================================================

def encontrar_archivo_clima_leticia():
    """Localiza automáticamente el Excel de NASA POWER junto al proyecto."""
    carpeta_codigo = Path(__file__).resolve().parent
    carpetas = [
        carpeta_codigo,
        carpeta_codigo / "DATOS CLIMA",
        carpeta_codigo / "datos",
        carpeta_codigo / "datos" / "leticia",
        carpeta_codigo / "datos" / "leticia" / "clima",
    ]

    nombres_preferidos = [
        "NASA_POWER_LETICIA_FINAL.xlsx",
        "NASA_POWER_LETICIA_FINAL (3).xlsx",
    ]

    for carpeta in carpetas:
        for nombre in nombres_preferidos:
            ruta = carpeta / nombre
            if ruta.exists() and ruta.is_file():
                return ruta

    # Permite variaciones del nombre, por ejemplo copias con (1), (2), etc.
    for carpeta in carpetas:
        if carpeta.exists():
            coincidencias = sorted(carpeta.glob("NASA_POWER_LETICIA*.xlsx"))
            if coincidencias:
                return coincidencias[0]

    return None


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

def encontrar_archivo_excel(prefijos, nombres_preferidos, subcarpetas):
    """Localiza un Excel junto al proyecto, incluso si tiene (1), (2), etc."""
    carpeta_codigo = Path(__file__).resolve().parent
    carpetas = [carpeta_codigo] + [carpeta_codigo / sub for sub in subcarpetas]

    for carpeta in carpetas:
        for nombre in nombres_preferidos:
            ruta = carpeta / nombre
            if ruta.exists() and ruta.is_file():
                return ruta

    for carpeta in carpetas:
        if not carpeta.exists():
            continue
        for prefijo in prefijos:
            coincidencias = sorted(carpeta.glob(f"{prefijo}*.xlsx"))
            if coincidencias:
                return coincidencias[0]
    return None


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

ARCHIVOS_CLIMA_NASA = {
    "Leticia": ARCHIVO_CLIMA_LETICIA,
    "Medellín": ARCHIVO_CLIMA_MEDELLIN,
    "San Andrés": ARCHIVO_CLIMA_SAN_ANDRES,
}

# Alias de compatibilidad para la sección de comparación.
ARCHIVOS_NASA = ARCHIVOS_CLIMA_NASA


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


def decisiones_climaticas_tumaco(control: pd.DataFrame) -> pd.DataFrame:
    """Construye la decisión de uso por variable con base en disponibilidad y calidad."""
    completitud = {}
    if control is not None and not control.empty:
        for _, fila in control.iterrows():
            completitud[str(fila.get("Variable", ""))] = fila.get("Completitud [%]")

    def pct(clave):
        valor = completitud.get(clave)
        return f"{float(valor):.2f} %" if pd.notna(valor) else "—"

    return pd.DataFrame({
        "Variable": [
            "Precipitación",
            "Temperatura media",
            "Temperatura máxima",
            "Temperatura mínima",
            "Humedad relativa",
            "Viento",
            "Presión",
            "Radiación",
        ],
        "Completitud IDEAM": [
            pct("precipitacion"),
            pct("temperatura_media"),
            pct("temperatura_maxima"),
            pct("temperatura_minima"),
            pct("humedad_relativa"),
            "No disponible",
            "No disponible",
            "No disponible",
        ],
        "Fuente principal": [
            "IDEAM",
            "IDEAM",
            "IDEAM con cautela",
            "IDEAM con cautela",
            "NASA POWER + contraste IDEAM",
            "NASA POWER",
            "NASA POWER",
            "NASA POWER",
        ],
        "Uso de la otra fuente": [
            "NASA POWER para comparación; no reemplaza la lluvia observada",
            "NASA POWER como serie continua complementaria",
            "NASA POWER como apoyo por faltantes IDEAM",
            "NASA POWER como apoyo por faltantes IDEAM",
            "IDEAM como observación local parcial",
            "Sin contraste IDEAM en el archivo",
            "Sin contraste IDEAM en el archivo",
            "Sin contraste IDEAM en el archivo",
        ],
    })


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
    """Devuelve la ruta de una imagen sin depender de su extensión."""
    for extension in EXTENSIONES_IMAGEN:
        ruta = CARPETA_MAPAS / f"{nombre_base}{extension}"
        if ruta.exists():
            return ruta

    # También permite pequeñas variaciones de mayúsculas/minúsculas en el nombre.
    if CARPETA_MAPAS.exists():
        objetivo = nombre_base.casefold()
        for archivo in CARPETA_MAPAS.iterdir():
            if archivo.is_file() and archivo.stem.casefold() == objetivo:
                if archivo.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}:
                    return archivo

    return None


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
        if nombre_territorio == "Tumaco":
            if ARCHIVO_IDEAM_TUMACO is not None:
                df_i, _, _, _ = cargar_ideam_tumaco(str(ARCHIVO_IDEAM_TUMACO))
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
        "Leticia": "Alta humedad y fuerte relación con el sistema fluvial amazónico.",
        "Tumaco": "Interacción permanente entre sistemas fluviales, estuarinos y marino-costeros.",
        "Medellín": "Contexto urbano-andino con quebradas, fuertes pendientes y amenaza por inundación.",
        "San Andrés": "La disponibilidad de agua dulce está estrechamente ligada a la lluvia y los acuíferos.",
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

    fig = px.scatter_mapbox(
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
        mapbox_style="carto-positron",
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
        (Leticia, Tumaco, Medellín y San Andrés).<br>
        ⚪ <strong>Gris:</strong> otras sedes de la Universidad Nacional que se muestran
        únicamente como contexto institucional y todavía no tienen un módulo territorial
        desarrollado dentro de esta versión del prototipo.
    </div>
    """
    st.markdown(dedent(html).strip(), unsafe_allow_html=True)

def tabla_disponibilidad(nombre_territorio: str) -> pd.DataFrame:
    if nombre_territorio in {"Leticia", "Medellín", "San Andrés"}:
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
            "NASA POWER",
            "NASA POWER",
            "NASA POWER",
        ],
    })


# =========================================================
# BARRA LATERAL CON SUBMENÚS
# =========================================================

st.sidebar.markdown("## 💧 SIAMS")
st.sidebar.caption("Plataforma hidroambiental")

modo_presentacion = st.sidebar.checkbox(
    "🎤 Modo presentación",
    value=False,
    help="Oculta elementos técnicos y deja una vista más limpia para exponer.",
)


territorio = st.sidebar.selectbox(
    "Territorio",
    ["Leticia", "Tumaco", "Medellín", "San Andrés"],
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
    ],
    "Clima y datos": [
        "Clima",
        "Estaciones y datos",
    ],
    "Subsuelo y calidad del agua": [
        "Geología",
        "Hidrogeología",
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

publico = st.sidebar.selectbox(
    "Nivel de consulta",
    [
        "Público general",
        "Estudiantes",
        "Información técnica",
    ],
)

st.sidebar.divider()
st.sidebar.caption("Prototipo académico. Información sujeta a revisión.")
st.sidebar.success(f"Versión activa: {VERSION_APP}")
if not modo_presentacion:
    with st.sidebar.expander("Diagnóstico de archivos", expanded=False):
        st.write(f"**Script:** `{Path(__file__).name}`")
        st.write(f"**Carpeta de mapas:** `{CARPETA_MAPAS}`")
        if CARPETA_MAPAS.exists():
            archivos_detectados = sorted(
                archivo.name for archivo in CARPETA_MAPAS.iterdir() if archivo.is_file()
            )
            st.write("**Archivos detectados:**")
            st.code("\n".join(archivos_detectados) if archivos_detectados else "Carpeta vacía", language=None)
        else:
            st.error("La carpeta de mapas no existe.")

# PRESENTATION_HIDE_DOWNLOADS
if modo_presentacion:
    st.markdown(
        """
        <style>
        .stDownloadButton { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
    m1.metric("Territorios activos en SIAMS", "4")
    m2.metric("Cobertura actual", "Amazonía · Caribe · Andina · Pacífico")

    st.caption(
        "La localización nacional permite contextualizar el alcance territorial del prototipo "
        "y visualizar las sedes priorizadas para esta fase de desarrollo."
    )

    st.markdown(
        '<div class="section-title">Estado rápido de los territorios</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        mostrar_tarjeta(
            "Leticia",
            "<strong>Clima completo</strong><br>Cartografía ambiental avanzada.",
            "🌿",
        )

    with c2:
        mostrar_tarjeta(
            "Tumaco",
            "<strong>Clima completo</strong><br>IDEAM + NASA POWER y cartografía regional.",
            "🌊",
        )

    with c3:
        mostrar_tarjeta(
            "Medellín",
            "<strong>Clima completo</strong><br>Geología, estructura ecológica e inundación.",
            "🏙️",
        )

    with c4:
        mostrar_tarjeta(
            "San Andrés",
            "<strong>Clima completo</strong><br>Hidrogeología y calidad del agua destacadas.",
            "🏝️",
        )

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
            "Geología, hidrogeología, hidrogeoquímica y calidad del agua.",
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
        "Territorio": ["Leticia", "Tumaco", "Medellín", "San Andrés"],
        "Clima": ["✅", "✅", "✅", "✅"],
        "Hidrología": ["✅", "✅", "🟡", "✅"],
        "Geología": ["✅", "✅", "✅", "✅"],
        "Hidrogeología": ["🟡", "🟡", "—", "✅"],
        "Calidad del agua": ["🟡", "—", "—", "🟡"],
        "Monitoreo": ["—", "—", "—", "—"],
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
    m1.metric("Territorios", "4")
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

    st.write(
        "Este mapa interactivo ubica la sede de referencia. Los mapas temáticos "
        "completos se presentan en las secciones de hidrología, cobertura, relieve, "
        "geología, hidrogeología e IRCA."
    )

    mapa = pd.DataFrame(
        {
            "lat": [info["lat"]],
            "lon": [info["lon"]],
        }
    )

    st.map(mapa, zoom=12 if territorio == "San Andrés" else (11 if territorio in {"Leticia", "Medellín"} else 10))

    c1, c2, c3 = st.columns(3)

    with c1:
        mostrar_tarjeta(
            "Sede de referencia",
            info["sede"],
            "📍",
        )

    with c2:
        mostrar_tarjeta(
            "Área principal",
            f"Análisis ambiental de referencia: {info['area_principal']}.",
            "🧭",
        )

    with c3:
        mostrar_tarjeta(
            "Contexto",
            info["contexto"],
            "🌎",
        )

    st.info(
        "Los mapas temáticos disponibles fueron incorporados como imágenes de "
        "referencia para evitar cargar capas SIG pesadas dentro del prototipo."
    )

# =========================================================
# CLIMA
# =========================================================

elif seccion == "Clima":
    st.title(f"🌧️ Clima de {territorio}")
    st.caption("SIAMS · análisis climático por fuente y calidad de datos")

    # -----------------------------------------------------
    # TUMACO: IDEAM como observación + NASA POWER continuo
    # -----------------------------------------------------
    if territorio == "Tumaco":
        faltantes = []
        if ARCHIVO_IDEAM_TUMACO is None:
            faltantes.append("ANALISIS_HIDROMETEOROLOGICO_Tumaco*.xlsx")
        if ARCHIVO_NASA_TUMACO is None:
            faltantes.append("NASA_POWER_TUMACO*.xlsx")

        if faltantes:
            st.error(
                "Faltan los archivos climáticos de Tumaco junto a `app.py`: "
                + ", ".join(faltantes)
            )
            st.info(
                "La página no mezcla datos inventados. Cuando subas ambos Excel, "
                "se activarán las comparaciones y decisiones por variable."
            )
        else:
            try:
                df_nasa, ind_nasa = cargar_nasa_tumaco(str(ARCHIVO_NASA_TUMACO))
                df_ideam, ind_ideam, control_ideam, fuentes_ideam = cargar_ideam_tumaco(
                    str(ARCHIVO_IDEAM_TUMACO)
                )
                df = df_ideam.merge(df_nasa, on="Mes", how="inner")

                st.success(
                    f"IDEAM: `{ARCHIVO_IDEAM_TUMACO.name}` · "
                    f"NASA POWER: `{ARCHIVO_NASA_TUMACO.name}`"
                )

                p_ideam_anual = df["Precipitación IDEAM (mm)"].sum()
                p_nasa_anual = df["Precipitación NASA (mm)"].sum()
                diferencia_p = (p_nasa_anual / p_ideam_anual - 1) * 100 if p_ideam_anual else float("nan")

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
                m4.metric("NASA frente a IDEAM", f"{diferencia_p:.1f} %")

                st.markdown(dedent("""
                    <div class="soft-box">
                        <strong>Criterio adoptado:</strong> la precipitación IDEAM se usa como
                        referencia principal por su alta completitud. NASA POWER se conserva
                        para comparar y para variables sin observación terrestre suficiente.
                        Las dos fuentes se muestran separadas y no se fusionan para rellenar faltantes.
                    </div>
                    """).strip(), unsafe_allow_html=True)

                st.markdown(
                    f'<div class="interpretation-box"><strong>Síntesis automática:</strong><br>{interpretacion_tumaco(df, control_ideam)}</div>',
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
                        title="Régimen mensual multianual de precipitación",
                    )
                    fig.update_layout(
                        xaxis_title="Mes",
                        yaxis_title="Precipitación mensual (mm)",
                        legend_title_text="Fuente",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    mes_max = df.loc[df["Precipitación IDEAM (mm)"].idxmax()]
                    mes_min = df.loc[df["Precipitación IDEAM (mm)"].idxmin()]
                    st.info(
                        f"Con IDEAM, el máximo mensual ocurre en **{mes_max['Mes']}** "
                        f"({mes_max['Precipitación IDEAM (mm)']:.1f} mm) y el mínimo en "
                        f"**{mes_min['Mes']}** ({mes_min['Precipitación IDEAM (mm)']:.1f} mm). "
                        f"La suma climatológica NASA es {abs(diferencia_p):.1f} % menor que la IDEAM."
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
                        key="temperatura_tumaco",
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
                        title=f"{seleccion_t}: comparación mensual",
                        xaxis_title="Mes",
                        yaxis_title="Temperatura (°C)",
                        legend=dict(orientation="h", y=-0.2),
                        margin=dict(b=80),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    diferencia_media = (df[col_n] - df[col_i]).mean()
                    st.caption(
                        f"Diferencia mensual promedio NASA − IDEAM: {diferencia_media:+.2f} °C. "
                        "La comparación es regional porque las variables IDEAM provienen de estaciones específicas."
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
                        title="Humedad relativa mensual",
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
                    st.warning(
                        f"La humedad IDEAM tiene {comp_hr:.2f} % de completitud. "
                        f"NASA presenta en la climatología mensual una diferencia media de "
                        f"{diferencia_hr:+.2f} puntos porcentuales frente a IDEAM. "
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
                        key="otras_nasa_tumaco",
                    )
                    columna = opciones[seleccion]
                    fig = px.line(
                        df,
                        x="Mes",
                        y=columna,
                        markers=True,
                        title=f"Régimen mensual de {seleccion.lower()}",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(
                        "Estas variables se presentan con NASA POWER porque el archivo IDEAM "
                        "procesado no contiene series equivalentes para Tumaco."
                    )

                with tab_calidad:
                    st.subheader("Decisión de uso por variable")
                    st.dataframe(
                        decisiones_climaticas_tumaco(control_ideam),
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
                        with open(ARCHIVO_IDEAM_TUMACO, "rb") as archivo:
                            st.download_button(
                                "Descargar base IDEAM procesada",
                                data=archivo.read(),
                                file_name=ARCHIVO_IDEAM_TUMACO.name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="descarga_ideam_tumaco",
                            )
                    with c2:
                        with open(ARCHIVO_NASA_TUMACO, "rb") as archivo:
                            st.download_button(
                                "Descargar base NASA POWER",
                                data=archivo.read(),
                                file_name=ARCHIVO_NASA_TUMACO.name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="descarga_nasa_tumaco",
                            )

            except Exception as error:
                st.error(
                    "Se encontraron los Excel de Tumaco, pero ocurrió un error al procesarlos."
                )
                st.code(str(error), language=None)

    # -----------------------------------------------------
    # LETICIA, MEDELLÍN Y SAN ANDRÉS: NASA POWER
    # -----------------------------------------------------
    else:
        archivo_nasa = ARCHIVOS_CLIMA_NASA.get(territorio)
        indicadores = {}
        datos_reales = archivo_nasa is not None

        if datos_reales:
            try:
                df, indicadores = cargar_clima_leticia(str(archivo_nasa))
                st.success(
                    f"Datos reales cargados desde `{archivo_nasa.name}` · Fuente: NASA POWER."
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
            }
            st.warning(
                f"No se encontró el Excel de NASA POWER para **{territorio}**. "
                f"Ponlo al mismo nivel de `app.py` con un nombre que comience por "
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
                            file_name=archivo_nasa.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"descarga_clima_{territorio}",
                        )

# =========================================================
# HIDROLOGÍA
# =========================================================

elif seccion == "Hidrología":
    st.title(f"💦 Hidrología de {territorio}")

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

    else:  # Medellín
        mostrar_mapa_imagen(
            "inundacion", "Amenaza por inundaciones en Medellín",
            "Alcaldía de Medellín – Plan de Ordenamiento Territorial (POT)",
            "La cartografía muestra sectores con distintos niveles de amenaza por inundación. Debe interpretarse según la escala y metodología del POT.",
        )
        st.caption("Para una siguiente versión conviene complementar este componente con la red hídrica y las microcuencas/quebradas del Valle de Aburrá.")

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
        else:
            mostrar_mapa_imagen("geologia", "Plancha geológica 228 – Medellín", "Servicio Geológico Colombiano (SGC)")

    with tab2:
        st.warning(
            "La imagen geológica ya está incorporada, pero todavía no se ha transcrito y validado "
            "la tabla completa de códigos, edades y litologías de la leyenda. Para evitar errores, "
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

    st.markdown(dedent("""
        <div class="warning-box">
            <strong>Nota:</strong> La plataforma debe diferenciar claramente entre
            información oficial, interpretación general y resultados propios del semillero.
        </div>
        """).strip(), unsafe_allow_html=True)

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
# COBERTURA Y RELIEVE
# =========================================================

elif seccion == "Cobertura y relieve":
    st.title(f"🌿 Cobertura y relieve de {territorio}")

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
    else:
        st.info("Para San Andrés todavía no se incorporó una capa específica de cobertura o relieve. La versión actual prioriza geología, acuíferos, nitratos y microcuencas.")

# =========================================================
# ESTACIONES Y DATOS
# =========================================================

elif seccion == "Estaciones y datos":
    st.title(f"📚 Estaciones y disponibilidad de datos – {territorio}")

    if territorio == "Tumaco" and ARCHIVO_IDEAM_TUMACO is not None:
        try:
            _, _, control_ideam, fuentes_ideam = cargar_ideam_tumaco(
                str(ARCHIVO_IDEAM_TUMACO)
            )
            st.subheader("Resumen de decisión por variable")
            st.dataframe(
                decisiones_climaticas_tumaco(control_ideam),
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
        except Exception as error:
            st.error("No fue posible leer el inventario IDEAM de Tumaco.")
            st.code(str(error), language=None)
    else:
        st.dataframe(
            tabla_disponibilidad(territorio),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown(
        """
        Para cada estación se documentan nombre, código, tipo, estado, coordenadas,
        variable, periodo, registros, completitud y criterio de uso. En Tumaco, las
        variables no necesariamente provienen de la misma estación; esto debe conservarse
        visible al interpretar comparaciones con NASA POWER.
        """
    )

# =========================================================
# MONITOREO Y CURVAS
# =========================================================

elif seccion == "Monitoreo y curvas":
    st.title(f"📡 Monitoreo y curvas – {territorio}")

    st.warning(
        "Actualmente no se dispone de series de sondas o nivel validadas para este territorio. "
        "Por esa razón se retiraron las gráficas demostrativas del prototipo."
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

    st.title("⚖️ Comparación climática de los cuatro territorios")

    st.markdown(
        """
        <div class="soft-box">
            <strong>Criterio de comparación:</strong>
            Leticia, Medellín y San Andrés utilizan NASA POWER como fuente climática principal.
            En Tumaco, IDEAM se conserva como referencia principal para precipitación y temperatura,
            mientras que NASA POWER se usa como complemento para otras variables.
            La comparación es descriptiva porque las fuentes y periodos no son idénticos.
        </div>
        """,
        unsafe_allow_html=True,
    )

    datasets = []
    fuentes_resumen = []

    # -----------------------------------------------------
    # LETICIA / MEDELLÍN / SAN ANDRÉS
    # -----------------------------------------------------
    for nombre in ("Leticia", "Medellín", "San Andrés"):

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
    # TUMACO
    # -----------------------------------------------------
    if ARCHIVO_IDEAM_TUMACO is not None:

        try:
            df_tumaco_ideam, _, _, _ = cargar_ideam_tumaco(
                str(ARCHIVO_IDEAM_TUMACO)
            )

            df_tumaco = df_tumaco_ideam.copy()

            # Agregar NASA Tumaco para humedad, viento, presión y radiación si existe.
            if ARCHIVO_NASA_TUMACO is not None:
                try:
                    df_tumaco_nasa, _ = cargar_nasa_tumaco(
                        str(ARCHIVO_NASA_TUMACO)
                    )
                    df_tumaco = df_tumaco.merge(
                        df_tumaco_nasa,
                        on="Mes",
                        how="left",
                    )
                except Exception:
                    pass

            temporal = pd.DataFrame({
                "Mes": df_tumaco["Mes"],
                "Precipitación mensual (mm)": df_tumaco["Precipitación IDEAM (mm)"],
                "Temperatura media (°C)": df_tumaco["Temperatura media IDEAM (°C)"],
                "Temperatura máxima (°C)": (
                    df_tumaco["Temperatura máxima IDEAM (°C)"]
                    if "Temperatura máxima IDEAM (°C)" in df_tumaco.columns
                    else pd.NA
                ),
                "Temperatura mínima (°C)": (
                    df_tumaco["Temperatura mínima IDEAM (°C)"]
                    if "Temperatura mínima IDEAM (°C)" in df_tumaco.columns
                    else pd.NA
                ),
                "Humedad relativa (%)": (
                    df_tumaco["Humedad NASA (%)"]
                    if "Humedad NASA (%)" in df_tumaco.columns
                    else (
                        df_tumaco["Humedad IDEAM (%)"]
                        if "Humedad IDEAM (%)" in df_tumaco.columns
                        else pd.NA
                    )
                ),
                "Viento a 2 m (m/s)": (
                    df_tumaco["Viento a 2 m NASA (m/s)"]
                    if "Viento a 2 m NASA (m/s)" in df_tumaco.columns
                    else pd.NA
                ),
                "Presión superficial (kPa)": (
                    df_tumaco["Presión NASA (kPa)"]
                    if "Presión NASA (kPa)" in df_tumaco.columns
                    else pd.NA
                ),
                "Radiación solar (kWh/m²/día)": (
                    df_tumaco["Radiación NASA (kWh/m²/día)"]
                    if "Radiación NASA (kWh/m²/día)" in df_tumaco.columns
                    else pd.NA
                ),
                "Territorio": "Tumaco",
                "Fuente principal": "IDEAM + NASA POWER",
            })

            datasets.append(temporal)

            fuentes_resumen.append({
                "Territorio": "Tumaco",
                "Precipitación": "IDEAM",
                "Temperatura": "IDEAM",
                "Humedad": "NASA POWER + contraste IDEAM",
                "Viento / presión / radiación": "NASA POWER",
            })

        except Exception:
            pass

    # -----------------------------------------------------
    # VISUALIZACIÓN
    # -----------------------------------------------------
    if datasets:

        comparar = pd.concat(
            datasets,
            ignore_index=True,
            sort=False,
        )

        tab_p, tab_t, tab_hr, tab_otras, tab_resumen, tab_fuentes = st.tabs(
            [
                "Precipitación",
                "Temperatura",
                "Humedad",
                "Viento, presión y radiación",
                "Resumen anual",
                "Fuentes",
            ]
        )

        # -------------------------------------------------
        # PRECIPITACIÓN
        # -------------------------------------------------
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

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            st.caption(
                "Tumaco utiliza precipitación IDEAM; Leticia, Medellín y San Andrés utilizan NASA POWER."
            )

        # -------------------------------------------------
        # TEMPERATURA
        # -------------------------------------------------
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

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            # Rango térmico mensual por territorio
            resumen_temp = (
                comparar
                .groupby("Territorio")
                .agg(
                    Temperatura_media_C=("Temperatura media (°C)", "mean"),
                    Temperatura_min_media_C=("Temperatura media (°C)", "min"),
                    Temperatura_max_media_C=("Temperatura media (°C)", "max"),
                )
                .reset_index()
            )

            resumen_temp["Amplitud_media_mensual_C"] = (
                resumen_temp["Temperatura_max_media_C"]
                - resumen_temp["Temperatura_min_media_C"]
            )

            st.dataframe(
                resumen_temp.round(2),
                use_container_width=True,
                hide_index=True,
            )

        # -------------------------------------------------
        # HUMEDAD
        # -------------------------------------------------
        with tab_hr:

            datos_hr = comparar.dropna(
                subset=["Humedad relativa (%)"]
            )

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

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

                st.caption(
                    "En Tumaco se usa NASA POWER como referencia continua de humedad, con IDEAM como contraste cuando está disponible."
                )

            else:
                st.info("No hay datos de humedad disponibles para comparar.")

        # -------------------------------------------------
        # OTRAS VARIABLES
        # -------------------------------------------------
        with tab_otras:

            opciones = {
                "Viento a 2 m": "Viento a 2 m (m/s)",
                "Presión superficial": "Presión superficial (kPa)",
                "Radiación solar": "Radiación solar (kWh/m²/día)",
            }

            seleccion = st.selectbox(
                "Variable",
                list(opciones.keys()),
                key="comparacion_otras_4_territorios",
            )

            columna = opciones[seleccion]

            datos_variable = comparar.dropna(
                subset=[columna]
            )

            if not datos_variable.empty:

                fig = px.line(
                    datos_variable,
                    x="Mes",
                    y=columna,
                    color="Territorio",
                    markers=True,
                    title=f"{seleccion} · comparación entre territorios",
                )

                fig.update_layout(
                    xaxis_title="Mes",
                    legend_title_text="Territorio",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

                st.caption(
                    "Estas variables se comparan principalmente con NASA POWER para mantener una fuente homogénea entre territorios."
                )

            else:
                st.info(
                    f"No hay suficientes datos de {seleccion.lower()} para construir la comparación."
                )

        # -------------------------------------------------
        # RESUMEN ANUAL
        # -------------------------------------------------
        with tab_resumen:

            resumen = (
                comparar
                .groupby("Territorio")
                .agg(
                    Precipitacion_anual_mm=(
                        "Precipitación mensual (mm)",
                        "sum",
                    ),
                    Temperatura_media_C=(
                        "Temperatura media (°C)",
                        "mean",
                    ),
                    Humedad_media_pct=(
                        "Humedad relativa (%)",
                        "mean",
                    ),
                    Viento_medio_m_s=(
                        "Viento a 2 m (m/s)",
                        "mean",
                    ),
                    Presion_media_kPa=(
                        "Presión superficial (kPa)",
                        "mean",
                    ),
                    Radiacion_media_kWh_m2_dia=(
                        "Radiación solar (kWh/m²/día)",
                        "mean",
                    ),
                )
                .reset_index()
            )

            st.dataframe(
                resumen.round(2),
                use_container_width=True,
                hide_index=True,
            )

            if not resumen.empty:
                mas_lluvioso = resumen.loc[
                    resumen["Precipitacion_anual_mm"].idxmax()
                ]

                mas_calido = resumen.loc[
                    resumen["Temperatura_media_C"].idxmax()
                ]

                mas_humedo = resumen.dropna(
                    subset=["Humedad_media_pct"]
                )

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
                    fila_h = mas_humedo.loc[
                        mas_humedo["Humedad_media_pct"].idxmax()
                    ]
                    c3.metric(
                        "Mayor humedad media",
                        fila_h["Territorio"],
                        f"{fila_h['Humedad_media_pct']:.1f} %",
                    )

        # -------------------------------------------------
        # FUENTES
        # -------------------------------------------------
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
            "No se encontraron suficientes archivos climáticos para construir la comparación de los cuatro territorios."
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

    if modo_presentacion:
        st.info(
            "🎤 Vista simplificada de presentación: se ocultan los botones de descarga "
            "y el diagnóstico técnico del proyecto."
        )

    st.title("📂 Fuentes y descargas")

    tab_archivos, tab_mapas, tab_fuentes = st.tabs([
        "Archivos climáticos", "Estado de mapas", "Inventario de fuentes"
    ])

    with tab_archivos:
        st.write(
            "Los botones se habilitan únicamente cuando el archivo existe junto al script o en una carpeta de datos reconocida."
        )
        archivos = [
            ("NASA POWER · Leticia", ARCHIVO_CLIMA_LETICIA, "descarga_fuente_leticia"),
            ("NASA POWER · Medellín", ARCHIVO_CLIMA_MEDELLIN, "descarga_fuente_medellin"),
            ("NASA POWER · San Andrés", ARCHIVO_CLIMA_SAN_ANDRES, "descarga_fuente_san_andres"),
            ("NASA POWER · Tumaco", ARCHIVO_NASA_TUMACO, "descarga_fuente_nasa_tumaco"),
            ("IDEAM procesado · Tumaco", ARCHIVO_IDEAM_TUMACO, "descarga_fuente_ideam_tumaco"),
        ]
        estado = []
        for etiqueta, ruta, clave_boton in archivos:
            estado.append({
                "Archivo": etiqueta,
                "Nombre detectado": Path(ruta).name if ruta else "—",
                "Estado": archivo_disponible(ruta),
            })
            if ruta is not None and Path(ruta).exists():
                with open(ruta, "rb") as archivo:
                    st.download_button(
                        f"Descargar {etiqueta}",
                        data=archivo.read(),
                        file_name=Path(ruta).name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=clave_boton,
                    )
        st.dataframe(pd.DataFrame(estado), use_container_width=True, hide_index=True)

    with tab_mapas:
        st.write(f"**Carpeta detectada:** `{CARPETA_MAPAS}`")
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
        st.dataframe(pd.DataFrame(estado_mapas), use_container_width=True, hide_index=True)

    with tab_fuentes:
        fuentes = pd.DataFrame({
            "Fuente": [
                "IDEAM", "NASA POWER", "Instituto SINCHI", "Corpoamazonia",
                "CORPONARIÑO / POMCA Río Mira", "Parques Nacionales", "SENA",
                "CORALINA", "Servicio Geológico Colombiano", "Alcaldía de Medellín / POT", "SIAMS",
            ],
            "Uso": [
                "Series terrestres y control de completitud", "Variables climáticas continuas",
                "Mapas regionales de Leticia", "Humedales e inundación de Leticia",
                "Geología, cobertura, relieve e inundación de Tumaco", "Contexto hídrico y costero de Tumaco",
                "Referencia académica de pozos e IRCA en Leticia",
                "Geología, acuíferos, nitratos y microcuencas de San Andrés",
                "Plancha geológica 228 de Medellín", "Estructura ecológica y amenaza por inundación de Medellín",
                "Procesamiento, decisiones de uso e integración web",
            ],
            "Condición": [
                "Principal o complementaria según variable", "Principal o complementaria según variable",
                "Referencia cartográfica", "Referencia cartográfica", "Referencia cartográfica",
                "Referencia cartográfica", "Referencia académica complementaria", "Referencia cartográfica",
                "Referencia cartográfica oficial", "Referencia cartográfica oficial", "Producto académico",
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
    f"Territorio seleccionado: {territorio} · Nivel: {publico} · Actualización: {FECHA_ACTUALIZACION}"
)