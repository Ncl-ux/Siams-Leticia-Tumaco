from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
# FUNCIONES
# =========================================================

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


def encontrar_carpeta_mapas() -> Path:
    """Busca la carpeta de mapas tanto junto al código como en Documentos."""
    carpeta_codigo = Path(__file__).resolve().parent

    candidatas = [
        carpeta_codigo / "SIAMS MAPAS",
        carpeta_codigo / "mapas",
        carpeta_codigo / "datos" / "leticia" / "mapas",
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
    """Convierte una fecha sin aplicar ``origin`` a textos o fechas ya interpretadas."""
    if valor is None or pd.isna(valor):
        return None

    # El Excel de NASA POWER llega normalmente como datetime de Python o Timestamp.
    # Este intento funciona para ambos y también para textos ISO como 2000-01-01.
    fecha = pd.to_datetime(valor, errors="coerce")
    if pd.notna(fecha):
        return pd.Timestamp(fecha)

    # Respaldo exclusivo para un serial numérico real de Excel.
    # Se suma el número de días, sin usar el parámetro origin de pd.to_datetime.
    if pd.api.types.is_number(valor):
        return pd.Timestamp("1899-12-30") + pd.to_timedelta(float(valor), unit="D")

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
    """Muestra un mapa de Leticia o un aviso claro si el archivo no aparece."""
    nombre_base = MAPAS_LETICIA[clave]
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
        return

    # Se conserva el tamaño original para evitar que Streamlit agrande una
    # captura pequeña y la vuelva más borrosa. En pantallas estrechas el
    # navegador la ajusta automáticamente.
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
            key=f"descargar_{clave}_{ruta.name}",
        )

    st.caption(
        "La nitidez depende del archivo original. Para una mejora real conviene "
        "exportar nuevamente el mapa desde el PDF o SIG a 300 ppp; el código evita "
        "ampliarlo artificialmente dentro de la página."
    )

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
        return pd.DataFrame(
            {
                "Variable": [
                    "Precipitación",
                    "Temperatura",
                    "Humedad",
                    "Presión",
                    "Viento",
                    "Radiación",
                ],
                "IDEAM": [
                    "Parcial",
                    "Insuficiente",
                    "Insuficiente",
                    "No encontrada",
                    "Limitada",
                    "No encontrada",
                ],
                "NASA POWER": [
                    "Disponible",
                    "Disponible",
                    "Disponible",
                    "Disponible",
                    "Disponible",
                    "Disponible",
                ],
                "Uso preliminar": [
                    "NASA POWER",
                    "NASA POWER",
                    "NASA POWER",
                    "NASA POWER",
                    "NASA POWER",
                    "NASA POWER",
                ],
            }
        )

    return pd.DataFrame(
        {
            "Variable": [
                "Precipitación",
                "Temperatura",
                "Humedad",
                "Presión",
                "Viento",
                "Radiación",
            ],
            "IDEAM": [
                "Disponible parcial",
                "Disponible parcial",
                "Disponible parcial",
                "No encontrada",
                "Limitada",
                "No encontrada",
            ],
            "NASA POWER": [
                "Disponible",
                "Disponible",
                "Disponible",
                "Disponible",
                "Disponible",
                "Disponible",
            ],
            "Uso preliminar": [
                "Comparación",
                "Comparación",
                "Comparación",
                "NASA POWER",
                "NASA POWER",
                "NASA POWER",
            ],
        }
    )


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
        st.markdown(
            """
            - Confirmar el área definitiva de análisis.
            - Incorporar datos oficiales revisados.
            - Definir las capas cartográficas prioritarias.
            - Agregar fotografías y textos institucionales autorizados.
            """
        )

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

    if territorio == "Leticia":
        st.info(
            "Los mapas temáticos disponibles fueron incorporados como imágenes de "
            "referencia para evitar cargar capas SIG pesadas dentro del prototipo."
        )

# =========================================================
# CLIMA
# =========================================================

elif seccion == "Clima":
    st.title(f"🌧️ Clima de {territorio}")
    st.caption("Lector climático SIAMS · corrección de fechas v3")

    indicadores = {}
    datos_reales = territorio == "Leticia" and ARCHIVO_CLIMA_LETICIA is not None

    if datos_reales:
        try:
            df, indicadores = cargar_clima_leticia(str(ARCHIVO_CLIMA_LETICIA))
            st.success(
                f"Datos reales cargados desde `{ARCHIVO_CLIMA_LETICIA.name}` · "
                "Fuente: NASA POWER."
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
        if territorio == "Leticia":
            st.warning(
                "No se encontró el Excel de NASA POWER. Súbelo al mismo nivel de "
                "`app.py` con un nombre que comience por `NASA_POWER_LETICIA`."
            )
        else:
            st.warning(
                "Los valores mostrados todavía son ilustrativos para este territorio."
            )

    if datos_reales and indicadores:
        fecha_inicial = indicadores.get("Fecha inicial")
        fecha_final = indicadores.get("Fecha final")
        dias = indicadores.get("Número de días descargados", "—")
        p_max = indicadores.get("Precipitación diaria máxima [mm/día]", "—")
        t_media = indicadores.get("Temperatura media del periodo [°C]", "—")
        hr_media = indicadores.get("Humedad relativa media [%]", "—")

        m1, m2, m3, m4 = st.columns(4)
        periodo = (
            f"{fecha_inicial:%Y-%m-%d} a {fecha_final:%Y-%m-%d}"
            if hasattr(fecha_inicial, "strftime") and hasattr(fecha_final, "strftime")
            else "—"
        )
        m1.metric("Periodo", periodo)
        m2.metric("Días analizados", f"{int(dias):,}" if pd.notna(dias) else "—")
        m3.metric("Máxima diaria", f"{float(p_max):.2f} mm/día" if pd.notna(p_max) else "—")
        m4.metric("Temperatura media", f"{float(t_media):.2f} °C" if pd.notna(t_media) else "—")

        st.markdown(
            f"""
            <div class="soft-box">
                <strong>Humedad relativa media del periodo:</strong> {float(hr_media):.2f} %<br>
                <strong>Tratamiento:</strong> régimen mensual multianual calculado a partir de datos diarios.<br>
                <strong>Nota:</strong> la precipitación de la gráfica corresponde al total mensual climatológico, no a mm/día.
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Precipitación",
            "Temperatura y humedad",
            "Viento, presión y radiación",
            "Tabla",
        ]
    )

    with tab1:
        fig = px.bar(
            df,
            x="Mes",
            y="Precipitación mensual (mm)",
            title="Régimen mensual multianual de precipitación",
            text_auto=".1f",
        )
        fig.update_layout(
            xaxis_title="Mes",
            yaxis_title="Precipitación mensual (mm)",
            margin=dict(l=30, r=30, t=60, b=30),
        )
        st.plotly_chart(fig, use_container_width=True)

        if datos_reales:
            mes_max = df.loc[df["Precipitación mensual (mm)"].idxmax()]
            mes_min = df.loc[df["Precipitación mensual (mm)"].idxmin()]
            st.info(
                f"El mayor promedio mensual se presenta en **{mes_max['Mes']}** "
                f"({mes_max['Precipitación mensual (mm)']:.1f} mm), mientras que "
                f"el menor ocurre en **{mes_min['Mes']}** "
                f"({mes_min['Precipitación mensual (mm)']:.1f} mm)."
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
            title="Temperatura y humedad relativa",
            yaxis=dict(title="Temperatura (°C)"),
            yaxis2=dict(
                title="Humedad relativa (%)",
                overlaying="y",
                side="right",
                range=[0, 100],
            ),
            legend=dict(orientation="h", y=-0.2),
            margin=dict(l=30, r=30, t=60, b=80),
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
                "Variable climática",
                columnas_otras,
                key=f"variable_clima_{territorio}",
            )
            fig = px.line(
                df,
                x="Mes",
                y=variable,
                markers=True,
                title=f"Régimen mensual de {variable.lower()}",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                "Estas variables se mostrarán cuando exista un archivo procesado para el territorio."
            )

    with tab4:
        st.dataframe(
            df.round({
                "Precipitación mensual (mm)": 1,
                "Temperatura media (°C)": 2,
                "Temperatura máxima (°C)": 2,
                "Temperatura mínima (°C)": 2,
                "Humedad relativa (%)": 2,
                "Viento a 2 m (m/s)": 3,
                "Presión superficial (kPa)": 2,
                "Radiación solar (kWh/m²/día)": 2,
            }),
            use_container_width=True,
            hide_index=True,
        )

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
        c1, c2 = st.columns(2)

        with c1:
            mostrar_tarjeta(
                "Agua superficial",
                "Ríos, quebradas, humedales, cuerpos de agua y dirección general del drenaje.",
                "🌊",
            )

        with c2:
            mostrar_tarjeta(
                "Información por incorporar",
                "Cuencas, subcuencas, inventario de humedales, caudales y zonas inundables.",
                "📂",
            )

        st.info("Los mapas temáticos de Tumaco todavía están pendientes de incorporación.")

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
            st.info("El mapa geológico de Tumaco todavía está pendiente de incorporación.")

    with tab2:
        ejemplo = pd.DataFrame(
            {
                "Código": ["Pendiente"],
                "Unidad": ["Información en revisión"],
                "Edad": ["—"],
                "Material dominante": ["—"],
                "Descripción": ["Reemplazar con datos oficiales"],
            }
        )

        st.dataframe(
            ejemplo,
            use_container_width=True,
            hide_index=True,
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
            st.info("El mapa de coberturas de Tumaco todavía está pendiente.")

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
            st.info("El mapa de relieve de Tumaco todavía está pendiente.")

# =========================================================
# ESTACIONES Y DATOS
# =========================================================

elif seccion == "Estaciones y datos":
    st.title(f"📚 Estaciones y disponibilidad de datos – {territorio}")

    st.dataframe(
        tabla_disponibilidad(territorio),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        """
        Para cada estación se debe incorporar:

        - Nombre.
        - Código.
        - Tipo.
        - Estado.
        - Coordenadas.
        - Distancia a la sede.
        - Variables.
        - Periodo.
        - Número de registros.
        - Porcentaje de faltantes.
        - Criterio de uso o descarte.
        """
    )

# =========================================================
# MONITOREO Y CURVAS
# =========================================================

elif seccion == "Monitoreo y curvas":
    st.title(f"📡 Monitoreo y curvas – {territorio}")

    st.info(
        "La página no procesará los datos de las sondas. Mostrará únicamente "
        "gráficas, resultados e interpretaciones generadas en un programa externo."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Precipitación y nivel",
            "Eventos",
            "Resultados",
        ]
    )

    with tab1:
        fechas = pd.date_range(
            "2026-01-01",
            periods=20,
            freq="D",
        )

        demo = pd.DataFrame(
            {
                "Fecha": fechas,
                "Precipitación": [
                    0, 4, 12, 0, 0, 20, 8, 0, 0, 3,
                    15, 0, 0, 0, 11, 5, 0, 0, 9, 0,
                ],
                "Nivel": [
                    2.50, 2.49, 2.46, 2.45, 2.44,
                    2.39, 2.36, 2.35, 2.34, 2.33,
                    2.28, 2.27, 2.26, 2.25, 2.21,
                    2.20, 2.20, 2.19, 2.16, 2.16,
                ],
            }
        )

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=demo["Fecha"],
                y=demo["Precipitación"],
                name="Precipitación (mm)",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=demo["Fecha"],
                y=demo["Nivel"],
                mode="lines+markers",
                name="Nivel (m)",
                yaxis="y2",
            )
        )

        fig.update_layout(
            title="Ejemplo visual: precipitación y nivel",
            yaxis=dict(
                title="Precipitación (mm)",
            ),
            yaxis2=dict(
                title="Nivel (m)",
                overlaying="y",
                side="right",
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.caption(
            "Datos demostrativos. Reemplazar por resultados procesados."
        )

    with tab2:
        eventos = pd.DataFrame(
            {
                "Evento": [
                    "E1",
                    "E2",
                    "E3",
                ],
                "Precipitación acumulada (mm)": [
                    "—",
                    "—",
                    "—",
                ],
                "Variación del nivel (m)": [
                    "—",
                    "—",
                    "—",
                ],
                "Tiempo de respuesta": [
                    "—",
                    "—",
                    "—",
                ],
                "Calidad": [
                    "Pendiente",
                    "Pendiente",
                    "Pendiente",
                ],
            }
        )

        st.dataframe(
            eventos,
            use_container_width=True,
            hide_index=True,
        )

    with tab3:
        st.markdown(
            """
            Los resultados podrán incluir:

            - Cambio de nivel.
            - Precipitación acumulada.
            - Tiempo de respuesta.
            - Comparación entre eventos.
            - Coeficiente aprobado por el equipo.
            - Limitaciones metodológicas.
            """
        )

# =========================================================
# COMPARAR TERRITORIOS
# =========================================================

elif seccion == "Comparar territorios":
    st.title("⚖️ Comparación entre Leticia y Tumaco")

    comparacion = pd.DataFrame(
        {
            "Aspecto": [
                "Región",
                "Fuente climática principal",
                "Estado IDEAM",
                "Condición hídrica",
                "Área principal",
            ],
            "Leticia": [
                "Amazonía",
                "NASA POWER",
                "Muy limitada",
                "Fluvial amazónica",
                "15 km",
            ],
            "Tumaco": [
                "Pacífico",
                "IDEAM + NASA POWER",
                "Parcial",
                "Costera y estuarina",
                "25 km",
            ],
        }
    )

    st.dataframe(
        comparacion,
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "La comparación definitiva debe usar periodos, unidades y metodologías equivalentes."
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

    if territorio == "Leticia":
        with st.expander("Estado de los archivos de mapas", expanded=False):
            st.write(f"**Carpeta detectada:** `{CARPETA_MAPAS}`")
            estado_mapas = []
            for clave, nombre_base in MAPAS_LETICIA.items():
                ruta = buscar_mapa(nombre_base)
                estado_mapas.append(
                    {
                        "Mapa": clave.replace("_", " ").title(),
                        "Archivo esperado": nombre_base,
                        "Estado": "Encontrado" if ruta else "No encontrado",
                    }
                )
            st.dataframe(
                pd.DataFrame(estado_mapas),
                use_container_width=True,
                hide_index=True,
            )

    fuentes = pd.DataFrame(
        {
            "Fuente": [
                "IDEAM",
                "NASA POWER",
                "Servicio Geológico Colombiano",
                "IGAC / SIAC",
                "DEM y cobertura",
                "SIAMS",
            ],
            "Uso": [
                "Estaciones y series",
                "Variables climáticas",
                "Geología, hidrogeología y pozos",
                "Cartografía base",
                "Relieve y uso del suelo",
                "Resultados procesados y documentos",
            ],
            "Estado": [
                "En revisión",
                "Disponible",
                "Pendiente",
                "Pendiente",
                "Pendiente",
                "En construcción",
            ],
        }
    )

    st.dataframe(
        fuentes,
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "Los botones de descarga se habilitarán cuando los archivos estén revisados y autorizados."
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
    f"Territorio seleccionado: {territorio} · Nivel: {publico}"
)