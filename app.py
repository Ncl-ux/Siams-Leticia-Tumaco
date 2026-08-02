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
        "area_principal": "25 km",
        "contexto": "Hasta 50 km",
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
    st.title(f"🗺️ Mapa territorial de {territorio}")

    st.write(
        "En la versión final se integrarán capas de sede UNAL, área principal, "
        "contexto regional, hidrografía, humedales, estaciones, pozos y sondas."
    )

    mapa = pd.DataFrame(
        {
            "lat": [info["lat"]],
            "lon": [info["lon"]],
        }
    )

    st.map(mapa, zoom=8)

    c1, c2, c3 = st.columns(3)

    with c1:
        mostrar_tarjeta(
            "Capas base",
            "Límites administrativos, centros poblados y sede UNAL.",
            "📍",
        )

    with c2:
        mostrar_tarjeta(
            "Capas hídricas",
            "Ríos, quebradas, humedales y cuerpos de agua.",
            "💦",
        )

    with c3:
        mostrar_tarjeta(
            "Capas de monitoreo",
            "Estaciones IDEAM, pozos SGC y sondas.",
            "📡",
        )

# =========================================================
# CLIMA
# =========================================================

elif seccion == "Clima":
    st.title(f"🌧️ Clima de {territorio}")

    st.warning(
        "Los valores mostrados son ilustrativos y deben reemplazarse por los Excel finales."
    )

    df = pd.DataFrame(
        {
            "Mes": MESES,
            "Precipitación (mm)": info["precipitacion"],
            "Temperatura (°C)": info["temperatura"],
            "Humedad relativa (%)": info["humedad"],
        }
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Precipitación",
            "Temperatura y humedad",
            "Tabla",
        ]
    )

    with tab1:
        fig = px.bar(
            df,
            x="Mes",
            y="Precipitación (mm)",
            title="Régimen mensual de precipitación",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with tab2:
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["Mes"],
                y=df["Temperatura (°C)"],
                mode="lines+markers",
                name="Temperatura (°C)",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["Mes"],
                y=df["Humedad relativa (%)"],
                mode="lines+markers",
                name="Humedad relativa (%)",
                yaxis="y2",
            )
        )

        fig.update_layout(
            title="Temperatura y humedad relativa",
            yaxis=dict(
                title="Temperatura (°C)",
            ),
            yaxis2=dict(
                title="Humedad (%)",
                overlaying="y",
                side="right",
            ),
            margin=dict(
                l=30,
                r=30,
                t=60,
                b=30,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with tab3:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

# =========================================================
# HIDROLOGÍA
# =========================================================

elif seccion == "Hidrología":
    st.title(f"💦 Hidrología de {territorio}")

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

    st.info(
        "Esta sección quedará conectada al mapa territorial y a fichas de cuerpos de agua."
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
        st.info(
            "Aquí se mostrará el mapa geológico oficial o una capa GeoJSON simplificada."
        )

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
        "El mapa clasificará los puntos por nivel de riesgo y permitirá consultar "
        "fecha, fuente, valor IRCA y parámetros que generan incumplimiento."
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
            "Estado": [
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
        "La clasificación corresponde al punto y periodo evaluado; "
        "no representa automáticamente toda el área cercana."
    )

# =========================================================
# COBERTURA Y RELIEVE
# =========================================================

elif seccion == "Cobertura y relieve":
    st.title(f"🌿 Cobertura y relieve de {territorio}")

    tab1, tab2 = st.tabs(
        [
            "Cobertura",
            "Relieve",
        ]
    )

    with tab1:
        st.markdown(
            """
            Se incorporarán categorías como bosque, manglar, zona urbana,
            cultivos, pastos, humedales, agua y áreas intervenidas.
            """
        )

        st.info(
            "Pendiente: capa de cobertura, año, leyenda y porcentaje por categoría."
        )

    with tab2:
        st.markdown(
            """
            Se incorporará el modelo digital de elevación, elevación mínima y máxima,
            pendientes, perfil altitudinal y relación con el drenaje.
            """
        )

        st.info(
            "Pendiente: DEM, resolución espacial y estadísticas del área de análisis."
        )

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
                "25 km",
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