"""Panel complementario GRACE + niveles de Leticia para SIAMS.

Se integra mediante mostrar_grace_leticia() al final del bloque existente
'Agua subterránea (GRACE)' de app.py. No reemplaza el NetCDF ni el GGDI.
Los CSV acompañantes conservan las salidas procesadas del proyecto GRACE
entregado por la profesora (procesamiento 2026-10-04).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

CARPETA_DATOS = Path(__file__).resolve().parent.parent / "data/processed/grace/leticia"
if not CARPETA_DATOS.is_dir():
    CARPETA_DATOS = Path(__file__).resolve().parent.parent / "Datos_GRACE_Leticia"
VERDE = "#146c5c"       # Paleta original de SIAMS (siams/estilos.py).
VERDE_2 = "#1f7f6c"
AZUL = "#4679a3"
NARANJA = "#c48a3d"
GRIS = "#687784"

# Datos de campo comunicados el 20-10-2026. La profundidad de instalación
# está medida desde el TERRENO hasta el sensor (no desde el brocal).
# No son calibraciones del transductor ni validan el campo h_natural_m.
SONDAS_LETICIA = {
    "Numae": {
        "punto": "Numae · indicador de columna",
        "cota_terreno_msnm": 77.0,
        "profundidad_instalacion_m": 7.0,  # excepción: NO son 17 m
    },
    "SONDA01_CasaProfeArturo": {
        "punto": "Casa del profesor Arturo · indicador de columna",
        "cota_terreno_msnm": 80.0,
        "profundidad_instalacion_m": 17.0,
    },
}
# Pachovela no aparece como serie temporal validada en el CSV procesado.
# Se guarda su ficha de referencia sin fabricar observaciones.
PACHOVELA = {"punto": "Colegio Pachovela", "cota_terreno_msnm": 78.0,
             "profundidad_instalacion_m": 17.0}


def _tabla_referencias_sondas() -> pd.DataFrame:
    """Ficha de terreno e instalación (no depende de los CSV)."""
    filas = [
        {"Punto": "Numae", "Cota terreno (m s. n. m.)": 77.0,
         "Instalación bajo terreno (m)": 7.0, "Estado": "Referencia informada"},
        {"Punto": "Casa del profesor Arturo", "Cota terreno (m s. n. m.)": 80.0,
         "Instalación bajo terreno (m)": 17.0, "Estado": "Referencia informada"},
        {"Punto": "Colegio Pachovela", "Cota terreno (m s. n. m.)": 78.0,
         "Instalación bajo terreno (m)": 17.0,
         "Estado": "Solo ficha; sin serie histórica validada"},
    ]
    return pd.DataFrame(filas)


@st.cache_data(show_spinner=False)
def _leer_csv(nombre: str) -> pd.DataFrame:
    """Lee solamente nombres definidos por el módulo desde su carpeta de datos."""
    validos = {
        "GWSA_A_B_sites_Leticia.csv",
        "transductores_natural_diario.csv",
        "Leticia_pozo_serie_natural_filtrada.csv",
        "ideam_nivel_rio_mensual.csv",
        "GRACE_site_pixels.csv",
    }
    if nombre not in validos:
        raise ValueError("Nombre de archivo GRACE no permitido")
    return pd.read_csv(CARPETA_DATOS / nombre)


def _serie_grace() -> pd.DataFrame:
    df = _leer_csv("GWSA_A_B_sites_Leticia.csv").copy()
    df["Fecha"] = pd.to_datetime(df["nominal_month"], errors="coerce")
    variables = [
        "GWSA_B_standard_cm", "GWSA_A_original_cm", "TWSA_scaled_cm",
        "Zenodo_GWSA_cm", "SMSA_cm", "CWSA_cm", "SWEA_cm",
    ]
    for nombre in variables:
        df[nombre] = pd.to_numeric(df[nombre], errors="coerce")
    return df.dropna(subset=["Fecha"]).sort_values("Fecha").reset_index(drop=True)


def _niveles_campo() -> pd.DataFrame:
    """Carga datos de campo sin sobrescribir mediciones originales.

    Si h_natural_m equivale a metros de columna de agua SOBRE el sensor,
    la profundidad al agua = profundidad de instalación - h_natural_m y
    la elevación = cota del terreno - profundidad instalación + h_natural_m.
    Hasta verificar conversión/compensación de presión y datum altimétrico,
    ambas columnas calculadas se consideran PROVISIONALES.
    """
    columnas = ["Fecha", "Punto", "Valor", "Tipo", "Referencia", "Lectura_original_m",
                "Cota_terreno_msnm", "Profundidad_instalacion_m", "Cota_sensor_msnm",
                "Profundidad_agua_m", "Cota_agua_msnm", "Estado_conversion"]
    sensores = _leer_csv("transductores_natural_diario.csv")
    sensores = sensores[["fecha", "equipo", "h_natural_m", "fuente_h_natural"]].copy()
    sensores["Fecha"] = pd.to_datetime(sensores["fecha"], errors="coerce")
    sensores["Valor"] = pd.to_numeric(sensores["h_natural_m"], errors="coerce")
    sensores["Punto"] = sensores["equipo"].map(
        {equipo: meta["punto"] for equipo, meta in SONDAS_LETICIA.items()}
    )
    sensores["Tipo"] = "Columna de agua inferida de presión (m; provisional)"
    sensores["Referencia"] = "Lectura de presión/columna aún pendiente de validar"
    sensores["Lectura_original_m"] = sensores["Valor"]
    sensores["Cota_terreno_msnm"] = sensores["equipo"].map(
        {equipo: meta["cota_terreno_msnm"] for equipo, meta in SONDAS_LETICIA.items()}
    )
    sensores["Profundidad_instalacion_m"] = sensores["equipo"].map(
        {equipo: meta["profundidad_instalacion_m"] for equipo, meta in SONDAS_LETICIA.items()}
    )
    sensores["Cota_sensor_msnm"] = (
        sensores["Cota_terreno_msnm"] - sensores["Profundidad_instalacion_m"]
    )
    sensores["Profundidad_agua_m"] = (
        sensores["Profundidad_instalacion_m"] - sensores["Valor"]
    )
    sensores["Cota_agua_msnm"] = sensores["Cota_sensor_msnm"] + sensores["Valor"]
    sensores["Estado_conversion"] = "Provisional; verificar columna de agua, compensación y datum"
    dudosos = (sensores["Valor"] < 0) | (sensores["Valor"] > sensores["Profundidad_instalacion_m"])
    sensores.loc[dudosos, "Estado_conversion"] = (
        "Revisar: columna fuera de 0 a profundidad de instalación (posible referencia o condición surgente)"
    )
    sensores = sensores[columnas]

    unal = _leer_csv("Leticia_pozo_serie_natural_filtrada.csv")
    # No publicar como 'natural' una medición descartada por el filtrado.
    aceptada = unal["en_serie_natural"].astype(str).str.lower().eq("true")
    unal = unal.loc[aceptada, ["fechahora", "prof_natural_m"]].copy()
    unal["Fecha"] = pd.to_datetime(unal["fechahora"], errors="coerce")
    unal["Valor"] = pd.to_numeric(unal["prof_natural_m"], errors="coerce")
    unal["Punto"] = "Pozo UNAL · medición manual"
    unal["Tipo"] = "Profundidad bajo brocal (m)"
    unal["Referencia"] = "Referencia local del brocal; sin cota absoluta verificada"
    unal["Lectura_original_m"] = unal["Valor"]
    for campo in ["Cota_terreno_msnm", "Profundidad_instalacion_m", "Cota_sensor_msnm",
                  "Profundidad_agua_m", "Cota_agua_msnm"]:
        unal[campo] = np.nan
    unal["Estado_conversion"] = "Sin elevación del brocal: no se calcula cota absoluta"
    unal = unal[columnas]
    return pd.concat([sensores, unal], ignore_index=True).dropna(
        subset=["Fecha", "Punto", "Valor"]
    ).sort_values("Fecha").reset_index(drop=True)


def _rio_leticia() -> pd.DataFrame:
    df = _leer_csv("ideam_nivel_rio_mensual.csv")
    df = df.loc[df["estacion"].astype(str).str.lstrip("0") == "48017010"].copy()
    df["Fecha"] = pd.to_datetime(df["mes"], errors="coerce")
    df["Valor"] = pd.to_numeric(df["nivel_medio_cm"], errors="coerce")
    return df[["Fecha", "Valor", "estacion", "pct_dias_validos"]].dropna(
        subset=["Fecha", "Valor"]
    ).sort_values("Fecha")


def _figura(titulo: str, eje_y: str) -> go.Figure:
    figura = go.Figure()
    figura.update_layout(
        title={"text": titulo, "x": 0, "font": {"size": 17}},
        xaxis_title="Fecha", yaxis_title=eje_y,
        hovermode="x unified", height=420,
        margin=dict(l=18, r=18, t=68, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.23, x=0),
    )
    figura.update_xaxes(showgrid=True, gridcolor="rgba(125,130,130,.15)")
    figura.update_yaxes(showgrid=True, gridcolor="rgba(125,130,130,.15)")
    return figura


def _mensual_con_huecos(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Inserta NaN en meses no observados para que Plotly NO una las brechas."""
    temporal = df[["Fecha", columna]].copy()
    temporal["Fecha"] = pd.to_datetime(temporal["Fecha"], errors="coerce")
    temporal = temporal.dropna(subset=["Fecha"])
    if temporal.empty:
        return pd.DataFrame(columns=["Fecha", columna])
    # No basta connectgaps=False: la gráfica necesita el mes ausente como NaN.
    temporal["_mes"] = temporal["Fecha"].dt.to_period("M")
    temporal = temporal.sort_values("Fecha").drop_duplicates("_mes", keep="last")
    meses = pd.period_range(temporal["_mes"].min(), temporal["_mes"].max(), freq="M")
    serie = temporal.set_index("_mes")[[columna]].reindex(meses)
    serie.index = serie.index.to_timestamp()
    return serie.rename_axis("Fecha").reset_index()


def _diaria_con_huecos(df: pd.DataFrame, columna: str = "Valor") -> pd.DataFrame:
    """Para sondas/pozos, distingue días sin registro de datos continuos."""
    salida = df[["Fecha", columna]].rename(columns={columna: "Valor"}).copy()
    salida["Fecha"] = pd.to_datetime(salida["Fecha"], errors="coerce")
    salida = salida.dropna(subset=["Fecha"])
    if salida.empty:
        return salida
    salida["_dia"] = salida["Fecha"].dt.normalize()
    salida = salida.sort_values("Fecha").drop_duplicates("_dia", keep="last")
    dias = pd.date_range(salida["_dia"].min(), salida["_dia"].max(), freq="D")
    salida = salida.set_index("_dia")[["Valor"]].reindex(dias)
    return salida.rename_axis("Fecha").reset_index()


def _meses_comunes_normalizados(
    grace: pd.DataFrame, campo: pd.DataFrame, rio: pd.DataFrame, puntos: list[str]
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Anomalías estandarizadas SOLO en meses compartidos con GRACE.

    1) Agrupación mensual de datos locales disponibles.
    2) Unión temporal por mes exacto.
    3) z-score sobre el periodo compartido y sin completar datos faltantes.
    Para profundidad del pozo UNAL el signo se invierte: menor profundidad
    significa mayor nivel relativo, si la referencia de medición no cambió.
    """
    base = grace[["Fecha", "GWSA_B_standard_cm"]].rename(
        columns={"GWSA_B_standard_cm": "GRACE · GWSA B"}
    ).dropna().copy()
    base["Fecha"] = base["Fecha"].dt.to_period("M").dt.to_timestamp()
    combinada = base.set_index("Fecha")
    comunes: dict[str, int] = {}
    for punto in puntos:
        if punto == "Río Amazonas · IDEAM":
            temporal = rio[["Fecha", "Valor"]].copy()
        else:
            es_pozo_unal = punto.startswith("Pozo UNAL")
            # Series de sondas convertidas a cota provisoria: la estandarización
            # no cambia al sumar/restar una constante por estación.
            columna = "Valor" if es_pozo_unal else "Cota_agua_msnm"
            temporal = campo.loc[campo["Punto"] == punto, ["Fecha", columna]].copy()
            temporal = temporal.rename(columns={columna: "Valor"})
        temporal["Fecha"] = temporal["Fecha"].dt.to_period("M").dt.to_timestamp()
        serie = temporal.groupby("Fecha")["Valor"].mean()
        if punto.startswith("Pozo UNAL"):
            # Invertir solamente el signo, no afirmar una cota absoluta.
            serie = -serie
        temporal_comun = combinada[["GRACE · GWSA B"]].join(serie.rename(punto), how="inner")
        temporal_comun = temporal_comun.dropna()
        comunes[punto] = int(len(temporal_comun))
        combinada = combinada.join(serie.rename(punto), how="left")
    columnas = ["GRACE · GWSA B", *puntos]
    combinada = combinada[columnas].dropna()  # misma ventana para las curvas seleccionadas
    if len(combinada) < 3:
        return pd.DataFrame(), comunes
    salida = pd.DataFrame(index=combinada.index)
    for nombre in columnas:
        desv = float(combinada[nombre].std(ddof=0))
        if not np.isfinite(desv) or desv <= 1e-12:
            return pd.DataFrame(), comunes
        salida[nombre] = (combinada[nombre] - combinada[nombre].mean()) / desv
    return salida.reset_index().rename(columns={"index": "Fecha"}), comunes


def _descargar(df: pd.DataFrame, archivo: str, etiqueta: str, clave: str) -> None:
    st.download_button(
        etiqueta,
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=archivo,
        mime="text/csv",
        key=clave,
    )


def mostrar_grace_leticia() -> None:
    """Inserta panel SIAMS sin alterar la lógica GRACE/GGDI existente."""
    st.divider()
    st.subheader("💧 Niveles de agua y GRACE · Leticia")
    st.caption("SIAMS · Observación local, información satelital y control de calidad")
    st.markdown(
        "**¿Por qué se comparan satélites con pozos?** Los satélites permiten seguir "
        "cambios generales en una región, mientras que las sondas muestran lo "
        "que sucede en un punto concreto. Compararlos ayuda a formular preguntas "
        "sobre el agua subterránea en Leticia, aunque no necesariamente se muevan igual."
    )
    with st.expander("Antes de empezar · cuatro conceptos sin tecnicismos", expanded=False):
        st.markdown(
            "**GRACE:** misión satelital que ayuda a estimar cambios en el agua almacenada "
            "en grandes regiones.\n\n"
            "**GWSA:** cambio estimado de almacenamiento *subterráneo* respecto a un "
            "periodo de referencia, expresado como centímetros equivalentes de agua. "
            "No representa la profundidad de un pozo.\n\n"
            "**Sonda:** equipo instalado en un pozo que registra cambios en la presión "
            "o el nivel, según su calibración.\n\n"
            "**Anomalía:** diferencia frente a una referencia. Una anomalía negativa "
            "no significa que se haya agotado toda el agua."
        )
    st.markdown(
        '<div class="soft-box"><strong>Lectura integrada:</strong> GRACE/GRACE-FO observa '
        'anomalías regionales de almacenamiento; las sondas y la medición manual '
        'describen condiciones de puntos específicos. Se presentan por separado '
        'y solo se comparan de manera exploratoria en fechas coincidentes.</div>',
        unsafe_allow_html=True,
    )

    faltantes = [p.name for p in (
        CARPETA_DATOS / "GWSA_A_B_sites_Leticia.csv",
        CARPETA_DATOS / "transductores_natural_diario.csv",
        CARPETA_DATOS / "Leticia_pozo_serie_natural_filtrada.csv",
        CARPETA_DATOS / "ideam_nivel_rio_mensual.csv",
        CARPETA_DATOS / "GRACE_site_pixels.csv",
    ) if not p.is_file()]
    if faltantes:
        st.warning("Faltan archivos del nuevo módulo GRACE: " + ", ".join(faltantes))
        st.caption(f"Carpeta esperada: {CARPETA_DATOS}")
        return

    try:
        grace, campo, rio = _serie_grace(), _niveles_campo(), _rio_leticia()
        pixel = _leer_csv("GRACE_site_pixels.csv")
        pixel_leticia = pixel.loc[pixel["site"] == "Leticia"].iloc[0]
    except (KeyError, ValueError, OSError, pd.errors.ParserError, IndexError) as exc:
        st.error("No se pudieron cargar los archivos procesados de GRACE/Leticia.")
        st.code(str(exc), language=None)
        return

    valido = grace.dropna(subset=["GWSA_B_standard_cm"])
    if valido.empty:
        st.warning("No hay valores válidos de GWSA B para Leticia.")
        return
    a, b, c, d = st.columns(4)
    a.metric("GRACE/GWSA B", f"{len(valido)} meses", f"{valido['Fecha'].min():%Y-%m} a {valido['Fecha'].max():%Y-%m}", delta_color="off")
    b.metric("Pozo Numae", f"{len(campo[campo['Punto'].str.startswith('Numae')])} días", "Indicador provisional", delta_color="off")
    c.metric("Pozo UNAL", f"{len(campo[campo['Punto'].str.startswith('Pozo UNAL')])} mediciones", "Filtradas", delta_color="off")
    d.metric("Píxel GRACE", f"{float(pixel_leticia['near_dist_km']):.1f} km", "Separación sede-celda", delta_color="off")

    tab_sat, tab_pozos, tab_comparar, tab_calidad = st.tabs([
        "🛰️ Serie GRACE", "💧 Pozos y sondas", "📈 Comparación temporal", "📋 Metodología y descargas"
    ])
    with tab_sat:
        st.markdown(
            "**¿Qué muestra esta gráfica?** La evolución del almacenamiento de agua "
            "subterránea estimado para la región de Leticia. La línea horizontal "
            "en **0 cm** es el valor de referencia: estar arriba implica más "
            "almacenamiento relativo; estar abajo, menos. Ninguno de los dos "
            "significa automáticamente una condición buena o mala."
        )
        anos = (int(valido["Fecha"].dt.year.min()), int(valido["Fecha"].dt.year.max()))
        inicio, final = st.slider(
            "Años que deseas visualizar", min_value=anos[0], max_value=anos[1],
            value=anos, key="siams_grace_leticia_rango",
        )
        variables = {
            "GWSA · método B (recomendado)": ("GWSA_B_standard_cm", VERDE),
            "GWSA · método A": ("GWSA_A_original_cm", NARANJA),
            "GRACE · TWSA": ("TWSA_scaled_cm", AZUL),
            "GWSA · referencia Zenodo (hasta 2023)": ("Zenodo_GWSA_cm", GRIS),
        }
        elegidas = st.multiselect(
            "Seleccionar señales", list(variables),
            default=["GWSA · método B (recomendado)", "GWSA · referencia Zenodo (hasta 2023)"],
            key="siams_grace_leticia_variables",
        )
        df_g = grace.loc[grace["Fecha"].dt.year.between(inicio, final)].copy()
        fig = _figura("Almacenamiento de agua · Leticia", "Altura de agua equivalente (cm)")
        for nombre in elegidas:
            columna, color = variables[nombre]
            base = _mensual_con_huecos(df_g, columna) if not df_g.empty else pd.DataFrame()
            if not base.empty:
                fig.add_trace(go.Scatter(
                    x=base["Fecha"], y=base[columna], mode="lines",
                    name=nombre, connectgaps=False, line=dict(color=color, width=2.4),
                ))
        fig.add_hline(y=0, line_dash="dash", line_color="rgba(125,125,125,0.5)")
        st.plotly_chart(fig, use_container_width=True, key="siams_grace_leticia_serie")
        st.caption("Las brechas de misión o meses sin producto se dejan vacíos: no se interpolan. "
                   "La serie principal corresponde a GWSA B (2004–2009 como periodo base).")
        principal = df_g.dropna(subset=["GWSA_B_standard_cm"]).sort_values("Fecha")
        if not principal.empty:
            ultimo = principal.iloc[-1]
            v = float(ultimo["GWSA_B_standard_cm"])
            estado = (
                "por encima de la referencia histórica" if v > 0.005
                else "por debajo de la referencia histórica" if v < -0.005
                else "muy cerca de la referencia histórica"
            )
            st.markdown(
                f"**Lectura del dato más reciente del periodo seleccionado:** en "
                f"**{ultimo['Fecha']:%B de %Y}**, la GWSA B fue **{v:+.2f} cm**: "
                f"el almacenamiento estimado estaba **{estado}**. "
                "Este valor describe una anomalía regional; no indica la profundidad "
                "de los pozos ni permite afirmar por sí solo que el acuífero se recuperó "
                "o se está agotando."
            )
        with st.expander("¿En qué se diferencian las líneas A, B, TWSA y Zenodo?"):
            st.markdown(
                "**Método B:** estimación de agua subterránea recomendada en el proyecto; "
                "resta de GRACE otros componentes del almacenamiento terrestre usando "
                "una referencia común.\n\n"
                "**Método A:** otra formulación incluida para comparar metodologías; "
                "no se debe interpretar como una medición independiente de pozo.\n\n"
                "**TWSA:** cambio del agua terrestre *total*, que incluye agua del suelo, "
                "superficie y subsuelo.\n\n"
                "**Zenodo:** producto publicado usado como referencia comparativa. "
                "Que B se parezca a Zenodo no equivale a comprobarlo con un pozo."
            )
        _descargar(df_g, "SIAMS_Leticia_GRACE_2002_2026.csv", "⬇️ Descargar datos GRACE de Leticia", "siams_descargar_grace_leticia")

    with tab_pozos:
        st.markdown(
            "**¿Qué vas a ver?** Las sondas cuentan ahora con cotas del terreno y "
            "profundidades de instalación informadas el 20/10/2026. El nivel "
            "calculado es **provisional**, pues el campo `h_natural_m` se infiere de "
            "presión y aún falta verificar su interpretación y compensación. "
            "Las mediciones UNAL siguen referidas al brocal, cuya elevación falta."
        )
        st.markdown("**Referencias de instalación informadas por sede**")
        referencias = _tabla_referencias_sondas()
        st.dataframe(referencias, use_container_width=True, hide_index=True)
        st.caption(
            "La cota del sensor se obtiene restando la profundidad de instalación "
            "a la del terreno: Numae 70 m; Casa del profesor Arturo 63 m; "
            "Colegio Pachovela 61 m. Comprobar datum vertical y precisión de cotas."
        )
        _descargar(referencias, "SIAMS_Leticia_referencias_sondas.csv",
                   "⬇️ Descargar referencias de instalación", "siams_grace_leticia_descargar_referencias")
        st.markdown("**Registros de campo y niveles calculados bajo supuesto de columna de agua**")
        puntos_campo = list(campo["Punto"].unique())
        if not puntos_campo:
            st.info("No hay mediciones de pozo/sonda disponibles en los CSV procesados.")
        else:
            punto = st.selectbox("Punto de monitoreo", puntos_campo, key="siams_grace_leticia_pozo")
            seleccion = campo.loc[campo["Punto"] == punto].copy().sort_values("Fecha")
            es_unal = punto.startswith("Pozo UNAL")
            if es_unal:
                columna_grafica = "Valor"
                unidad = "Profundidad bajo brocal (m)"
                st.caption("UNAL: nivel manual referido al brocal; no se le aplican las cotas de las sondas.")
            else:
                alternativas = {
                    "Elevación calculada (provisional)": ("Cota_agua_msnm", "Elevación calculada (m s. n. m.; provisional)"),
                    "Profundidad al agua (provisional)": ("Profundidad_agua_m", "Profundidad bajo terreno (m; provisional)"),
                    "Lectura instrumental original": ("Valor", "Columna de agua inferida (m; provisional)"),
                }
                vista = st.radio("Variable para visualizar", list(alternativas), horizontal=True,
                                key="siams_grace_leticia_vista_nivel")
                columna_grafica, unidad = alternativas[vista]
                datos_referencia = seleccion.iloc[0]
                st.caption(
                    f"Cota del terreno: {datos_referencia['Cota_terreno_msnm']:.2f} m s. n. m. · "
                    f"Profundidad del sensor desde terreno: "
                    f"{datos_referencia['Profundidad_instalacion_m']:.2f} m · "
                    f"Cota del sensor: {datos_referencia['Cota_sensor_msnm']:.2f} m s. n. m."
                )
                st.warning(
                    "**Conversión provisional:** se supone que `h_natural_m` es la altura de "
                    "agua sobre el sensor (m de columna de agua), ya compensada por "
                    "presión atmosférica cuando corresponde. Antes de publicar el nivel "
                    "como definitivo, confirmar esta condición con la ficha del transductor, "
                    "el datum de las cotas y alguna medición manual de contraste."
                )
                anomalias = seleccion[seleccion["Estado_conversion"].str.startswith("Revisar:")]
                if not anomalias.empty:
                    st.warning(
                        f"{len(anomalias)} registros requieren revisión: la lectura "
                        "está fuera del intervalo 0–profundidad de instalación. "
                        "Podría deberse a referencia/calibración o a nivel surgente; "
                        "no se borraron ni se recortaron automáticamente."
                    )
            fig = _figura(f"Evolución de la medición · {punto}", unidad)
            campo_visual = _diaria_con_huecos(seleccion, columna_grafica)
            fig.add_trace(go.Scatter(
                x=campo_visual["Fecha"], y=campo_visual["Valor"],
                mode="lines+markers" if len(seleccion) < 70 else "lines",
                name=punto, connectgaps=False,
                line=dict(color=VERDE, width=2.6), marker=dict(size=5),
            ))
            if es_unal or (not es_unal and columna_grafica == "Profundidad_agua_m"):
                fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True, key="siams_grace_leticia_pozos_fig")
            st.caption("Los días sin registro se dejan en blanco: sin interpolación ni líneas a través de huecos.")
            st.caption(f"{len(seleccion)} observaciones válidas · {seleccion['Fecha'].min():%Y-%m-%d} a "
                       f"{seleccion['Fecha'].max():%Y-%m-%d} · {seleccion['Referencia'].iloc[0]}.")
            primera, ultima = seleccion.iloc[0], seleccion.iloc[-1]
            variacion = float(ultima[columna_grafica] - primera[columna_grafica])
            if len(seleccion) > 1 and primera["Fecha"] != ultima["Fecha"]:
                if es_unal:
                    sentido = ("el agua terminó más alejada del brocal" if variacion > 0
                               else "el agua terminó más cercana al brocal" if variacion < 0
                               else "la profundidad inicial y final resultó igual")
                    st.markdown(
                        f"**¿Qué nos dicen las mediciones?** La profundidad pasó de "
                        f"**{primera['Valor']:.2f} m** a **{ultima['Valor']:.2f} m**; "
                        f"{sentido}. La referencia es el brocal, no el nivel del mar."
                    )
                else:
                    st.markdown(
                        f"**Cambio en la variable seleccionada:** de "
                        f"**{primera[columna_grafica]:.2f}** a "
                        f"**{ultima[columna_grafica]:.2f}** ({variacion:+.2f} m). "
                        "La interpretación de ascenso/descenso depende de la calibración "
                        "y del tipo de variable representada."
                    )
            else:
                st.info("Este punto no tiene suficientes fechas distintas para describir un cambio temporal.")
            _descargar(seleccion, "SIAMS_Leticia_niveles_y_cotas_seleccion.csv",
                       "⬇️ Descargar lecturas originales y niveles calculados", "siams_descargar_niveles_leticia")
        with st.expander("¿Dónde está la sonda de Pachovela?", expanded=False):
            st.info(
                "Pachovela: terreno 78 m s. n. m. e instalación a 17 m bajo terreno "
                "(cota del sensor 61 m s. n. m.). El archivo existente contiene "
                "una prueba de pocos segundos, no una serie validada para comparación "
                "histórica. No se inventan registros ni se agrega una curva ficticia."
            )

    with tab_comparar:
        st.markdown(
            "**La pregunta de esta sección es:** ¿los cambios registrados en los pozos "
            "se parecen, en el tiempo, a los cambios regionales estimados con GRACE? "
            "Para compararlos, primero se reúnen las mediciones por mes y se dejan "
            "únicamente las fechas en común. Después se colocan las curvas en una "
            "misma escala estadística (**z-score**), porque sus unidades son distintas."
        )
        st.markdown('<div class="interpretation-box"><strong>Comparación exploratoria:</strong> '
                    'las magnitudes se estandarizan (z-score) solo en los meses compartidos. '
                    'No son niveles absolutos ni equivalencias físicas de almacenamiento y profundidad. '
                    'Con los pocos meses coincidentes no se concluye causalidad ni significancia estadística.'
                    '</div>',
                    unsafe_allow_html=True)
        opciones = ["Numae · indicador de columna", "Casa del profesor Arturo · indicador de columna",
                    "Pozo UNAL · medición manual", "Río Amazonas · IDEAM"]
        puntos = st.multiselect(
            "Mediciones para comparar", opciones, default=opciones[:2],
            key="siams_grace_leticia_comparar_selecciones",
        )
        if puntos:
            normalizadas, comunes = _meses_comunes_normalizados(grace, campo, rio, puntos)
            if normalizadas.empty:
                st.info("No hay al menos tres meses coincidentes y variables entre los datos seleccionados.")
            else:
                fig = _figura("GRACE y observaciones locales en meses coincidentes", "Anomalía estandarizada (z)")
                paleta = [VERDE, AZUL, NARANJA, GRIS]
                for i, nombre in enumerate(["GRACE · GWSA B", *puntos]):
                    grafica = _mensual_con_huecos(normalizadas, nombre)
                    fig.add_trace(go.Scatter(
                        x=grafica["Fecha"], y=grafica[nombre],
                        name=nombre, mode="lines+markers", connectgaps=False,
                        line=dict(color=paleta[i], width=2.6), marker=dict(size=7),
                    ))
                fig.add_hline(y=0, line_dash="dash", line_color="rgba(120,120,120,.5)")
                st.plotly_chart(fig, use_container_width=True, key="siams_grace_leticia_comparacion")
                st.caption(f"Meses comunes de todas las señales: {len(normalizadas)}. "
                           "Profundidad UNAL invertida solo para comparar el sentido de subida/bajada. "
                           "Agrupación mensual local, sin rellenar vacíos ni inferir desfases.")
                n_comunes = len(normalizadas)
                st.markdown(
                    f"**¿Cómo interpretar las curvas?** Un valor **z = 0** indica el "
                    f"promedio de la *ventana compartida*, no un nivel de agua nulo. "
                    f"Los valores positivos y negativos muestran desviaciones relativas. "
                    f"En tu selección solo hay **{n_comunes} meses coincidentes**. "
                    "Puedes observar si algunas curvas suben o bajan en meses similares, "
                    "pero con esta información **no es válido afirmar una relación causal "
                    "ni una correlación estadísticamente sólida**."
                )
                _descargar(normalizadas, "SIAMS_Leticia_comparacion_normalizada.csv",
                           "⬇️ Descargar comparación", "siams_descargar_comparacion_grace")
        else:
            st.info("Selecciona al menos una observación local.")
        st.markdown("**Nivel del río Amazonas (IDEAM)**")
        st.markdown(
            "El nivel del río aporta contexto hidrológico: permite ver cuándo el "
            "Amazonas presenta niveles más altos o bajos en la estación considerada. "
            "No equivale a medir el agua subterránea del pozo y conserva una referencia propia."
        )
        if not rio.empty:
            fig = _figura("Serie mensual disponible · Estación IDEAM 48017010", "Nivel medio reportado (cm)")
            rio_viz = _mensual_con_huecos(rio, "Valor")
            fig.add_trace(go.Scatter(x=rio_viz["Fecha"], y=rio_viz["Valor"], mode="lines",
                                     connectgaps=False, line=dict(color=AZUL, width=2), name="IDEAM · río"))
            st.plotly_chart(fig, use_container_width=True, key="siams_grace_leticia_rio")
            st.caption("Se conserva el sistema de referencia original IDEAM. No se convierte esta serie "
                       "en un nivel del acuífero ni se confunde con los datos de los pozos.")

    with tab_calidad:
        st.markdown(
            "**¿De dónde sale el dato de agua subterránea?** GRACE observa cambios "
            "en el agua almacenada sobre y bajo el terreno. Para aproximar la parte "
            "subterránea se descuentan las contribuciones estimadas del suelo, la "
            "nieve y la vegetación. El resultado es una **estimación regional**, "
            "no una lectura directa de un pozo."
        )
        st.markdown("**Método para interpretar la estimación satelital**")
        st.latex(r"\mathrm{GWSA}_B=\mathrm{TWSA}-\mathrm{SMSA}-\mathrm{SWEA}-\mathrm{CWSA}")
        st.markdown(
            "TWSA = anomalía de almacenamiento terrestre GRACE; "
            "SMSA = anomalía de humedad del suelo; SWEA = agua almacenada como nieve; "
            "CWSA = agua interceptada en el dosel. "
            "Los componentes comparten la referencia 2004–2009 en el método B."
        )
        col1, col2 = st.columns(2)
        col1.metric("Validación B vs. Zenodo · Leticia", "r = 0,99")
        col2.metric("RMSE B vs. Zenodo · Leticia", "2,50 cm")
        st.caption("Estos indicadores describen reproducción de un producto satelital publicado (2002–2023); "
                   "NO validación contra las sondas ni precisión real de un pozo.")
        st.markdown(
            "**¿Qué significan r y RMSE?** Una **r cercana a 1** indica que las dos "
            "series satelitales comparadas evolucionan de forma parecida. "
            "El **RMSE** resume el tamaño típico de sus diferencias en centímetros. "
            "**No** son medidas de exactitud frente a los pozos de Leticia."
        )
        st.markdown(
            f'<div class="warning-box"><strong>Limitación espacial:</strong> '
            f'centro de la celda JPL ({float(pixel_leticia["near_lat"]):.2f}, '
            f'{float(pixel_leticia["near_lon"]):.2f}); separación sede–centro '
            f'{float(pixel_leticia["near_dist_km"]):.1f} km. La grilla de 0,5° '
            f'no debe confundirse con resolución espacial efectiva de GRACE. '
            f'En una zona fronteriza como Leticia, la representatividad regional '
            f'requiere especial cuidado.</div>', unsafe_allow_html=True,
        )
        st.markdown(
            "**Limitaciones del conjunto:** 33 meses sin solución GRACE en 2002–2026 "
            "(no interpolados); GWSA B disponible hasta junio de 2026; "
            "las mediciones de Casa del profesor Arturo son de agosto–septiembre de 2026 "
            "y por ahora no se superponen con GWSA B. "
            "Las cotas y profundidades de instalación fueron informadas el 20/10/2026, "
            "pero falta verificar el datum vertical y la interpretación/compensación "
            "de la presión de las sondas, especialmente Numae."
        )
        with st.expander("Fuentes, trazabilidad y notas para la revisión", expanded=False):
            st.markdown(
                "- **Proyecto recibido:** `Proyecto_GRACE_Leticia`, salidas procesadas el 4 de octubre de 2026.\n"
                "- **GRACE/GRACE-FO:** JPL Mascon RL06.3Mv04; estimación GWSA B con GLDAS Noah 0,25° v2.1.\n"
                "- **Referencia comparativa:** Romero–Piña, Zenodo DOI 10.5281/zenodo.14707819.\n"
                "- **Pozos:** registro manual UNAL y transductores Keller; valores depurados según reportes del proyecto.\n"
                "- **Referencias informadas (20/10/2026):** Numae terreno 77 m s. n. m., "
                "instalación 7 m; Casa del profesor Arturo 80 m, instalación 17 m; "
                "Colegio Pachovela 78 m, instalación 17 m (sin serie histórica). "
                "Cotas pendientes de confirmar datum vertical.\n"
                "- **Corrección provisional:** elevación = cota del terreno - profundidad "
                "de instalación + h_natural_m, solo si h_natural_m es altura de columna "
                "de agua sobre el sensor correctamente compensada.\n"
                "- **Río:** nivel IDEAM 48017010; no se ajusta arbitrariamente la cota de referencia.\n"
                "- **Publicación:** validar niveles y comparaciones con el equipo antes de denominarlos resultados concluyentes."
            )
        _descargar(grace, "SIAMS_GRACE_Leticia_datos_completos.csv",
                   "⬇️ Descargar GWSA y componentes", "siams_descargar_grace_metodo")


__all__ = ["mostrar_grace_leticia", "_serie_grace", "_niveles_campo",
           "_meses_comunes_normalizados", "_tabla_referencias_sondas"]
