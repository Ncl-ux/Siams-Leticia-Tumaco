"""Tablero IDEAM Leticia · SIAMS.

Visualización basada en el CSV mensual DHIME aportado al proyecto. Se integra
como vista propia bajo Clima y datos → Clima, sin pestañas superiores.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .ideam_leticia_datos import (
    ARCHIVO_IDEAM_LETICIA,
    MESES,
    catalogo_estaciones,
    climatologia_mensual,
    leer_dhime,
    matriz_calendario,
    resumen_registros,
    serie_mensual_anio,
    tabla_anual,
    ult_anio_completo,
)

# Paleta nativa SIAMS, alineada con siams/estilos.py.
VERDE_OSCURO = "#0b3d36"
VERDE = "#146c5c"
VERDE_2 = "#1f7f6c"
ACENTO = "#24a58c"
VERDE_CLARO = "#8ed7c1"
GRIS = "#9eaaa4"


@st.cache_data(show_spinner=False)
def _datos_archivo(ruta: str, mtime_ns: int) -> pd.DataFrame:
    """El mtime invalida la caché si se sustituye el CSV y se reinicia/rerun."""
    return leer_dhime(Path(ruta))


def _css() -> None:
    """Reutiliza las variables y fondos de SIAMS sin modificar el CSS global."""
    st.markdown("""
<style>
/* IDEAM se integra con la paleta original de SIAMS. No cambia el sidebar. */
.siams-ideam-hero {
    position: relative;
    overflow: hidden;
    padding: 22px clamp(20px, 3vw, 34px) 21px;
    border-radius: 16px;
    margin: 0 0 16px;
    background: linear-gradient(108deg,
        var(--siams-verde-oscuro, #0b3d36) 0%,
        #115246 62%,
        var(--siams-verde, #146c5c) 100%);
    border: 1px solid rgba(14, 76, 63, .65);
    box-shadow: var(--siams-sombra, 0 6px 18px rgba(0,0,0,.08));
}
.siams-ideam-hero::after {
    content: "";
    position: absolute;
    pointer-events: none;
    width: 275px;
    height: 275px;
    border-radius: 50%;
    right: -90px;
    top: -155px;
    border: 35px solid rgba(255,255,255,.055);
}
.siams-ideam-hero .eyebrow {
    display: flex; align-items: center; gap: 8px;
    color: #c8e8d9;
    font-size: .72rem;
    font-weight: 750;
    letter-spacing: .085em;
    margin-bottom: 9px;
}
.siams-ideam-hero .eyebrow::before {
    content: ""; width: 7px; height: 7px;
    background: #8ed7c1; border-radius: 50%;
    display: inline-block;
}
.siams-ideam-hero h1 {
    color: #fff !important;
    font-size: clamp(1.6rem, 2.65vw, 2.23rem);
    line-height: 1.18;
    letter-spacing: -.025em;
    font-weight: 790;
    margin: 0 0 9px;
}
.siams-ideam-hero h1 span { color: #a7e9d6; }
.siams-ideam-hero p {
    color: #f0faf5;
    font-size: .94rem;
    line-height: 1.55;
    margin: 0;
    max-width: 850px;
}
.siams-ideam-hero .ideam-chip {
    display: inline-flex;
    align-items: center;
    margin-top: 13px;
    padding: 6px 12px;
    color: #e9fff4;
    background: rgba(255,255,255,.105);
    border: 1px solid rgba(220,255,240,.28);
    border-radius: 999px;
    font-size: .75rem;
    font-weight: 680;
}
.siams-ideam-metric {
    box-sizing: border-box;
    min-height: 114px;
    padding: 14px 17px 12px;
    margin-bottom: 7px;
    background: var(--secondary-background-color, #f6f8f7);
    color: var(--text-color, #18342e);
    border: 1px solid var(--siams-borde, rgba(128,128,128,.28));
    border-left: 4px solid var(--siams-verde-2, #1f7f6c);
    border-radius: 15px;
    box-shadow: var(--siams-sombra, 0 6px 18px rgba(0,0,0,.08));
    overflow: hidden;
}
.siams-ideam-metric .m-label {
    color: var(--text-color, #213d34);
    opacity: .85;
    font-size: .83rem;
    font-weight: 750;
    margin-bottom: 6px;
}
.siams-ideam-metric .m-val {
    color: var(--siams-verde-oscuro, #0b3d36);
    font-size: clamp(1.25rem, 1.95vw, 1.97rem);
    font-weight: 820;
    letter-spacing: -.028em;
    line-height: 1.13;
    overflow-wrap: anywhere;
}
.siams-ideam-metric .m-val.teal {color: var(--siams-verde, #146c5c)}
.siams-ideam-metric .m-note {
    color: var(--text-color, #244039);
    opacity: .74;
    font-size: .76rem;
    line-height: 1.4;
    margin-top: 7px;
}
.siams-ideam-head {
    color: var(--text-color, #1c332b);
    font-size: 1.04rem;
    font-weight: 780;
    margin: 0 0 5px;
    letter-spacing: -.01em;
}
.siams-ideam-sub {
    color: var(--text-color, #29443a);
    opacity: .75;
    font-size: .83rem;
    margin: 0 0 11px;
}
.siams-ideam-station {
    padding: 12px 13px;
    margin: 0 0 10px;
    background: var(--secondary-background-color, #f6f8f7);
    border: 1px solid var(--siams-borde, rgba(128,128,128,.28));
    border-radius: 12px;
}
.siams-ideam-station .st-name {
    color: var(--text-color, #1d3930);
    font-weight: 760;
    font-size: .86rem;
    line-height: 1.45;
}
.siams-ideam-station .st-data {
    color: var(--text-color, #1d3930);
    opacity: .78;
    font-size: .78rem;
    margin-top: 4px;
}
.siams-ideam-track {
    margin-top: 10px;
    height: 7px;
    background: color-mix(in srgb, var(--siams-verde, #146c5c) 12%, var(--background-color, white));
    border-radius: 20px;
    overflow: hidden;
}
.siams-ideam-fill {
    height: 7px;
    border-radius: 20px;
    background: linear-gradient(90deg, #146c5c, #24a58c);
}
.siams-ideam-note {
    padding: 12px 14px;
    border-radius: 10px;
    background: color-mix(in srgb, var(--siams-verde, #146c5c) 9%, var(--background-color, white));
    border-left: 4px solid var(--siams-verde, #146c5c);
    color: var(--text-color, #1d3930);
    font-size: .81rem;
    line-height: 1.5;
}
.siams-ideam-foot {
    border-top: 1px solid var(--siams-borde, rgba(128,128,128,.28));
    color: var(--text-color, #1d3930);
    opacity: .76;
    padding: 12px 2px 0;
    margin-top: 10px;
    font-size: .78rem;
    line-height: 1.55;
}
.siams-ideam-filter-label {
    color: var(--text-color, #1d3930);
    font-size: .99rem;
    font-weight: 770;
    margin-top: 11px;
    margin-bottom: 3px;
}
@media (max-width:730px) {
    .siams-ideam-hero {padding: 18px; border-radius: 12px;}
    .siams-ideam-hero h1 {font-size: 1.65rem;}
    .siams-ideam-metric {min-height: 99px;}
}
</style>
""", unsafe_allow_html=True)


def _banner() -> None:
    """Encabezado con los mismos verdes institucionales de SIAMS."""
    st.markdown("""
<div class="siams-ideam-hero">
  <div class="eyebrow">SIAMS / Clima y datos / Leticia</div>
  <h1>Precipitación <span>IDEAM</span> · Leticia</h1>
  <p>La lluvia también cuenta nuestra historia. Explora los registros mensuales de
  DHIME, compara años y reconoce los periodos sin datos.</p>
  <div class="ideam-chip">Fuente IDEAM / DHIME · registros preliminares</div>
</div>
""", unsafe_allow_html=True)


def _metrica(etiqueta: str, valor: str, nota: str, *, teal: bool = False) -> None:
    st.markdown(
        f'<div class="siams-ideam-metric"><div class="m-label">{escape(etiqueta)}</div>'
        f'<div class="m-val{" teal" if teal else ""}">{escape(valor)}</div>'
        f'<div class="m-note">{escape(nota)}</div></div>',
        unsafe_allow_html=True,
    )


def _layout_plot(fig: go.Figure, *, alto: int = 320, margen_t: int = 20) -> go.Figure:
    fig.update_layout(
        height=alto,
        margin=dict(l=65, r=12, t=margen_t, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
        hoverlabel=dict(bgcolor=VERDE_OSCURO, font_color="white"),
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="h", x=1, xanchor="right", y=1.09, yanchor="bottom", font=dict(size=11)),
    )
    fig.update_xaxes(showline=True, linecolor="#cbd9d1", gridcolor="#e8efe9", zeroline=False)
    fig.update_yaxes(
        gridcolor="#e6eee9", zeroline=False, ticksuffix="",
        tickformat=",.0f", automargin=True, tickfont=dict(size=11),
    )
    return fig


def _grafica_mensual(
    historica: pd.DataFrame,
    actual: pd.DataFrame,
    anio: int,
    periodo: str,
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=MESES, y=historica["Media_mm"], name=f"Promedio {periodo}", mode="lines+markers",
        line=dict(color=VERDE_OSCURO, width=2.7, shape="spline", smoothing=0.65),
        marker=dict(size=7), connectgaps=False,
        hovertemplate="%{y:,.1f} mm<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=MESES, y=actual["Valor"], name=str(anio), mode="lines+markers",
        line=dict(color=ACENTO, width=2.8, shape="spline", smoothing=0.65),
        marker=dict(size=8), connectgaps=False,
        hovertemplate="%{y:,.1f} mm<extra></extra>",
    ))
    fig.update_yaxes(
        title="Precipitación (mm)", rangemode="tozero",
        tickformat=",.0f", nticks=7, automargin=True,
    )
    fig.update_xaxes(categoryorder="array", categoryarray=MESES)
    return _layout_plot(fig, alto=327, margen_t=24)


def _grafica_anual(df: pd.DataFrame, seleccionado: int) -> go.Figure:
    fig = go.Figure()
    colores = [
        (ACENTO if y == seleccionado and completo else
         VERDE if completo else "#a6b7b0")
        for y, completo in zip(df["Anio"], df["Completo"])
    ]
    custom = np.stack([df["Meses"], df["Completo"].map({True: "Completo", False: "Parcial"})], axis=1)
    fig.add_trace(go.Bar(
        x=df["Anio"], y=df["Precipitacion_mm"], name="Acumulado observado",
        marker=dict(color=colores, line=dict(width=0)),
        customdata=custom,
        hovertemplate="Año %{x}<br>%{y:,.1f} mm<br>%{customdata[0]}/12 meses · %{customdata[1]}<extra></extra>",
    ))
    fig.update_layout(showlegend=False, bargap=0.24, hovermode="closest")
    fig.update_xaxes(title=None, dtick=5, tickformat="d")
    fig.update_yaxes(
        title="Precipitación observada (mm)", rangemode="tozero",
        tickformat=",.0f", nticks=7, automargin=True,
    )
    return _layout_plot(fig, alto=313).update_layout(showlegend=False)


def _grafica_calendario(tabla: pd.DataFrame) -> go.Figure:
    tabla = tabla.sort_index(ascending=False)
    valores = tabla.to_numpy(dtype=float)
    etiquetas = np.empty(valores.shape, dtype=object)
    for i in range(valores.shape[0]):
        for j in range(valores.shape[1]):
            etiquetas[i, j] = f"{valores[i, j]:,.1f} mm" if np.isfinite(valores[i, j]) else "Dato no disponible"
    fig = go.Figure(go.Heatmap(
        z=valores, x=MESES, y=tabla.index.astype(str).tolist(),
        text=etiquetas,
        colorscale=[
            [0.00, "#edf4f0"], [0.12, "#c8eadd"], [0.32, "#83cbb2"],
            [0.53, "#3c9c82"], [0.76, "#146c5c"], [1.00, "#0b3d36"],
        ],
        zmin=0, zmax=max(700.0, float(np.nanmax(tabla.to_numpy(dtype=float)))),
        colorbar=dict(title="mm", thickness=10, len=0.77, x=1.015),
        hovertemplate="Año %{y}, %{x}<br>%{text}<extra></extra>",
        xgap=1.8, ygap=1.8, showscale=True,
    ))
    fig.update_layout(
        height=max(313, len(tabla) * 11 + 70),
        margin=dict(l=52, r=7, t=8, b=24),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#e8eeeb", font=dict(size=11),
        xaxis=dict(side="top", showgrid=False, ticks="", tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, ticks="", dtick=5, autorange="reversed"),
    )
    # El eje y se renderiza de arriba a abajo en el orden indicado; no se
    # completan visualmente las observaciones faltantes (NaN).
    return fig


def _estaciones_html(catalogo: pd.DataFrame) -> None:
    for fila in catalogo.itertuples():
        nombre = escape(str(fila.NombreEstacion))
        pct = float(fila.CoberturaPct)
        periodo = f"{fila.PrimeraFecha:%Y-%m} a {fila.UltimaFecha:%Y-%m}"
        icono = "🌧️" if "AEROPUERTO" in nombre.upper() else "🌳"
        st.markdown(
            f'<div class="siams-ideam-station">'
            f'<div class="st-name">{icono} &nbsp;{nombre} · {escape(str(fila.CodigoEstacion))}</div>'
            f'<div class="st-data">{fila.Registros} registros mensuales · '
            f'{pct:.1f}% de cobertura</div>'
            f'<div class="st-data">{escape(periodo)}</div>'
            f'<div class="siams-ideam-track"><div class="siams-ideam-fill" style="width:{min(100,pct):.1f}%"></div></div>'
            f'</div>', unsafe_allow_html=True,
        )


def mostrar_ideam_leticia() -> None:
    """Panel de precipitación IDEAM como apartado junto a Clima."""
    _css()
    _banner()
    if not ARCHIVO_IDEAM_LETICIA.is_file():
        st.error("No se encontró el CSV de precipitación mensual DHIME para Leticia.")
        st.code(str(ARCHIVO_IDEAM_LETICIA), language="text")
        return
    try:
        datos = _datos_archivo(str(ARCHIVO_IDEAM_LETICIA), ARCHIVO_IDEAM_LETICIA.stat().st_mtime_ns)
        catalogo = catalogo_estaciones(datos)
        resumen = resumen_registros(datos)
    except (OSError, UnicodeError, ValueError, pd.errors.ParserError) as exc:
        st.error("No se pudo interpretar el archivo DHIME sin comprometer la calidad de los resultados.")
        st.code(str(exc), language="text")
        return

    codigo_principal = "48015050" if "48015050" in set(catalogo["CodigoEstacion"]) else str(catalogo.iloc[0]["CodigoEstacion"])
    principal = datos[datos["CodigoEstacion"].eq(codigo_principal)]
    anio_completo_principal = ult_anio_completo(principal)
    tabla_principal = tabla_anual(principal)
    total_principal = tabla_principal.loc[tabla_principal["Anio"].eq(anio_completo_principal), "Precipitacion_mm"]
    total_anio = float(total_principal.iloc[0]) if not total_principal.empty else np.nan

    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        _metrica("◉ Registros", f"{resumen['registros']:,}".replace(",", "."), "Meses reportados en DHIME")
    with c2:
        _metrica("⌖ Estaciones", str(resumen["estaciones"]), "Estaciones disponibles")
    with c3:
        _metrica("▦ Periodo global", f"{resumen['anio_min']}–{resumen['anio_max']}", "Hay periodos sin información")
    with c4:
        etiqueta = f"Precipitación {anio_completo_principal}" if anio_completo_principal else "Último año completo"
        _metrica(etiqueta, f"{total_anio:,.1f} mm".replace(",", "X").replace(".", ",").replace("X", ".") if np.isfinite(total_anio) else "Sin dato",
                 "Aeropuerto Vásquez Cobo" if codigo_principal == "48015050" else str(codigo_principal), teal=True)

    estaciones_opciones = {
        f"{r.NombreEstacion} · {r.CodigoEstacion}": str(r.CodigoEstacion)
        for r in catalogo.itertuples()
    }
    st.markdown('<div class="siams-ideam-filter-label">Explora las observaciones</div>', unsafe_allow_html=True)
    a, b = st.columns([1.6, 1], gap="medium")
    with a:
        estacion_texto = st.selectbox(
            "Estación IDEAM", list(estaciones_opciones),
            key="siams_ideam_le_estacion",
        )
    codigo = estaciones_opciones[estacion_texto]
    estacion = datos[datos["CodigoEstacion"].eq(codigo)].copy()
    years = sorted(estacion["Anio"].unique().tolist())
    defecto = ult_anio_completo(estacion)
    with b:
        anio = st.selectbox(
            "Año de comparación", years[::-1],
            index=(years[::-1].index(defecto) if defecto in years else 0),
            key="siams_ideam_le_anio",
        )

    etiqueta_estacion = str(catalogo.loc[catalogo["CodigoEstacion"].eq(codigo), "NombreEstacion"].iloc[0])
    referencia_inicio, referencia_fin = (1990, 2016)
    clim, periodos_completos = climatologia_mensual(estacion, referencia_inicio, referencia_fin)
    if not periodos_completos:
        # Amacayacu tiene datos fragmentados; elegir todos los años completos
        # del período realmente registrado, evitando inferir meses.
        referencia_inicio = int(estacion["Anio"].min())
        referencia_fin = int(estacion["Anio"].max())
        clim, periodos_completos = climatologia_mensual(estacion, referencia_inicio, referencia_fin)
    serie_anio = serie_mensual_anio(estacion, anio)
    tabla_anios = tabla_anual(estacion)
    fila_anio = tabla_anios.loc[tabla_anios["Anio"].eq(anio)].iloc[0]
    total_ref = sum(clim["Media_mm"].dropna()) if not clim["Media_mm"].isna().all() else np.nan

    izquierda, derecha = st.columns([1.55, 1], gap="medium")
    with izquierda:
        with st.container(border=True):
            st.markdown('<div class="siams-ideam-head">▥ &nbsp;Precipitación mensual</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="siams-ideam-sub">{escape(etiqueta_estacion)} · Comparación con {anio}</div>', unsafe_allow_html=True)
            if periodos_completos:
                fig = _grafica_mensual(clim, serie_anio, anio, f"{referencia_inicio}–{referencia_fin}")
                st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, theme="streamlit")
                st.caption(f"Climatología calculada con {len(periodos_completos)} años completos del periodo {referencia_inicio}–{referencia_fin}; no se completan los meses faltantes.")
            else:
                st.info("No hay años completos suficientes para construir una climatología mensual.")
    with derecha:
        with st.container(border=True):
            st.markdown('<div class="siams-ideam-head">⌖ &nbsp;Estaciones IDEAM</div>', unsafe_allow_html=True)
            st.markdown('<div class="siams-ideam-sub">Cobertura calculada dentro del intervalo de cada estación</div>', unsafe_allow_html=True)
            _estaciones_html(catalogo)
            if np.isfinite(total_ref):
                st.markdown(
                    f'<div class="siams-ideam-note">Promedio anual histórico de referencia: '
                    f'<strong>{total_ref:,.0f} mm</strong> ({len(periodos_completos)} años completos). '
                    f'<br>Registros del archivo: <strong>preliminares</strong>.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("Sin climatología anual de referencia para esta estación.")

    izquierda2, derecha2 = st.columns([1.1, 1], gap="medium")
    with izquierda2:
        with st.container(border=True):
            st.markdown('<div class="siams-ideam-head">▥ &nbsp;Historia de la lluvia</div>', unsafe_allow_html=True)
            st.markdown('<div class="siams-ideam-sub">Acumulados observados por año · tonos claros = años parciales</div>', unsafe_allow_html=True)
            st.plotly_chart(_grafica_anual(tabla_anios, anio), use_container_width=True, config={"displaylogo": False}, theme="streamlit")
            if not bool(fila_anio["Completo"]):
                st.warning(f"{anio}: solo {int(fila_anio['Meses'])}/12 meses registrados; el acumulado no representa el total anual.")
            else:
                st.caption(f"{anio}: {float(fila_anio['Precipitacion_mm']):,.1f} mm, con 12 meses registrados.")
    with derecha2:
        with st.container(border=True):
            st.markdown('<div class="siams-ideam-head">▦ &nbsp;Calendario histórico de precipitaciones</div>', unsafe_allow_html=True)
            st.markdown('<div class="siams-ideam-sub">Cada celda es un mes · celdas grises = datos no disponibles</div>', unsafe_allow_html=True)
            matriz = matriz_calendario(estacion)
            st.plotly_chart(_grafica_calendario(matriz), use_container_width=True, config={"displaylogo": False}, theme="streamlit")

    with st.expander("📋 Metodología, control de calidad y descargas", expanded=False):
        st.markdown(
            "**Fuente:** archivo DHIME suministrado para SIAMS, variable PRECIPITACION, "
            "parámetro *Precipitación total mensual* (mm). Todos los registros del archivo "
            "están marcados como **Preliminar**. Las precipitaciones se visualizan "
            "individualmente por estación, sin mezclar sus periodos de cobertura. "
            "Los totales con menos de 12 meses se muestran como **acumulados parciales**, "
            "no se anualizan. La climatología promedia los meses de años completos. "
            "Los meses faltantes no se imputan."
        )
        st.dataframe(
            estacion[["CodigoEstacion", "NombreEstacion", "Fecha", "Valor", "Unidad", "NivelAprobacion"]]
            .sort_values("Fecha", ascending=False), use_container_width=True, hide_index=True,
        )
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "⬇️ Descargar serie mensual seleccionada",
                estacion[["CodigoEstacion", "NombreEstacion", "Fecha", "Valor", "Unidad", "NivelAprobacion"]]
                .to_csv(index=False).encode("utf-8-sig"),
                file_name=f"SIAMS_IDEAM_Leticia_{codigo}_mensual.csv", mime="text/csv",
                key="siams_ideam_le_download_mensual",
            )
        with d2:
            st.download_button(
                "⬇️ Descargar resumen anual",
                tabla_anios.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"SIAMS_IDEAM_Leticia_{codigo}_anual.csv", mime="text/csv",
                key="siams_ideam_le_download_anual",
            )
    st.markdown(
        '<div class="siams-ideam-foot">SIAMS · Datos IDEAM/DHIME suministrados al semillero · '
        'Valores preliminares sujetos a revisión. Análisis exploratorio: no implica validación '
        'oficial de las series ni atribución causal de cambios hidroclimáticos.</div>',
        unsafe_allow_html=True,
    )


__all__ = ["mostrar_ideam_leticia"]
