"""Pantalla Streamlit SIAMS — A1, homogeneidad de series (Tumaco).

No modifica ni recalcula los datos; visualiza resultados auditados previamente.
Uso: from siams.homogeneidad_a1 import renderizar_a1_homogeneidad
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except ImportError:
    go = None


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "a1" / "tumaco"
CSV_MENSUAL = "SIAMS_A1_COCO_Granja_mensual.csv"
CSV_COBERTURA = "SIAMS_A1_Cobertura_Granja_anual.csv"
JSON_RESULTADOS = "SIAMS_A1_Granja_Analisis_Ampliado.json"
EXCEL_RESULTADOS = "SIAMS_A1_Granja_El_Mira_Ampliado.xlsx"
EXCEL_INICIAL = "SIAMS_A1_SNHT_Homogeneidad_Actualizado.xlsx"
COLOR_COCO = "#176EAB"
COLOR_GRANJA = "#139B89"
COLOR_CAMBIO = "#C87425"


def cargar_datos(base: Path = DATA):
    """Carga resultados precomputados, conservando los archivos fuente intactos."""
    faltantes = [name for name in (CSV_MENSUAL, CSV_COBERTURA, JSON_RESULTADOS)
                 if not (base / name).is_file()]
    if faltantes:
        raise FileNotFoundError("Faltan datos A1 en " + str(base) + ": " + ", ".join(faltantes))
    m = pd.read_csv(base / CSV_MENSUAL, encoding="utf-8-sig")
    c = pd.read_csv(base / CSV_COBERTURA, encoding="utf-8-sig")
    resultados = json.loads((base / JSON_RESULTADOS).read_text(encoding="utf-8"))
    requeridas = {"mes", "coco_mm", "granja_mm", "ln_relativo", "cobertura_coco_pct", "cobertura_granja_pct"}
    if not requeridas.issubset(m.columns):
        raise ValueError("El CSV mensual A1 tiene columnas ausentes: " + ", ".join(sorted(requeridas - set(m.columns))))
    m["fecha"] = pd.to_datetime(m["mes"], format="%Y-%m", errors="raise")
    m["anio"] = m["fecha"].dt.year
    return m.sort_values("fecha").reset_index(drop=True), c, resultados


def _grafico_base(titulo: str, ylabel: str):
    fig = go.Figure()
    fig.update_layout(
        title={"text": titulo, "x": 0.02, "font": {"size": 18}},
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        margin={"l": 12, "r": 12, "t": 58, "b": 18},
        hovermode="x unified", legend={"orientation": "h", "y": -0.24, "x": 0},
        xaxis={"title": "Fecha", "showgrid": True, "gridcolor": "#edf1f4"},
        yaxis={"title": ylabel, "showgrid": True, "gridcolor": "#edf1f4"},
    )
    return fig


def _marca_cambio(fig, fecha, etiqueta, color=COLOR_CAMBIO, dash="dash"):
    fig.add_shape(type="line", x0=fecha, x1=fecha, y0=0, y1=1, yref="paper",
                  line={"color": color, "width": 1.8, "dash": dash})
    fig.add_annotation(x=fecha, y=1, yref="paper", yanchor="bottom",
                       text=etiqueta, showarrow=False, font={"size": 11, "color": color},
                       bgcolor="rgba(255,255,255,0.84)")


def _numero(v, n=3):
    if v is None:
        return "No disponible"
    return f"{float(v):.{n}f}".replace(".", ",")


def _lineas_mensuales(df):
    fig = _grafico_base("Precipitación mensual observada", "Precipitación (mm/mes)")
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["coco_mm"], name="COCO EL",
                             mode="lines", line={"color": COLOR_COCO, "width": 1.7}))
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["granja_mm"], name="Granja El Mira",
                             mode="lines", line={"color": COLOR_GRANJA, "width": 1.7}))
    _marca_cambio(fig, pd.Timestamp("1997-06-01"), "1997 · COCO")
    return fig


def _relacion_estaciones(df):
    fig = _grafico_base("Contraste mensual entre estaciones", "ln[(COCO+1)/(Granja+1)]")
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["ln_relativo"], name="Relación transformada",
                             mode="lines", line={"color": COLOR_COCO, "width": 1.8}))
    fig.add_hline(y=0, line_dash="dot", line_color="#9AA7B4")
    _marca_cambio(fig, pd.Timestamp("1994-03-01"), "1994 · SNHT relativo", "#9A61AC")
    _marca_cambio(fig, pd.Timestamp("1997-06-01"), "1997 · SNHT absoluto")
    return fig


def _promedios_anuales(df):
    annual = df.groupby("anio", as_index=False).agg(
        coco_mm=("coco_mm", "mean"), granja_mm=("granja_mm", "mean"),
        meses=("mes", "count"))
    # Evita presentar meses incompletos como totales anuales completos.
    annual = annual.loc[annual["meses"] >= 9].copy()
    fig = _grafico_base("Promedio mensual por año (años con ≥9 meses válidos)", "Precipitación media (mm/mes)")
    fig.add_trace(go.Bar(x=annual["anio"], y=annual["coco_mm"], name="COCO EL",
                         marker_color=COLOR_COCO))
    fig.add_trace(go.Bar(x=annual["anio"], y=annual["granja_mm"], name="Granja El Mira",
                         marker_color=COLOR_GRANJA))
    fig.update_layout(barmode="group", xaxis={"title": "Año", "type": "category"})
    return fig


def _metrica_p(resultado, etiqueta):
    return f"{etiqueta}: T={_numero(resultado.get('T_SNHT'))} · p={_numero(resultado.get('p_bloques'))} · cambio {resultado.get('corte','—')}"


def renderizar_a1_homogeneidad():
    """Renderiza el panel. Puede llamarse desde app.py, desde st.navigation o pages/."""
    st.markdown("""
<style>
.a1-kicker {letter-spacing: .13em; text-transform: uppercase; font-size: .73rem;
    font-weight: 750; color: #138C86; margin-bottom: .28rem;}
.a1-intro {color:#677483; font-size: 1rem; margin-top:-.5rem;}
.a1-info {border-left:4px solid #168C83; padding: .75rem 1rem;
          background:rgba(24,154,137,0.065); border-radius: 0 .45rem .45rem 0;
          color:inherit; line-height:1.5; margin: .6rem 0 1rem 0;}
</style>
""", unsafe_allow_html=True)
    st.markdown('<div class="a1-kicker">SIAMS / Control de calidad / A1</div>', unsafe_allow_html=True)
    st.title("Homogeneidad y tendencias · Tumaco")
    st.markdown('<div class="a1-intro">Validación estadística de la precipitación en COCO EL frente a Granja El Mira (IDEAM).</div>',
                unsafe_allow_html=True)

    if go is None:
        st.error("Falta Plotly. En la terminal ejecuta: python -m pip install plotly")
        return
    try:
        df, cobertura, resultados = cargar_datos()
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        st.error(f"No pude cargar los resultados A1: {exc}")
        st.info("Copia la carpeta data/processed/a1/tumaco del paquete de integración.")
        return

    rel = resultados.get("snht_relativo", {}).get("periodo_completo", {})
    abs_coco = resultados.get("snht_absoluto", {}).get("COCO_EL_1985_2025", {})
    abs_granja = resultados.get("snht_absoluto", {}).get("GRANJA_1985_2025", {})
    cc = resultados.get("control", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meses comparables", f"{int(cc.get('meses_validos', len(df))):,}".replace(",", "."))
    c2.metric("Correlación mensual", _numero(resultados.get("correlaciones", {}).get("pearson")))
    c3.metric("SNHT absoluto COCO", abs_coco.get("corte", "—"))
    c4.metric("SNHT relativo", rel.get("corte", "—"))
    st.markdown('''<div class="a1-info"><b>Estado:</b> validación de homogeneidad pendiente de certificación.
    Las pruebas señalan cambios estadísticos, pero no atribuyen una causa instrumental ni justifican corregir
    automáticamente la serie histórica.</div>''', unsafe_allow_html=True)

    years = sorted(df["anio"].unique().tolist())
    izquierda, derecha = st.columns([3, 1])
    with izquierda:
        interval = st.slider("Periodo mostrado en los gráficos", int(years[0]), int(years[-1]),
                             (int(years[0]), int(years[-1])), key="a1_tumaco_periodo")
    with derecha:
        st.caption("El filtro no recalcula los SNHT publicados; solo cambia los gráficos y la tabla.")
    vista = df.loc[df["anio"].between(*interval)].copy()
    if vista.empty:
        st.warning("No hay meses comparables dentro del periodo seleccionado.")
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "Lluvia comparada", "Cambios y SNHT", "Calidad y cobertura", "Resultados y descargas"
    ])
    with tab1:
        st.plotly_chart(_lineas_mensuales(vista), use_container_width=True)
        st.plotly_chart(_promedios_anuales(vista), use_container_width=True)
        st.caption("Se muestran datos IDEAM-IDEAM con cobertura diaria ≥90 % en cada estación. "
                   "Los promedios anuales solo incluyen años con al menos 9 meses válidos.")

    with tab2:
        st.plotly_chart(_relacion_estaciones(vista), use_container_width=True)
        a, b, c = st.columns(3)
        a.metric("COCO EL · SNHT absoluto", _numero(abs_coco.get("T_SNHT")))
        b.metric("Granja · SNHT absoluto", _numero(abs_granja.get("T_SNHT")))
        c.metric("COCO/Granja · SNHT relativo", _numero(rel.get("T_SNHT")))
        st.markdown("**Detalle de pruebas calculadas sobre la serie completa:**")
        st.write("• " + _metrica_p(abs_coco, "COCO absoluto"))
        st.write("• " + _metrica_p(abs_granja, "Granja absoluto"))
        st.write("• " + _metrica_p(rel, "Contraste relativo"))
        ventana = resultados.get("snht_relativo", {}).get("ventana_1990_2005", {})
        st.write("• " + _metrica_p(ventana, "Contraste relativo 1990–2005"))
        st.caption("La fecha del máximo SNHT relativo (1994) difiere del SNHT absoluto de COCO (1997). "
                   "La sensibilidad temporal impide declarar homogeneidad definitiva.")

    with tab3:
        st.markdown("**Trazabilidad de las observaciones**")
        v1, v2, v3 = st.columns(3)
        v1.metric("Meses aceptados", str(cc.get("meses_validos", "—")))
        v2.metric("Meses descartados", str(cc.get("meses_rechazados", "—")))
        v3.metric("Duplicados con discrepancias", str(cc.get("filas_duplicadas_discordantes", "—")))
        st.dataframe(cobertura, use_container_width=True, hide_index=True)
        st.caption("La cobertura corresponde a Granja El Mira, incluida su etapa anterior a COCO EL. "
                   "Hay observaciones catalogadas en DHIME como preliminares o en revisión.")
        st.markdown("**Archivos utilizados para el análisis**")
        fuentes = pd.DataFrame(resultados.get("archivos_granja", []))
        if not fuentes.empty:
            fuentes["nivel_aprobacion"] = fuentes["nivel_aprobacion"].apply(
                lambda v: ", ".join(f"{k}: {n}" for k, n in v.items()) if isinstance(v, dict) else str(v))
            st.dataframe(fuentes, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("**Conclusión metodológica**")
        st.write(resultados.get("conclusion", "No se dispone de conclusión."))
        st.info("A1: Pettitt, Mann-Kendall y SNHT realizados; comparación IDEAM ampliada. "
                "Pendiente: metadatos instrumentales, estación independiente adicional y dictamen definitivo.")
        st.caption("El informe inicial del A1 también conserva Pettitt y Mann-Kendall; los paneles anteriores muestran la ampliación SNHT con referencia IDEAM.")
        st.markdown("**Serie mensual comparada**")
        st.dataframe(vista.drop(columns=["anio", "fecha"], errors="ignore"),
                     use_container_width=True, hide_index=True)
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.download_button("Descargar meses filtrados (.csv)",
                               vista.drop(columns=["anio", "fecha"], errors="ignore")
                               .to_csv(index=False).encode("utf-8-sig"),
                               file_name="SIAMS_A1_Tumaco_meses_filtrados.csv", mime="text/csv")
        with col_b:
            excel = DATA / EXCEL_RESULTADOS
            if excel.is_file():
                st.download_button("Excel · contraste ampliado", excel.read_bytes(),
                                   file_name=EXCEL_RESULTADOS,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col_c:
            excel_inicial = DATA / EXCEL_INICIAL
            if excel_inicial.is_file():
                st.download_button("Excel · A1 Pettitt y MK", excel_inicial.read_bytes(),
                                   file_name=EXCEL_INICIAL,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


if __name__ == "__main__":
    # Para pruebas puntuales: streamlit run siams/homogeneidad_a1.py
    st.set_page_config(page_title="SIAMS — A1 Homogeneidad", page_icon="🌧️", layout="wide")
    renderizar_a1_homogeneidad()
