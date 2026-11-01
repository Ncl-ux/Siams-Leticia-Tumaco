"""Secciones nuevas de la actualización de sedes 2026: niveles de agua subterránea, carga de datos
de campo (XUE Hub), pruebas de bombeo, fisicoquímica de Arauca/Tumaco, isótopos y 'última actualización'."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from siams.datos_campo import URL_APP_XUE, cargar_esquema

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "data" / "processed"
ARCH_NIVELES = {"Arauca": "niveles_arauca.csv", "La Paz": "niveles_la_paz.csv", "Leticia": "niveles_leticia.csv",
                "Tumaco": "niveles_tumaco.csv", "Bogotá": "niveles_bogota.csv"}
COORD_SEDE = {"Leticia": (-4.193717, -69.941001), "Tumaco": (1.610206, -78.720520),
              "Arauca": (7.012223, -70.743388), "La Paz": (10.390218, -73.200389),
              "Bogotá": (4.638193, -74.084046), "Medellín": (6.260650, -75.579592),
              "San Andrés": (12.536552, -81.707935)}


def _leer_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def ultima_actualizacion(defecto: str) -> str:
    """Fecha más reciente entre la actualización automática semanal y el procesamiento de niveles."""
    fechas = []
    for p, k in ((PROC / "actualizacion" / "metadatos.json", "ultima_actualizacion"),
                 (PROC / "niveles" / "metadatos.json", "generado")):
        v = _leer_json(p).get(k)
        if v:
            fechas.append(pd.Timestamp(v).tz_convert("America/Bogota") if pd.Timestamp(v).tzinfo else pd.Timestamp(v))
    if not fechas:
        return defecto
    f = max(fechas)
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
             "octubre", "noviembre", "diciembre"]
    return f"{f.day} de {meses[f.month - 1]} de {f.year}"


# ----------------------------------------------------------------------------- niveles
@st.cache_data(show_spinner=False)
def _niveles(sede: str) -> pd.DataFrame:
    p = PROC / "niveles" / ARCH_NIVELES[sede]
    return pd.read_csv(p, parse_dates=["fecha"]) if p.exists() else pd.DataFrame()


@st.cache_data(show_spinner=False)
def _pozos() -> pd.DataFrame:
    p = PROC / "niveles" / "pozos.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def mostrar_niveles(territorio: str) -> None:
    st.title(f"💧 Niveles de agua subterránea – {territorio}")
    if territorio not in ARCH_NIVELES:
        st.info("Esta sede no tiene pozos con monitoreo de nivel en SIAMS.")
        return
    pozos = _pozos()
    pozos = pozos[pozos.sede == territorio] if not pozos.empty else pozos
    d = _niveles(territorio)
    if d.empty:
        st.warning("No se encontró la serie procesada (data/processed/niveles).")
        return
    meta = _leer_json(PROC / "niveles" / "metadatos.json")
    st.caption(
        "Cota del terreno = Copernicus DEM GLO-30 − 1,5 m (sesgo estimado), salvo que exista cota levantada. "
        "Cota del nivel = cota del terreno − profundidad del agua. En sondas de presión, profundidad = "
        "profundidad del sensor − carga de agua sobre el sensor. Si no se conoce la profundidad del sensor "
        "solo se publica la columna de agua (sin cota).")
    con_serie = pozos[pozos.pozo_id.isin(d.pozo_id.unique())]
    if not con_serie.empty:
        mapa = px.scatter_map(con_serie, lat="lat", lon="lon", hover_name="pozo_id",
                              hover_data={"nombre": True, "cota_terreno_msnm": ":.2f", "lat": ":.5f", "lon": ":.5f"},
                              center={"lat": con_serie.lat.mean(), "lon": con_serie.lon.mean()},
                              zoom=13 if territorio != "Bogotá" else 11, height=330)
        mapa.update_traces(marker={"size": 12, "color": "#1f77b4"})
        mapa.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}, map_style="open-street-map")
        st.plotly_chart(mapa, use_container_width=True)
    ids = sorted(d.pozo_id.unique())
    pozo = st.selectbox("Pozo", ids, index=0)
    s = d[d.pozo_id == pozo].sort_values("fecha")
    info = pozos[pozos.pozo_id == pozo].iloc[0] if (pozos.pozo_id == pozo).any() else None
    tiene_cota = s.cota_nivel_msnm.notna().any()
    var = st.radio("Variable", ["Cota del nivel (m s.n.m.)", "Profundidad del nivel (m)", "Carga sobre el sensor (m)"]
                   if tiene_cota else ["Carga sobre el sensor (m)"], horizontal=True)
    col = {"Cota del nivel (m s.n.m.)": "cota_nivel_msnm", "Profundidad del nivel (m)": "profundidad_nivel_m",
           "Carga sobre el sensor (m)": "carga_sobre_sensor_m"}[var]
    excluir = st.checkbox("Ocultar lecturas marcadas (sensor fuera del agua / posible bombeo)", value=True)
    v = s[s.calidad == "ok"] if excluir and "calidad" in s else s
    fig = px.scatter(v, x="fecha", y=col, color="metodo", height=420) if v.metodo.nunique() > 1 else \
        px.line(v, x="fecha", y=col, height=420)
    if col == "profundidad_nivel_m":
        fig.update_yaxes(autorange="reversed")
    fig.update_traces(marker={"size": 4}, selector={"mode": "markers"})
    fig.update_layout(yaxis_title=var, xaxis_title="", margin={"t": 10})
    st.plotly_chart(fig, use_container_width=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registros", f"{len(s):,}".replace(",", "."))
    c2.metric("Cota del terreno", f"{info.cota_terreno_msnm:.2f} m" if info is not None and pd.notna(info.cota_terreno_msnm) else "—")
    c3.metric("Prof. del sensor", f"{info.prof_sensor_m:g} m" if info is not None and pd.notna(info.prof_sensor_m) else "desconocida")
    c4.metric("Último dato", s.fecha.max().strftime("%Y-%m-%d"))
    if s.supuesto.notna().any():
        st.info("Supuestos: " + " | ".join(s.supuesto.dropna().unique()[:3]))
    if info is not None:
        with st.expander("Ficha del pozo"):
            st.dataframe(info.dropna().to_frame("valor"), use_container_width=True)
    st.caption(f"Fuente: sondas Keller/Diver y mediciones manuales del proyecto; Bogotá incluye la serie de la "
               f"Oficina de Gestión Ambiental (OGA) UNAL. {meta.get('fuente_dem', '')}.")
    st.download_button("Descargar serie (CSV)", s.to_csv(index=False).encode("utf-8"), f"niveles_{pozo}.csv", "text/csv")


def mostrar_cargar_datos_campo() -> None:
    st.title("📲 Cargar datos de campo")
    st.info("La captura en campo (sin conexión) se hace con la aplicación de XUE Hub. SIAMS recibe los archivos "
            "exportados, los valida con el esquema de abajo y los integra en el siguiente procesamiento.")
    if URL_APP_XUE:
        st.link_button("Abrir app de campo (XUE Hub)", URL_APP_XUE)
    else:
        st.button("Abrir app de campo (XUE Hub) – enlace pendiente", disabled=True)
    st.subheader("Esquema del archivo CSV")
    st.dataframe(cargar_esquema(), use_container_width=True, hide_index=True)
    st.caption("Validación local: python scripts/validar_datos_campo.py archivo.csv")


# ----------------------------------------------------------------------------- bombeo
def mostrar_pruebas_bombeo(territorio: str) -> None:
    st.title(f"🛠️ Pruebas de bombeo – {territorio}")
    p = PROC / "bombeo" / "resumen_pruebas_bombeo.csv"
    if not p.exists():
        st.warning("No se encontró el resumen de pruebas de bombeo.")
        return
    d = pd.read_csv(p)
    d = d[d.sede == territorio]
    if d.empty:
        st.info("No hay pruebas de bombeo documentadas para esta sede en SIAMS.")
        return
    t = d[d.parametro == "transmisividad"]
    cols = st.columns(4)
    for c, par, et in zip(cols, ["caudal_constante", "abatimiento", "capacidad_especifica", "nivel_estatico"],
                          ["Caudal", "Abatimiento", "Capacidad específica", "Nivel estático"]):
        f = d[d.parametro == par]
        if not f.empty:
            c.metric(et, f"{f.valor.iloc[0]:g} {f.unidad.iloc[0]}")
    if len(t) > 1:
        fig = px.bar(t, x="metodo", y="valor", labels={"valor": "T (m²/d)", "metodo": ""}, height=320)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(d[["parametro", "valor", "unidad", "metodo", "fecha_prueba", "pagina_pdf", "cita", "observacion"]],
                 use_container_width=True, hide_index=True)
    for f in d.fuente.unique():
        if len(f) > 20:
            st.caption("Fuente: " + f)
    for o in d.observacion.dropna().unique():
        st.warning(o)


# ----------------------------------------------------------------------------- fisicoquímica
def _stiff(fila: pd.Series) -> go.Figure:
    cat = [fila.nak_meq, fila.ca_meq, fila.mg_meq]
    an = [fila.cl_meq, fila.hco3_meq, fila.so4_meq]
    y = [2, 1, 0]
    x = [-c for c in cat] + an[::-1]
    yy = y + y[::-1]
    fig = go.Figure(go.Scatter(x=x + [x[0]], y=yy + [yy[0]], fill="toself", mode="lines+markers"))
    fig.update_layout(height=260, margin={"t": 30, "b": 10}, title=f"Stiff – {fila.pozo} {fila.fecha}",
                      xaxis_title="← cationes (meq/L)   aniones (meq/L) →",
                      yaxis={"tickvals": y, "ticktext": ["Na+K | Cl", "Ca | HCO₃+CO₃", "Mg | SO₄"]})
    return fig


def _piper(d: pd.DataFrame) -> go.Figure:
    """Triángulos de cationes y aniones (proyección ternaria) del diagrama de Piper."""
    fig = go.Figure()
    for nombre, cols, dx in (("Cationes", ("pct_ca", "pct_mg", "pct_nak"), 0), ("Aniones", ("pct_hco3", "pct_so4", "pct_cl"), 1.2)):
        izq, arr, der = (d[c] / 100 for c in cols)  # izq = vértice inferior izq., arr = superior, der = inferior der.
        x = dx + der + arr / 2
        y = arr * math.sqrt(3) / 2
        fig.add_trace(go.Scatter(x=[dx, dx + 1, dx + .5, dx], y=[0, 0, math.sqrt(3) / 2, 0], mode="lines",
                                 line={"color": "gray"}, showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name=nombre,
                                 text=d.pozo + " " + d.fecha.astype(str), marker={"size": 10}))
    for t, xx, yy in (("Ca", -.05, -.05), ("Mg", .5, .92), ("Na+K", .95, -.09),
                      ("HCO₃", 1.25, -.09), ("SO₄", 1.7, .92), ("Cl", 2.25, -.05)):
        fig.add_annotation(x=xx, y=yy, text=t, showarrow=False)
    fig.update_layout(height=330, xaxis={"visible": False}, yaxis={"visible": False, "scaleanchor": "x"},
                      margin={"t": 10}, title="")
    return fig


def mostrar_fq_sede(territorio: str) -> None:
    st.title(f"🧪 Hidrogeoquímica de {territorio}")
    pl, pi = PROC / "hidrogeoquimica" / "fq_sedes_largo.csv", PROC / "hidrogeoquimica" / "fq_sedes_iones.csv"
    if not pl.exists():
        st.info("Sin resultados fisicoquímicos procesados para esta sede.")
        return
    largo = pd.read_csv(pl)
    largo = largo[largo.sede == territorio]
    if largo.empty:
        st.info("Sin resultados fisicoquímicos procesados para esta sede.")
        return
    iones = pd.read_csv(pi)
    iones = iones[iones.sede == territorio]
    st.caption("Resultados de laboratorio transcritos de los informes de la sede (procesados con el paquete "
               "fqsiams del semillero). Na⁺ y K⁺ no se reportan: para Piper/Stiff se estiman por diferencia de "
               "carga, por lo que el balance iónico no es verificable.")
    piper = iones[iones.nak_estimado_por_diferencia]
    if piper.empty:
        st.warning("Los informes disponibles no traen todos los iones mayores (p. ej. cloruros, sodio): "
                   "no es posible construir Piper ni Stiff. Se muestran los parámetros medidos.")
    else:
        c1, c2 = st.columns(2)
        c1.plotly_chart(_piper(piper), use_container_width=True)
        orden = sorted(piper.index, key=lambda i: ("subterr" not in piper.pozo[i].lower() and "profundo" not in piper.pozo[i].lower(), piper.fecha[i]))
        fila = c2.selectbox("Muestra para Stiff", orden, format_func=lambda i: f"{piper.pozo[i]} · {piper.fecha[i]}")
        c2.plotly_chart(_stiff(piper.loc[fila]), use_container_width=True)
    ancha = largo.pivot_table(index=["parametro", "unidad"], columns=["pozo", "fecha"], values="valor", aggfunc="first")
    st.dataframe(ancha, use_container_width=True)
    dud = largo[largo.bandera.fillna("") == "dudoso_excluido_de_calculos"]
    if not dud.empty:
        st.caption("Valores dudosos excluidos de los cálculos: "
                   + ", ".join(f"{r.parametro} ({r.fecha})" for r in dud.itertuples()))
    st.download_button("Descargar resultados (CSV)", largo.to_csv(index=False).encode("utf-8"),
                       f"fq_{territorio}.csv", "text/csv")


# ----------------------------------------------------------------------------- isótopos
@st.cache_data(show_spinner=False)
def _isotopos() -> pd.DataFrame:
    p = PROC / "isotopos" / "isotopos_ideam_tidy.csv"
    return pd.read_csv(p, parse_dates=["date"], keep_default_na=False, na_values=[""]) if p.exists() else pd.DataFrame()


def _dist_km(lat1, lon1, lat2, lon2):
    r = np.radians
    a = np.sin(r(lat2 - lat1) / 2) ** 2 + np.cos(r(lat1)) * np.cos(r(lat2)) * np.sin(r(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def lmwl(d: pd.DataFrame) -> tuple[float, float, int]:
    """Recta meteórica local δ²H = a·δ¹⁸O + b por mínimos cuadrados (sin valores atípicos)."""
    a, b = np.polyfit(d.d18O, d.d2H, 1)
    return float(a), float(b), len(d)


def mostrar_isotopos(territorio: str) -> None:
    st.title(f"🔬 Isótopos estables en precipitación – {territorio}")
    d = _isotopos()
    if d.empty:
        st.info("Base nacional de isótopos no disponible.")
        return
    est = d.groupby("station")[["lat", "lon", "alt_m"]].first().reset_index()
    lat, lon = COORD_SEDE.get(territorio, (4.6, -74.1))
    est["dist_km"] = _dist_km(lat, lon, est.lat, est.lon).round(1)
    est = est.sort_values("dist_km")
    n = st.slider("Estaciones más cercanas", 1, 5, 3)
    sel = st.multiselect("Estaciones", est.station.tolist(), default=est.station.head(n).tolist(),
                         format_func=lambda s: f"{s} ({est.set_index('station').dist_km[s]:.0f} km)")
    if not sel:
        return
    w = d[d.station.isin(sel) & d.variable.isin(["d18O", "d2H"]) & (d.flag.fillna("") != "outlier")]
    w = w.pivot_table(index=["station", "sample_id", "date"], columns="variable", values="value").dropna().reset_index()
    if w.empty:
        st.info("Las estaciones seleccionadas no tienen pares δ¹⁸O–δ²H.")
        return
    fig = px.scatter(w, x="d18O", y="d2H", color="station", hover_data=["date"], height=480,
                     labels={"d18O": "δ¹⁸O (‰ VSMOW)", "d2H": "δ²H (‰ VSMOW)", "station": "Estación"})
    xs = np.linspace(w.d18O.min() - 1, w.d18O.max() + 1, 2)
    fig.add_trace(go.Scatter(x=xs, y=8 * xs + 10, mode="lines", name="GMWL: δ²H = 8·δ¹⁸O + 10",
                             line={"color": "black", "dash": "dash"}))
    filas = []
    for s, g in w.groupby("station"):
        if len(g) >= 5:
            a, b, k = lmwl(g)
            fig.add_trace(go.Scatter(x=xs, y=a * xs + b, mode="lines", name=f"LMWL {s}: δ²H = {a:.2f}·δ¹⁸O + {b:.2f}"))
            filas.append({"Estación": s, "pendiente": round(a, 2), "intercepto": round(b, 2), "n": k,
                          "periodo": f"{g.date.min():%Y}–{g.date.max():%Y}"})
    campus = PROC / "isotopos" / "isotopos_campus_tidy.csv"
    if territorio == "Bogotá" and campus.exists():
        c = pd.read_csv(campus)
        for tipo, simb in (("Subterranea", "diamond"), ("Lluvia", "x")):
            g = c[c.tipo.str.startswith(tipo[:5], na=False)]
            if not g.empty:
                fig.add_trace(go.Scatter(x=g.d18O, y=g.d2H, mode="markers", name=f"Campus – {tipo.lower()}",
                                         marker={"symbol": simb, "size": 9}, text=g.codigo.astype(str) + " " + g.fecha.astype(str)))
        lm = pd.read_csv(PROC / "isotopos" / "lmwl_bogota.csv")
        comb = lm[lm.serie.str.startswith("Combinada")]
        if not comb.empty:
            a, b = comb.pendiente.iloc[0], comb.intercepto.iloc[0]
            fig.add_trace(go.Scatter(x=xs, y=a * xs + b, mode="lines", line={"width": 3},
                                     name=f"LMWL combinada IDEAM + campus: δ²H = {a:.2f}·δ¹⁸O + {b:.2f}"))
        st.caption("Campus: 94 muestras 2022-11 a 2024-09 (Campus.xlsx). Tres muestras con exceso de deuterio < 0 "
                   "(PR 2, PA01 U-001, M2-PA25 U-003) están marcadas: posible evaporación o error analítico.")
    st.plotly_chart(fig, use_container_width=True)
    if territorio == "Bogotá" and (PROC / "isotopos" / "lmwl_bogota.csv").exists():
        st.dataframe(pd.read_csv(PROC / "isotopos" / "lmwl_bogota.csv"), use_container_width=True, hide_index=True)
    if filas:
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
    st.dataframe(est[est.station.isin(sel)], use_container_width=True, hide_index=True)
    st.caption("Fuente: base nacional de isótopos en precipitación, IDEAM – Subdirección de Hidrología "
               "(IsotoposIDEAM.xlsx). Estación Bogotá: Red Mundial de Isótopos en Precipitación IAEA/WMO (GNIP). "
               "Laboratorios según la base: OIEA, SGC, AGH, Univ. de Copenhague y otros. "
               "Se excluyen los valores marcados como atípicos. La GMWL es la de Craig (1961).")
    st.info("Pendiente: muestras de agua subterránea de los pozos de la sede para compararlas con la LMWL.")


def mostrar_fq_bogota() -> None:
    st.title("🧪 Hidrogeoquímica – Bogotá (campus)")
    p = PROC / "hidrogeoquimica" / "fq_bogota_campus.csv"
    if not p.exists():
        st.info("Sin resultados de laboratorio del campus.")
        return
    d = pd.read_csv(p)
    st.caption("Laboratorio de Ingeniería Ambiental UNAL, muestreos de agosto de 2023 (informes 38464–38498; "
               "agua potable: contrato OGA COT 023-2023). '<x' = bajo el límite (valor vacío, LD_LC = x).")
    sub = d[d.matriz.isin(["SUBTERRANEA", "LLUVIA"])]
    st.subheader("Agua subterránea y lluvia (29-ago-2023)")
    st.warning("PA05 y PA25: turbiedad y sólidos suspendidos extremos (SST 1 156 y 31 720 mg/L; muestras sin purga). "
               "No representan el acuífero y se muestran solo como referencia.")
    t = sub.pivot_table(index=["parametro", "unidad"], columns="id_pozo", values="valor", aggfunc="first")
    st.dataframe(t, use_container_width=True)
    with st.expander("Agua potable del campus (cafeterías y bebederos)"):
        pot = d[d.matriz == "POTABLE"]
        st.dataframe(pot.pivot_table(index=["parametro", "unidad"], columns=["muestra", "punto"], values="valor", aggfunc="first"),
                     use_container_width=True)
    st.download_button("Descargar resultados (CSV)", d.to_csv(index=False).encode("utf-8"), "fq_bogota_campus.csv", "text/csv")
