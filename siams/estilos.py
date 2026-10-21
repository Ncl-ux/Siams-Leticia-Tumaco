"""Estilos visuales originales de SIAMS, aislados de la lógica de datos."""
import streamlit as st

def aplicar_estilos():
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

        /* SIAMS_COLOR_CORREOS_SIDEBAR_V1 */
        /* Solo los enlaces de correo del lateral; no altera otros enlaces ni créditos. */
        [data-testid="stSidebar"] a[href^="mailto:"],
        [data-testid="stSidebar"] a[href^="mailto:"]:visited,
        [data-testid="stSidebar"] a[href^="mailto:"]:focus,
        [data-testid="stSidebar"] a[href^="mailto:"]:hover {
            color: #E3F5ED !important;
            -webkit-text-fill-color: #E3F5ED !important;
            text-decoration: none !important;
            font-weight: 500 !important;
        }
        [data-testid="stSidebar"] a[href^="mailto:"]:hover {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            text-decoration: underline !important;
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



        /* INICIO SIAMS · GALERÍA FOTOGRÁFICA DE LAS SIETE SEDES */
        .siams-home-kicker {
            color: var(--primary-color) !important;
            font-size: .78rem; text-transform: uppercase;
            font-weight: 800; letter-spacing: .12rem;
            margin: .2rem 0 .45rem;
        }
        .siams-home-subtitle {
            color: var(--text-color) !important;
            opacity: .78; font-size: .96rem; line-height: 1.55;
            max-width: 950px; margin-bottom: .9rem;
        }
        /* La altura es idéntica aunque varíen los textos y las imágenes. */
        .siams-sede-content {
            height: 375px; min-width: 0; display: flex;
            flex-direction: column; color: var(--text-color);
            overflow: hidden; border-radius: 12px;
        }
        .siams-sede-media {
            height: 134px; flex: 0 0 134px;
            position: relative; overflow: hidden;
            background: linear-gradient(125deg, #105e55, #389d81);
            border-radius: 11px; margin-bottom: .72rem;
        }
        .siams-sede-media img {
            display: block; height: 100%; width: 100%;
            object-fit: cover; object-position: center;
            transition: transform .28s ease;
        }
        .siams-sede-media:hover img {transform: scale(1.035);}
        .siams-sede-media--empty {
            display:flex; justify-content:center; align-items:center;
            color: #fff !important; font-size: 2.3rem;
        }
        .siams-sede-photo-label {
            position: absolute; bottom: 0; left: 0; right: 0;
            color: #fff !important; font-size: .68rem; font-weight: 700;
            padding: 14px 9px 7px;
            background:linear-gradient(0deg,rgba(0,0,0,.57),rgba(0,0,0,0));
        }

        /* SIAMS_A6_FOTOS_PORTADA_CREDITOS | crédito fotográfico junto a cada imagen */
        .siams-sede-photo-credit {
            position: absolute;
            top: 7px;
            right: 7px;
            z-index: 2;
            max-width: calc(100% - 14px);
            padding: .19rem .42rem;
            border-radius: 7px;
            background: rgba(8, 28, 25, .80);
            color: #fff !important;
            font-size: .65rem;
            font-weight: 650;
            line-height: 1.35;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            cursor: help;
        }
        .siams-sede-body {
            min-height:0; flex:1; display: flex; flex-direction: column;
        }
        .siams-sede-region {
            font-size: .67rem; font-weight: 750; letter-spacing:.03em;
            color:var(--text-color) !important; opacity: .7;
            white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
        }
        .siams-sede-title {
            color:var(--text-color) !important;
            font-size:1.14rem; font-weight:850; line-height:1.2;
            margin:.17rem 0 .12rem;
        }
        .siams-sede-focus {
            color:var(--primary-color) !important;
            font-size:.75rem; font-weight:800; margin-bottom:.35rem;
            overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
        }
        .siams-sede-description {
            color:var(--text-color) !important;
            font-size:.77rem; line-height:1.42; opacity:.91;
            margin:0 0 .35rem; min-height:4.26em;
            display:-webkit-box; -webkit-box-orient:vertical;
            -webkit-line-clamp:3; overflow:hidden;
        }
        .siams-sede-dates {
            border-top:1px solid var(--siams-borde);
            padding-top:.48rem; margin-top:auto;
            min-height:55px;
        }
        .siams-sede-date-heading {
            color:var(--text-color) !important; font-size:.66rem;
            font-weight:800; opacity:.74; margin-bottom:.22rem;
        }
        .siams-sede-date-row {
            color:var(--text-color) !important; font-size:.68rem;
            line-height:1.32; white-space:nowrap;
            overflow:hidden; text-overflow:ellipsis;
        }
        .siams-sede-date-source {font-weight:780;}
        .siams-sede-tags {
            display:flex; flex-wrap:nowrap; gap:.3rem;
            margin-top:.45rem; min-height:24px;
            overflow:hidden;
        }
        .siams-sede-tag {
            background:color-mix(in srgb, var(--primary-color) 11%, var(--secondary-background-color));
            border:1px solid color-mix(in srgb, var(--primary-color) 23%, var(--secondary-background-color));
            color:var(--text-color) !important; border-radius:999px;
            font-size:.61rem; font-weight:760; padding:.2rem .44rem;
            white-space:nowrap;
        }
        .siams-sede-empty {
            font-size:.7rem; color:var(--text-color) !important;
            opacity:.66; font-style:italic;
        }
        .siams-home-note {
            font-size:.8rem; opacity:.75; line-height:1.55;
            color:var(--text-color) !important; margin:.5rem 0 1.1rem;
        }
        @media(max-width:950px) {
            .siams-sede-content {height:410px;}
            .siams-sede-media {height:116px;flex-basis:116px;}
        }
        @media(max-width:640px) {
            .siams-sede-content {height:395px;}
            .siams-sede-media {height:132px;flex-basis:132px;}
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


        @media (max-width: 768px) {
            .block-container {
                padding-top: 0.8rem !important;
                padding-left: 0.65rem !important;
                padding-right: 0.65rem !important;
                padding-bottom: 1.4rem !important;
            }
            h1 {font-size: 1.55rem !important;}
            h2 {font-size: 1.3rem !important;}
            h3 {font-size: 1.12rem !important;}
            .soft-box, .sentinel-banner, .hero-card, .metric-card, .info-card {
                padding: 0.9rem !important;
                border-radius: 14px !important;
            }
            .location-progress {
                overflow-x: auto;
                white-space: nowrap;
                padding-bottom: 0.35rem;
            }
            [data-testid="stTabs"] button {
                font-size: 0.9rem !important;
                padding: 0.55rem 0.7rem !important;
            }
            [data-testid="stHorizontalBlock"] {gap: 0.6rem !important;}
            iframe {max-width: 100% !important;}
        }

        </style>

    """,
        unsafe_allow_html=True,
    )
