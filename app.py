from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

VERSION_APP = "PROTOTIPO-SIAMS-V8-2026-08-04"
FECHA_ACTUALIZACION = "4 de agosto de 2026"

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
    :root {
        --verde-oscuro: #0b3d36;
        --verde: #146c5c;
        --verde-claro: #eaf5f1;
        --fondo: #f5f8f7;
        --texto: #17312d;
        --gris: #6c7e7a;
        --borde: #dce7e4;
        --blanco: #ffffff;
    }

    .stApp {
        background: var(--fondo);
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b3d36 0%, #124f45 100%);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: white;
    }

    /* Corrige el texto de los selectores, que tienen fondo blanco */
    [data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #17312d !important;
    }

    [data-testid="stSidebar"] div[data-baseweb="select"] {
        background: white;
        border-radius: 10px;
    }

    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stSelectbox label {
        font-weight: 650;
    }

    .hero {
        padding: 3.2rem 3rem;
        border-radius: 24px;
        color: white;
        background:
            linear-gradient(90deg, rgba(7, 53, 49, 0.97), rgba(18, 112, 91, 0.80));
        margin-bottom: 1.5rem;
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.15);
    }

    .hero h1 {
        font-size: 3.2rem;
        line-height: 1.05;
        margin: 0.35rem 0 0.8rem 0;
        color: white;
    }

    .hero p {
        max-width: 900px;
        font-size: 1.08rem;
        line-height: 1.75;
        margin-bottom: 0;
        color: white;
    }

    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.12rem;
        font-size: 0.80rem;
        font-weight: 800;
        opacity: 0.88;
    }

    .section-title {
        color: var(--verde-oscuro);
        font-size: 1.75rem;
        font-weight: 800;
        margin: 1.2rem 0 0.8rem 0;
    }

    .card {
        background: white;
        border: 1px solid var(--borde);
        border-radius: 18px;
        padding: 1.3rem 1.4rem;
        min-height: 170px;
        box-shadow: 0 6px 18px rgba(20, 70, 60, 0.07);
        margin-bottom: 0.8rem;
    }

    .card h3 {
        color: var(--verde);
        margin-top: 0;
        margin-bottom: 0.6rem;
    }

    .card p {
        color: var(--texto);
        line-height: 1.65;
    }

    .soft-box {
        background: var(--verde-claro);
        border-left: 5px solid var(--verde);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin: 0.8rem 0 1rem 0;
    }

    .warning-box {
        background: #fff7e8;
        border-left: 5px solid #d99a1b;
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin: 0.8rem 0 1rem 0;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid var(--borde);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 5px 14px rgba(20, 70, 60, 0.06);
    }

    div[data-testid="stTabs"] button {
        font-size: 0.98rem;
        font-weight: 700;
    }

    .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 0.85rem;
        margin: 0.9rem 0 1.4rem 0;
    }

    .status-card {
        background: white;
        border: 1px solid var(--borde);
        border-radius: 16px;
        padding: 1rem 1.05rem;
        box-shadow: 0 5px 14px rgba(20, 70, 60, 0.06);
    }

    .status-card h4 {
        color: var(--verde-oscuro);
        margin: 0 0 0.45rem 0;
        font-size: 1rem;
    }

    .status-pill {
        display: inline-block;
        border-radius: 999px;
        padding: 0.22rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 800;
        margin-bottom: 0.45rem;
    }

    .status-completo { background: #daf3e7; color: #126447; }
    .status-proceso { background: #fff0c7; color: #8a5a00; }
    .status-pendiente { background: #eceff1; color: #52606d; }
    .status-nodatos { background: #f8dfe1; color: #9c2631; }

    .metadata-box {
        background: #ffffff;
        border: 1px solid var(--borde);
        border-radius: 14px;
        padding: 0.9rem 1rem;
        margin: 0.75rem 0 1rem 0;
        font-size: 0.94rem;
        line-height: 1.55;
    }

    .interpretation-box {
        background: #eef5ff;
        border-left: 5px solid #386fa4;
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin: 0.8rem 0 1rem 0;
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

TERRITORIOS = {
    "Leticia": {
        "region": "Amazonía colombiana",
        "departamento": "Amazonas",
        "sede": "Universidad Nacional de Colombia – Sede Amazonia",
        "lat": -4.2153,
        "lon": -69.9406,
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
        "precipitacion": [
            260, 275, 320, 335, 310, 245,
            190, 175, 205, 250, 280, 300,
        ],
        "temperatura": [
            26.0, 26.1, 25.8, 25.6, 25.5, 25.2,
            25.0, 25.4, 26.0, 26.3, 26.2, 26.1,
        ],
        "humedad": [
            86, 86, 88, 89, 89, 88,
            86, 84, 84, 85, 86, 86,
        ],
        "hallazgo": (
            "La disponibilidad de series IDEAM continuas es limitada, por lo que "
            "NASA POWER se plantea como fuente climática principal para el prototipo."
        ),
    },
    "Tumaco": {
        "region": "Pacífico colombiano",
        "departamento": "Nariño",
        "sede": "Universidad Nacional de Colombia – Sede Tumaco",
        "lat": 1.8067,
        "lon": -78.7647,
        "area_principal": "25 km",
        "contexto": "Hasta 50 km",
        "fuente_clima": "IDEAM + NASA POWER",
        "estado_datos": "Series parciales complementadas",
        "descripcion": (
            "Tumaco se localiza en la costa pacífica colombiana. El territorio se "
            "caracteriza por elevada precipitación, alta humedad y una interacción "
            "permanente entre sistemas continentales, costeros, estuarinos y marinos."
        ),
        "precipitacion": [
            310, 285, 330, 390, 430, 360,
            280, 240, 265, 315, 345, 330,
        ],
        "temperatura": [
            26.2, 26.4, 26.3, 26.1, 25.9, 25.7,
            25.6, 25.7, 25.8, 26.0, 26.1, 26.2,
        ],
        "humedad": [
            84, 84, 85, 86, 87, 86,
            85, 84, 84, 85, 85, 84,
        ],
        "hallazgo": (
            "En Tumaco existen algunas series IDEAM útiles, aunque su continuidad "
            "debe evaluarse y complementarse con NASA POWER."
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
    st.markdown('<div class="status-grid">' + ''.join(tarjetas) + '</div>', unsafe_allow_html=True)


def resumen_estados(nombre_territorio: str) -> dict:
    estados = [fila[1] for fila in ESTADO_COMPONENTES[nombre_territorio]]
    return {estado: estados.count(estado) for estado in set(estados)}


def mostrar_ficha_mapa(nombre_territorio: str, clave: str) -> None:
    meta = METADATOS_MAPAS.get(nombre_territorio, {}).get(clave)
    if not meta:
        return
    st.markdown(
        f"""<div class="metadata-box">
            <strong>Producto:</strong> {meta['producto']}<br>
            <strong>Entidad:</strong> {meta['entidad']}<br>
            <strong>Alcance espacial:</strong> {meta['alcance']}<br>
            <strong>Referencia temporal:</strong> {meta['actualidad']}<br>
            <strong>Limitación:</strong> {meta['limitacion']}
        </div>""",
        unsafe_allow_html=True,
    )


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

MAPAS_POR_TERRITORIO = {
    "Leticia": MAPAS_LETICIA,
    "Tumaco": MAPAS_TUMACO,
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
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">Semillero SIAMS</div>
            <h1>{titulo}</h1>
            <p>{subtitulo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_tarjeta(titulo: str, texto: str, icono: str = "💧") -> None:
    st.markdown(
        f"""
        <div class="card">
            <h3>{icono} {titulo}</h3>
            <p>{texto}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def tabla_disponibilidad(nombre_territorio: str) -> pd.DataFrame:
    if nombre_territorio == "Leticia":
        return pd.DataFrame({
            "Variable": ["Precipitación", "Temperatura", "Humedad", "Presión", "Viento", "Radiación"],
            "IDEAM": ["Parcial", "Insuficiente", "Insuficiente", "No encontrada", "Limitada", "No encontrada"],
            "NASA POWER": ["Disponible"] * 6,
            "Uso preliminar": ["NASA POWER"] * 6,
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

territorio = st.sidebar.selectbox(
    "Territorio",
    ["Leticia", "Tumaco"],
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
        '<div class="section-title">Explorar territorios</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        mostrar_tarjeta(
            "Leticia",
            "Territorio amazónico asociado al río Amazonas, con alta precipitación, "
            "elevada humedad y disponibilidad limitada de series terrestres continuas.",
            "🌿",
        )

    with c2:
        mostrar_tarjeta(
            "Tumaco",
            "Territorio costero del Pacífico con sistemas fluviales, estuarinos y marinos, "
            "además de información climática parcial que puede complementarse.",
            "🌊",
        )

    st.markdown(
        '<div class="section-title">¿Qué contiene la plataforma?</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        mostrar_tarjeta(
            "Clima",
            "Series, regímenes mensuales, promedios y disponibilidad de datos.",
            "🌧️",
        )

    with c2:
        mostrar_tarjeta(
            "Territorio",
            "Mapas, hidrografía, humedales, cobertura, relieve y estaciones.",
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
            "Resultados revisados de sondas, curvas y eventos de respuesta.",
            "📡",
        )

    st.markdown('<div class="section-title">Estado del prototipo</div>', unsafe_allow_html=True)
    mapas_encontrados = sum(
        1 for mapas in MAPAS_POR_TERRITORIO.values()
        for nombre in mapas.values() if buscar_mapa(nombre) is not None
    )
    componentes_completos = sum(
        1 for territorio_estado in ESTADO_COMPONENTES.values()
        for _, estado, _ in territorio_estado if estado == "Completo"
    )
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Territorios", "2")
    m2.metric("Mapas incorporados", f"{mapas_encontrados}/13")
    m3.metric("Componentes completos", componentes_completos)
    m4.metric("Actualización", FECHA_ACTUALIZACION)

    st.info(
        "El prototipo diferencia información completa, información en proceso, componentes pendientes "
        "y secciones sin datos. No se presentan valores demostrativos como si fueran resultados reales."
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

    st.markdown(
        f"""
        <div class="soft-box">
            <strong>Fuente climática principal:</strong> {info["fuente_clima"]}<br>
            <strong>Estado de los datos:</strong> {info["estado_datos"]}<br>
            <strong>Sede de referencia:</strong> {info["sede"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    st.map(mapa, zoom=11 if territorio == "Leticia" else 10)

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

                st.markdown(
                    """
                    <div class="soft-box">
                        <strong>Criterio adoptado:</strong> la precipitación IDEAM se usa como
                        referencia principal por su alta completitud. NASA POWER se conserva
                        para comparar y para variables sin observación terrestre suficiente.
                        Las dos fuentes se muestran separadas y no se fusionan para rellenar faltantes.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

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
    # LETICIA: se conserva el lector NASA POWER existente
    # -----------------------------------------------------
    else:
        indicadores = {}
        datos_reales = ARCHIVO_CLIMA_LETICIA is not None

        if datos_reales:
            try:
                df, indicadores = cargar_clima_leticia(str(ARCHIVO_CLIMA_LETICIA))
                st.success(
                    f"Datos reales cargados desde `{ARCHIVO_CLIMA_LETICIA.name}` · Fuente: NASA POWER."
                )
            except Exception as error:
                datos_reales = False
                df = clima_prototipo(info)
                st.error(
                    "Se encontró el Excel, pero ocurrió un error al procesarlo. "
                    "La aplicación usará temporalmente los valores de respaldo."
                )
                st.code(str(error), language=None)
        else:
            df = clima_prototipo(info)
            st.warning(
                "No se encontró el Excel de NASA POWER. Súbelo al mismo nivel de "
                "`app.py` con un nombre que comience por `NASA_POWER_LETICIA`."
            )

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

            st.markdown(
                f"""
                <div class="soft-box">
                    <strong>Humedad relativa media del periodo:</strong> {float(hr_media):.2f} %<br>
                    <strong>Tratamiento:</strong> régimen mensual multianual calculado a partir de datos diarios.<br>
                    <strong>Nota:</strong> la precipitación corresponde al total mensual climatológico.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="interpretation-box"><strong>Síntesis automática:</strong><br>{interpretacion_leticia(df)}</div>',
                unsafe_allow_html=True,
            )

        tab1, tab2, tab3, tab4 = st.tabs([
            "Precipitación",
            "Temperatura y humedad",
            "Viento, presión y radiación",
            "Tabla",
        ])

        with tab1:
            fig = px.bar(
                df,
                x="Mes",
                y="Precipitación mensual (mm)",
                title="Régimen mensual multianual de precipitación",
                text_auto=".1f",
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["Mes"], y=df["Temperatura media (°C)"],
                mode="lines+markers", name="Temperatura media",
            ))
            if "Temperatura máxima (°C)" in df.columns:
                fig.add_trace(go.Scatter(
                    x=df["Mes"], y=df["Temperatura máxima (°C)"],
                    mode="lines", name="Temperatura máxima", line=dict(dash="dot"),
                ))
                fig.add_trace(go.Scatter(
                    x=df["Mes"], y=df["Temperatura mínima (°C)"],
                    mode="lines", name="Temperatura mínima", line=dict(dash="dot"),
                ))
            fig.add_trace(go.Scatter(
                x=df["Mes"], y=df["Humedad relativa (%)"],
                mode="lines+markers", name="Humedad relativa", yaxis="y2",
            ))
            fig.update_layout(
                title="Temperatura y humedad relativa",
                yaxis=dict(title="Temperatura (°C)"),
                yaxis2=dict(title="Humedad (%)", overlaying="y", side="right", range=[0, 100]),
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
            if all(col in df.columns for col in columnas_otras):
                variable = st.selectbox(
                    "Variable climática", columnas_otras, key="variable_clima_leticia"
                )
                fig = px.line(df, x="Mes", y=variable, markers=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Estas variables se mostrarán cuando exista el archivo procesado.")

        with tab4:
            st.dataframe(df.round(2), use_container_width=True, hide_index=True)
            if datos_reales:
                with open(ARCHIVO_CLIMA_LETICIA, "rb") as archivo_excel:
                    st.download_button(
                        "Descargar base climática procesada",
                        data=archivo_excel.read(),
                        file_name=ARCHIVO_CLIMA_LETICIA.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="descarga_clima_leticia",
                    )

# =========================================================
# HIDROLOGÍA
# =========================================================

elif seccion == "Hidrología":
    st.title(f"💦 Hidrología de {territorio}")

    if territorio == "Leticia":
        mostrar_mapa_imagen(
            "hidrografia",
            "Mapa de hidrografía del municipio de Leticia",
            "Instituto Amazónico de Investigaciones Científicas SINCHI",
            """
            El mapa permite reconocer la extensa red de drenaje del municipio,
            compuesta por ríos, quebradas, caños y cuerpos de agua conectados con
            el sistema fluvial amazónico. Se utiliza como referencia municipal;
            el área principal del prototipo SIAMS se concentra alrededor de la sede.
            """,
        )

        c1, c2 = st.columns(2)

        with c1:
            with st.expander("Ver mapa regional de humedales", expanded=False):
                mostrar_mapa_imagen(
                    "humedales",
                    "Humedales de Leticia y Puerto Nariño",
                    "Corpoamazonia",
                    "Mapa regional complementario; no todos los humedales representados "
                    "se localizan dentro del área inmediata de la sede.",
                )

        with c2:
            with st.expander("Ver mapa de inundación urbana", expanded=False):
                mostrar_mapa_imagen(
                    "inundacion",
                    "Áreas de inundación en la zona urbana de Leticia",
                    "Corpoamazonia",
                    "La imagen se usa como antecedente territorial y debe interpretarse "
                    "de acuerdo con el año, la escala y la metodología de la fuente.",
                )

    else:
        mostrar_mapa_imagen(
            "hidrografia",
            "Sistemas hídricos de Tumaco y el Bajo Mira",
            "Parques Nacionales Naturales de Colombia",
            """
            El mapa presenta el contexto hidrográfico regional de Tumaco, el Bajo Mira
            y la zona costera. Permite reconocer la relación entre ríos, esteros,
            manglares y ambientes marino-costeros. Su alcance es regional y no se limita
            exclusivamente al entorno inmediato de la Sede Tumaco.
            """,
        )

        c1, c2 = st.columns(2)

        with c1:
            with st.expander("Ver mapa regional de manglares", expanded=False):
                mostrar_mapa_imagen(
                    "manglares",
                    "Distribución regional de manglares en Nariño",
                    "CORPONARIÑO y entidades participantes",
                    "El mapa se utiliza como referencia ambiental regional. Debe leerse "
                    "considerando el año de elaboración y la escala indicada en la imagen.",
                )

        with c2:
            with st.expander("Ver mapa de amenaza por inundación", expanded=False):
                mostrar_mapa_imagen(
                    "inundacion",
                    "Amenaza por inundación en la cuenca del río Mira",
                    "CORPONARIÑO – POMCA Río Mira",
                    "La clasificación de amenaza debe interpretarse según la metodología, "
                    "la escala y el periodo del POMCA.",
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
            mostrar_mapa_imagen(
                "geologia",
                "Distribución espacial de las unidades geológicas del Trapecio Sur",
                "Instituto SINCHI, con base en información geológica regional",
                "El mapa tiene alcance regional y sirve para contextualizar las unidades "
                "geológicas presentes en el sector del Trapecio Sur.",
            )
        else:
            mostrar_mapa_imagen(
                "geologia",
                "Unidades geológicas de la cuenca hidrográfica del río Mira",
                "CORPONARIÑO – POMCA Río Mira",
                "El mapa permite contextualizar la geología regional de Tumaco y la cuenca "
                "del río Mira. No representa exclusivamente el entorno inmediato de la sede.",
            )

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
            "pozos_irca",
            "Distribución de pozos de agua subterránea en Leticia",
            "SENA – recurso académico de aguas subterráneas de Leticia",
            "El mapa se incorpora como referencia académica complementaria. La ubicación "
            "de los puntos debe leerse junto con la fuente, el periodo y el uso reportado.",
        )

    st.markdown(
        """
        <div class="warning-box">
            <strong>Nota:</strong> La plataforma debe diferenciar claramente entre
            información oficial, interpretación general y resultados propios del semillero.
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# HIDROGEOQUÍMICA
# =========================================================

elif seccion == "Hidrogeoquímica":
    st.title(f"🧪 Hidrogeoquímica de {territorio}")

    st.write(
        "Esta sección mostrará puntos de muestreo, parámetros fisicoquímicos y, "
        "cuando los datos lo permitan, diagramas hidroquímicos."
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

    tab1, tab2 = st.tabs(
        [
            "Cobertura",
            "Relieve y geomorfología",
        ]
    )

    with tab1:
        if territorio == "Leticia":
            mostrar_mapa_imagen(
                "cobertura",
                "Coberturas de la tierra del municipio de Leticia",
                "Instituto SINCHI",
                "El mapa permite diferenciar bosques, áreas transformadas, cuerpos de "
                "agua y otras coberturas. Debe conservarse visible el año de la fuente.",
            )
        else:
            mostrar_mapa_imagen(
                "cobertura",
                "Cobertura y uso actual de la tierra en la cuenca del río Mira",
                "CORPONARIÑO – POMCA Río Mira",
                "La imagen permite reconocer bosques, manglares, áreas agrícolas, cuerpos "
                "de agua y zonas transformadas en el contexto regional de Tumaco.",
            )

    with tab2:
        if territorio == "Leticia":
            mostrar_mapa_imagen(
                "relieve",
                "Geomorfología y características generales del relieve del Trapecio Sur",
                "Instituto SINCHI",
                "Esta imagen se utiliza para interpretar las formas generales del terreno. "
                "No reemplaza un DEM ni un análisis detallado de pendientes.",
            )
        else:
            mostrar_mapa_imagen(
                "relieve",
                "Distribución de pendientes en la cuenca hidrográfica del río Mira",
                "CORPONARIÑO – POMCA Río Mira",
                "El mapa presenta las clases de pendiente del contexto regional. No reemplaza "
                "un análisis detallado del relieve específico alrededor de la sede.",
            )

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

    st.markdown(
        """
        <div class="soft-box">
            <strong>Criterio de publicación:</strong> esta sección solo se habilitará cuando las
            series hayan sido procesadas externamente, revisadas y acompañadas por una metodología.
            La página mostrará resultados finales; no realizará el procesamiento de sondas en línea.
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# COMPARAR TERRITORIOS
# =========================================================

elif seccion == "Comparar territorios":
    st.title("⚖️ Comparación entre Leticia y Tumaco")

    st.markdown(
        """
        La comparación utiliza la fuente principal definida para cada territorio:
        **NASA POWER para Leticia** y **IDEAM para la precipitación y temperatura de Tumaco**.
        Es una comparación descriptiva, porque las fuentes, estaciones y periodos no son idénticos.
        """
    )

    comparacion = pd.DataFrame({
        "Aspecto": [
            "Región", "Condición hídrica", "Fuente principal de precipitación",
            "Fuente principal de temperatura", "Disponibilidad terrestre",
            "Cartografía incorporada", "Área principal",
        ],
        "Leticia": [
            "Amazonía", "Fluvial amazónica", "NASA POWER", "NASA POWER",
            "IDEAM limitada", "7 mapas regionales", "15 km",
        ],
        "Tumaco": [
            "Pacífico", "Costera, estuarina y fluvial", "IDEAM", "IDEAM + NASA",
            "IDEAM variable según parámetro", "6 mapas regionales", "25 km",
        ],
    })
    st.dataframe(comparacion, use_container_width=True, hide_index=True)

    datos_completos = (
        ARCHIVO_CLIMA_LETICIA is not None
        and ARCHIVO_IDEAM_TUMACO is not None
        and ARCHIVO_NASA_TUMACO is not None
    )

    if datos_completos:
        try:
            leticia_df, _ = cargar_clima_leticia(str(ARCHIVO_CLIMA_LETICIA))
            tumaco_i, _, _, _ = cargar_ideam_tumaco(str(ARCHIVO_IDEAM_TUMACO))
            tumaco_n, _ = cargar_nasa_tumaco(str(ARCHIVO_NASA_TUMACO))
            tumaco_df = tumaco_i.merge(tumaco_n, on="Mes", how="inner")

            tab_p, tab_t, tab_fuentes, tab_estado = st.tabs([
                "Precipitación", "Temperatura", "Decisión de fuentes", "Estado general"
            ])

            with tab_p:
                p_comp = pd.concat([
                    leticia_df[["Mes", "Precipitación mensual (mm)"]].rename(
                        columns={"Precipitación mensual (mm)": "Precipitación (mm)"}
                    ).assign(Territorio="Leticia · NASA POWER"),
                    tumaco_df[["Mes", "Precipitación IDEAM (mm)"]].rename(
                        columns={"Precipitación IDEAM (mm)": "Precipitación (mm)"}
                    ).assign(Territorio="Tumaco · IDEAM"),
                ], ignore_index=True)
                fig = px.bar(
                    p_comp, x="Mes", y="Precipitación (mm)", color="Territorio",
                    barmode="group", title="Regímenes mensuales según la fuente principal"
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption(
                    "La diferencia refleja tanto el comportamiento climático como las fuentes y periodos utilizados; "
                    "no constituye una comparación homogénea de estaciones."
                )

            with tab_t:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=leticia_df["Mes"], y=leticia_df["Temperatura media (°C)"],
                    mode="lines+markers", name="Leticia · NASA POWER"
                ))
                fig.add_trace(go.Scatter(
                    x=tumaco_df["Mes"], y=tumaco_df["Temperatura media IDEAM (°C)"],
                    mode="lines+markers", name="Tumaco · IDEAM"
                ))
                fig.update_layout(
                    title="Temperatura media mensual según la fuente principal",
                    xaxis_title="Mes", yaxis_title="Temperatura (°C)",
                    legend=dict(orientation="h", y=-0.2), margin=dict(b=80),
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab_fuentes:
                st.dataframe(FUENTES_CLIMATICAS, use_container_width=True, hide_index=True)
                st.info(
                    "Las fuentes se seleccionan variable por variable. No se rellena automáticamente IDEAM con NASA POWER."
                )

            with tab_estado:
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Leticia")
                    mostrar_semaforo("Leticia")
                with c2:
                    st.subheader("Tumaco")
                    mostrar_semaforo("Tumaco")
        except Exception as error:
            st.error("No fue posible construir la comparación automática con los Excel disponibles.")
            st.code(str(error), language=None)
    else:
        st.warning(
            "Para activar las gráficas comparativas deben estar junto al código los Excel de "
            "NASA POWER Leticia, NASA POWER Tumaco e IDEAM Tumaco."
        )
        st.dataframe(FUENTES_CLIMATICAS, use_container_width=True, hide_index=True)

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
        st.markdown(
            f"""
            <div class="card" style="min-height:auto;">
                <h3>{titulo}</h3>
                <p>{texto}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =========================================================
# FUENTES Y DESCARGAS
# =========================================================

elif seccion == "Fuentes y descargas":
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
                "CORPONARIÑO / POMCA Río Mira", "Parques Nacionales", "SENA", "SIAMS",
            ],
            "Uso": [
                "Series terrestres y control de completitud",
                "Variables climáticas continuas",
                "Mapas regionales de Leticia",
                "Humedales e inundación de Leticia",
                "Geología, cobertura, relieve e inundación de Tumaco",
                "Contexto hídrico y costero de Tumaco",
                "Referencia académica de pozos e IRCA en Leticia",
                "Procesamiento, decisiones de uso e integración web",
            ],
            "Condición": [
                "Principal o complementaria según variable", "Principal o complementaria según variable",
                "Referencia cartográfica", "Referencia cartográfica", "Referencia cartográfica",
                "Referencia cartográfica", "Referencia académica complementaria", "Producto académico",
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