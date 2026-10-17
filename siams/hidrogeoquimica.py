"""SIAMS: interfaz Streamlit de hidrogeoquímica y taller fisicoquímico (2026).

Utiliza los estilos globales existentes de SIAMS. Datos reales suministrados y
publicables según autorización comunicada por los responsables del proyecto.
"""
from __future__ import annotations

import json
from pathlib import Path
import math
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from . import hidrogeoquimica_nucleo as hq
from .hidrogeoquimica_datos import (
    BASE, ROOT, RECURSOS, NOMBRES, UNIDADES, IONICOS_REQUERIDOS,
    analizar, detalle_irca, leer_carga, normalizar_base, parametros_de,
    preparar_manual,
)

VERDE = "#146C5C"
AZUL = "#4679A3"
NARANJA = "#C48A3D"
GRIS = "#687784"
ROJO = "#C75252"
VIOLETA = "#836BAA"
PALETA = [VERDE, AZUL, NARANJA, VIOLETA, ROJO, "#5B9B8D"]
NIVELES = {"Sin riesgo": VERDE, "Bajo": AZUL, "Medio": NARANJA,
           "Alto": ROJO, "Inviable sanitariamente": "#9C3344", "Sin información": GRIS}


@st.cache_data(show_spinner=False)
def _base_incluida() -> pd.DataFrame:
    return normalizar_base(pd.read_csv(BASE, dtype={"informe": str}))


def _leyenda(fig, titulo="", eje_x="", eje_y="", alto=410):
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=17), x=0),
        xaxis_title=eje_x, yaxis_title=eje_y,
        hovermode="closest", height=alto,
        margin=dict(l=15, r=20, t=68, b=45),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2, x=0),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(125,130,130,0.13)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(125,130,130,0.13)", zeroline=False)
    return fig


def _descarga(data: pd.DataFrame, nombre: str, etiqueta: str, key: str):
    st.download_button(etiqueta, data=data.to_csv(index=False).encode("utf-8-sig"),
                       file_name=nombre, mime="text/csv", key=key)


def _ingreso_manual(territorio):
    with st.form("siams_fq_form_manual"):
        a,b,c=st.columns(3)
        sede=a.text_input("Sede", value=territorio)
        punto=b.text_input("Código del punto", value="POZO-001")
        informe=c.text_input("Identificador de muestra", value="MANUAL-001")
        fecha=st.date_input("Fecha de muestreo", value=None)
        st.caption("Una fila por parámetro. Los valores son opcionales; conserva la unidad de la guía. "
                   "Para resultados por debajo del LD, elige el signo '<' e ingresa el límite de detección como valor.")
        codigos=list(dict.fromkeys([row[0] for row in hq.IRCA] + list(IONICOS_REQUERIDOS) +
                                  ["conductividad", "solidos_totales", "sst"]))
        manual=pd.DataFrame({"parametro":codigos, "nombre": [NOMBRES[x] for x in codigos],
                             "unidad":[UNIDADES[x] for x in codigos],
                             "signo":[""]*len(codigos), "valor":[float("nan")]*len(codigos)})
        editado=st.data_editor(manual, use_container_width=True, hide_index=True,
                               key="siams_fq_tabla_manual", num_rows="fixed",
                               disabled=["parametro", "nombre", "unidad"],
                               column_config={
                                   "signo": st.column_config.SelectboxColumn("Signo", options=["", "<"]),
                                   "valor": st.column_config.NumberColumn("Valor medido o LD", min_value=0.0),
                               })
        enviar=st.form_submit_button("Analizar esta muestra", type="primary")
    if enviar:
        if fecha is None:
            st.error("Selecciona la fecha de muestreo")
        else:
            try:
                st.session_state["siams_fq_manual"] = preparar_manual(sede,punto,informe,str(fecha),editado)
                st.success("Muestra cargada. Revisa sus cálculos y controles de calidad abajo.")
            except ValueError as error:
                st.error(str(error))
    return st.session_state.get("siams_fq_manual")


def _irca_figura(resumen):
    q=resumen.dropna(subset=["irca"]).copy()
    q=q.sort_values("irca")
    fig=go.Figure()
    fig.add_trace(go.Bar(y=q["informe"].astype(str), x=q["irca"], orientation="h",
                         marker_color=[NIVELES.get(x, GRIS) for x in q["nivel"]],
                         customdata=q[["grupo_punto", "irca_max"]].to_numpy(),
                         name="IRCA mínimo", hovertemplate="Informe %{y}<br>IRCA base %{x:.1f}%<br>Grupo %{customdata[0]}<br>Máx. %{customdata[1]:.1f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=q["irca_max"], y=q["informe"].astype(str), mode="markers",
                             marker=dict(symbol="diamond-open", color=GRIS, size=11, line=dict(width=2)),
                             name="Límite superior (LD no concluyentes)", hovertemplate="Muestra %{y}: máximo posible %{x:.1f}%<extra></extra>"))
    _leyenda(fig, "IRCA por muestra · escenario base e incertidumbre", "IRCA (%)", "Informe", max(365,len(q)*32+200))
    fig.update_xaxes(range=[0,105])
    return fig


def _tabla_irca(muestra, alternativo):
    p = parametros_de(muestra, nitratos_en_no3=alternativo)
    if not set(p).intersection({k for k, *_ in hq.IRCA}):
        return pd.DataFrame(columns=["caracteristica", "puntaje", "estado", "resultado", "límite", "unidad"]), {
            "irca": float("nan"), "irca_max": float("nan"), "nivel": "No calculable"
        }
    t,res = detalle_irca(muestra,nitratos_en_no3=alternativo)
    tabla=t[["caracteristica","puntaje","estado"]].copy()
    tabla["resultado"] = t.get("valor_limite_und", pd.Series(dtype=float))
    tabla["límite"] = t.get("maximo", pd.Series(dtype=float))
    tabla["unidad"] = t.get("unidad", pd.Series(dtype=object))
    return tabla,res


def _iones(df, ids, alternativo, regla_ld):
    filas=[]
    for id_muestra in ids:
        sub=df[df.id_muestra == id_muestra]
        if sub.empty: continue
        p=parametros_de(sub,nitratos_en_no3=alternativo)
        if not set(IONICOS_REQUERIDOS).issubset(p): continue
        try:
            b=hq.balance(p,regla_ld); m=b["meq"]
            v={"id_muestra":id_muestra, "informe":str(sub.iloc[0].informe),
               "grupo":str(sub.iloc[0].grupo_punto),
               "Ca":m["Ca"], "Mg":m["Mg"], "NaK":b["nak_dif_meq"],
               "HCO3":m["HCO3"] + m["CO3"], "Cl":m["Cl"] + m["NO3"] + m["F"],
               "SO4":m["SO4"], "error":b["error_pct"]}
            if all(math.isfinite(float(x)) for x in (v["Ca"],v["Mg"],v["NaK"],v["HCO3"],v["Cl"],v["SO4"])):
                filas.append(v)
        except (ValueError,TypeError,ZeroDivisionError,OverflowError):
            continue
    return pd.DataFrame(filas)


def _piper(iones):
    H=math.sqrt(3)/2
    off=1.2
    fig=go.Figure()
    vertices=[[(0,0),(1,0),(.5,H),(0,0)],[(off,0),(off+1,0),(off+.5,H),(off,0)],
              [((1+off)/2,H*(off-1)),(off/2,H*off),((1+off)/2,H*(off+1)),(1+off/2,H*off),((1+off)/2,H*(off-1))]]
    for poly in vertices:
        fig.add_trace(go.Scatter(x=[x for x,y in poly],y=[y for x,y in poly],mode="lines",
                                 line=dict(color=GRIS,width=1.4),showlegend=False,hoverinfo="skip"))
    for i, r in enumerate(iones.itertuples()):
        sc=r.Ca+r.Mg+r.NaK; sa=r.HCO3+r.Cl+r.SO4
        if sc<=0 or sa<=0:continue
        pc=(r.NaK/sc+r.Mg/sc/2,r.Mg/sc*H)
        pa=(off+r.Cl/sa+r.SO4/sa/2,r.SO4/sa*H)
        t2=(pa[0]-pc[0])-(pa[1]-pc[1])/(2*H)
        t1=t2+(pa[1]-pc[1])/H
        pdia=(pc[0]+.5*t1,pc[1]+H*t1)
        c=PALETA[i%len(PALETA)]
        fig.add_trace(go.Scatter(x=[pc[0],pa[0],pdia[0]],y=[pc[1],pa[1],pdia[1]],
                                 mode="markers",marker=dict(size=10,color=c,symbol=["circle","square","diamond"]),
                                 name=r.informe,customdata=[r.grupo]*3,
                                 hovertemplate="Informe "+r.informe+"<br>Grupo %{customdata}<extra></extra>"))
    for x,y,t in [(0,-.09,"Ca²⁺"),(1,-.09,"Na⁺+K⁺*"),(.5,H+.05,"Mg²⁺"),
                  (off,-.09,"HCO₃⁻+CO₃²⁻"),(off+1,-.09,"Cl⁻+NO₃⁻+F⁻"),(off+.5,H+.05,"SO₄²⁻")]:
        fig.add_annotation(x=x,y=y,text=t,showarrow=False,font=dict(size=11))
    _leyenda(fig,"Piper · composición iónica (Na⁺+K⁺ estimados*)","","",520)
    fig.update_xaxes(visible=False,range=[-.2,off+1.2],scaleanchor="y",scaleratio=1)
    fig.update_yaxes(visible=False,range=[-.2,2*H+.35])
    return fig


def _stiff(r):
    fig=go.Figure()
    # Stiff: cationes a la izquierda, aniones a la derecha en meq/L.
    xl=[-r.NaK,-r.Ca,-r.Mg]; xr=[r.Cl,r.HCO3,r.SO4]; ys=[2,1,0]
    fig.add_trace(go.Scatter(x=xl+xr[::-1]+[xl[0]],y=ys+ys[::-1]+[ys[0]],
                             fill="toself",mode="lines+markers",line=dict(color=VERDE,width=2),
                             fillcolor="rgba(20,108,92,0.19)",showlegend=False,
                             hovertemplate="%{x:.3f} meq/L<extra></extra>"))
    fig.add_vline(x=0,line_dash="dash",line_color=GRIS)
    _leyenda(fig,"Stiff · informe "+r.informe,"Cationes ← meq/L → Aniones","",400)
    lim=max([abs(x) for x in xl+xr])*1.25
    fig.update_xaxes(range=[-lim,lim]); fig.update_yaxes(tickvals=[2,1,0],ticktext=["Na+K* / Cl+NO3+F","Ca / HCO3+CO3","Mg / SO4"],range=[-.3,2.3])
    return fig


def _gibbs(df, iones, alternativo):
    fig=make_subplots(rows=1,cols=2,subplot_titles=["Catiónico: (Na+K*)/(Na+K*+Ca)","Aniónico: Cl/(Cl+HCO₃)"])
    env=ROOT / "data/processed/hidrogeoquimica" / "gibbs_envelope.json"
    if not env.is_file():
        env=ROOT / "Datos_Hidrogeoquimica" / "gibbs_envelope.json"
    if env.is_file():
        envolvente=json.loads(env.read_text(encoding="utf-8"))
        for col,clave in [(1,"cation"),(2,"anion")]:
            for segmento in envolvente.get(clave,[]):
                fig.add_trace(go.Scatter(x=[p[0] for p in segmento],y=[p[1] for p in segmento],
                                         mode="lines",line=dict(color=GRIS,dash="dot",width=1),
                                         showlegend=False,hoverinfo="skip"),row=1,col=col)
    cuentas=0
    for j, r in enumerate(iones.itertuples()):
        m=df[df.id_muestra == r.id_muestra]
        p=parametros_de(m,nitratos_en_no3=alternativo)
        if not {"solidos_totales","sst"}.issubset(p):continue
        solidos=hq.valor_calculo(*p["solidos_totales"])-hq.valor_calculo(*p["sst"])
        if solidos<=0: continue
        try:
            ion=p["cloruros"][1]/hq.peq("Cl")
            alc=r.HCO3
            cat=r.NaK/(r.NaK+r.Ca/2) if r.NaK+r.Ca/2>0 else float("nan")
            an=ion/(ion+alc) if ion+alc>0 else float("nan")
            for col,x in [(1,cat),(2,an)]:
                if math.isfinite(x):
                    fig.add_trace(go.Scatter(x=[x],y=[solidos],mode="markers",name=r.informe,
                                             marker=dict(color=PALETA[j%len(PALETA)],size=10),
                                             showlegend=(col==1),hovertemplate=r.informe+"<br>SDT≈%{y:.2f} mg/L<extra></extra>"),row=1,col=col)
                    cuentas+=1
        except (TypeError,ValueError,ZeroDivisionError): continue
    _leyenda(fig,"Gibbs · clasificación orientativa (SDT≈ST−SST)","Razón molar (aprox.)","SDT (mg/L)",450)
    fig.update_xaxes(range=[0,1]);fig.update_yaxes(type="log",range=[0,5])
    return fig, cuentas


def _series(df):
    a,b=st.columns([2,1])
    disponibles=sorted(df["parametro"].unique())
    elegir=a.selectbox("Parámetro",disponibles,format_func=lambda k: NOMBRES.get(k,k),key="siams_fq_serie_parametro")
    fig=go.Figure()
    dato=df[df.parametro==elegir].copy()
    dato["fecha_grafica"]=pd.to_datetime(dato["fecha_uso"].replace("",np.nan),errors="coerce")
    dato=dato.dropna(subset=["fecha_grafica"])
    xaxis="Fecha"
    for j,(g,m) in enumerate(dato.groupby("grupo_punto",sort=True)):
        m=m.sort_values("fecha_grafica")
        fig.add_trace(go.Scatter(x=m.fecha_grafica,y=m.valor,mode="lines+markers",
                                 name=str(g),marker=dict(size=9,color=PALETA[j%len(PALETA)],
                                                        symbol=["circle-open" if s=="<" else "circle" for s in m.signo]),
                                 customdata=m[["informe","signo"]].to_numpy(),
                                 hovertemplate="%{x|%Y-%m-%d}<br>Informe %{customdata[0]}<br>Valor %{y:g} (%{customdata[1]} LD si aplica)<extra></extra>"))
    _leyenda(fig,NOMBRES.get(elegir,elegir),xaxis,UNIDADES.get(elegir,"Unidad del informe"))
    st.plotly_chart(fig,use_container_width=True)
    if not dato.empty:
        validas = dato.loc[dato["signo"].ne("<") & dato["valor"].notna()].copy()
        puntos_validos = int(validas["grupo_punto"].nunique())
        if validas.empty:
            st.markdown(
                "**Lectura:** los valores disponibles corresponden a límites de "
                "detección; no es posible indicar un mínimo o máximo medido real "
                "para este parámetro."
            )
        elif len(validas) == 1:
            st.markdown(
                f"**Lectura:** existe una medición cuantificada de "
                f"**{float(validas.iloc[0]['valor']):.2f} {UNIDADES.get(elegir, '')}**. "
                "Una sola medición no permite hablar de evolución temporal."
            )
        else:
            st.markdown(
                f"**Lectura de las observaciones cuantificadas:** en "
                f"**{len(validas)} resultados** de **{puntos_validos} puntos**, "
                f"los valores fueron de **{float(validas['valor'].min()):.2f}** "
                f"a **{float(validas['valor'].max()):.2f}** "
                f"{UNIDADES.get(elegir, '')}. Es un rango de las muestras "
                "disponibles, no una tendencia estimada. Si se comparan puntos "
                "diferentes, las diferencias también pueden deberse al lugar "
                "de muestreo."
            )
    if dato.empty: st.info("No hay fechas válidas para este parámetro.")
    elif dato.fecha_grafica.nunique()<4: st.caption("Hay pocos eventos de muestreo. Estas líneas describen cambios observados, no una tendencia estadística.")
    st.caption("Marcadores huecos: resultado '<LD'. Se muestra el límite de detección, no una concentración cuantificada.")


def mostrar_hidrogeoquimica(territorio: str = "Leticia") -> None:
    st.title(f"🧪 Hidrogeoquímica · {territorio}")
    st.caption("SIAMS · Datos de laboratorio, cálculos reproducibles y diagramas interactivos")
    st.markdown(
        "**¿Para qué sirve este apartado?** Permite conocer qué características "
        "tiene el agua analizada en el laboratorio y explorar posibles diferencias "
        "entre muestras. Por ejemplo, puedes revisar su acidez, sales, turbiedad "
        "y los parámetros disponibles para una evaluación de calidad."
    )
    st.markdown(
        '<div class="soft-box"><strong>Empieza en tres pasos:</strong> '
        '<strong>1.</strong> Usa la base de Leticia, sube un Excel/CSV o ingresa una muestra. '
        '<strong>2.</strong> Revisa el panorama general y elige una muestra en la calculadora. '
        '<strong>3.</strong> Explora los diagramas y las comparaciones, leyendo las notas '
        'de interpretación debajo de cada gráfica.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Diccionario rápido: palabras que encontrarás aquí", expanded=False):
        st.markdown(
            "**pH:** indica si el agua es ácida, neutra o básica. Un valor bajo "
            "indica mayor acidez; no basta por sí solo para calificar su calidad.\n\n"
            "**Conductividad eléctrica (CE):** orienta sobre la presencia de iones "
            "disueltos. No permite identificar por sí sola cuáles sustancias hay.\n\n"
            "**Alcalinidad:** capacidad del agua para neutralizar ácidos; "
            "se relaciona con bicarbonatos y carbonatos.\n\n"
            "**Dureza:** asociada principalmente al calcio y magnesio.\n\n"
            "**IRCA:** índice de riesgo de la calidad del agua; en esta herramienta "
            "es un cálculo académico por muestra y parámetros disponibles.\n\n"
            "**<LD:** el laboratorio informó que la concentración está por debajo "
            "de su límite de detección: no significa necesariamente cero."
        )
    st.info("El IRCA de esta sección se presenta como ejercicio de evaluación sobre muestras individuales de agua cruda: "
            "no constituye una declaración de potabilidad ni una evaluación oficial de un sistema de suministro.")
    fuentes=["Base de Leticia (informes del taller)","Cargar CSV / Excel", "Ingreso manual"]
    preferida=0 if territorio=="Leticia" else 1
    fuente=st.radio("Fuente de información",fuentes,index=preferida,horizontal=True,key="siams_fq_fuente")
    df=None
    if fuente==fuentes[0]:
        if not BASE.is_file():
            st.error("No encuentro data/processed/hidrogeoquimica/siams_fq_largo.csv")
        else:
            try: df=_base_incluida()
            except (ValueError,KeyError,FileNotFoundError,pd.errors.ParserError) as ex: st.error(str(ex))
        if territorio!="Leticia": st.warning("El conjunto incluido corresponde a Leticia, no a la sede seleccionada. Carga archivos de esta sede para obtener sus resultados.")
    elif fuente==fuentes[1]:
        archivos=st.file_uploader("Sube informes consolidados (formato largo)",type=["csv","xlsx"],
                                  accept_multiple_files=True,key="siams_fq_subir")
        st.caption("Columnas mínimas: informe, parametro, valor. Recomendadas: sede, punto, grupo_punto, fecha_uso, signo, unidad, bandera. "
                   "Para Excel seleccionamos automáticamente la hoja datos_largo de la plantilla.")
        if archivos:
            try:
                partes=[]
                for j,archivo in enumerate(archivos):
                    contenido=archivo.getvalue()
                    if len(contenido)>20*1024*1024: raise ValueError("Archivo mayor que 20 MB")
                    tabla=leer_carga(archivo.name,contenido)
                    # prefijar informe si se cargan varios archivos independientes;
                    # preservar grupo para series y código original para referencia.
                    if len(archivos)>1:
                        tabla=tabla.copy()
                        tabla["informe"]=tabla["informe"].astype(str).map(lambda x:f"{j+1}:{x}")
                    partes.append(tabla)
                df=normalizar_base(pd.concat(partes,ignore_index=True),nombre_fuente="Archivos suministrados por el usuario")
                st.success(f"Cargadas {len(archivos)} fuentes, {len(df)} resultados.")
            except (ValueError,KeyError,ImportError,OSError,pd.errors.ParserError) as ex:
                st.error("No se pudieron validar los archivos: "+str(ex))
    else:
        df=_ingreso_manual(territorio)

    if df is None or df.empty:
        st.info("Selecciona una base, carga un CSV/Excel o ingresa una muestra para comenzar.")
        with st.expander("Formato esperado para nuevas sedes"):
            st.code("informe,sede,punto,grupo_punto,fecha_uso,parametro,valor,signo,unidad\nM-001,Arauca,PZ-01,PZ-01,2026-06-01,ph,6.8,,Unidades\nM-001,Arauca,PZ-01,PZ-01,2026-06-01,alcalinidad,25,,mg/L CaCO3",language="text")
        return
    st.caption("Fuente: " + ("Laboratorio de Ingeniería Ambiental (UNAL), compilación académica 2026" if fuente==fuentes[0] else fuente))
    c1,c2=st.columns([1,1])
    alternativo=c1.toggle("Ensayar nitrato expresado como NO₃⁻ en vez de N–NO₃",value=False,key="siams_fq_nitrato_alternativo",help="Escenario exploratorio ante una posible ambigüedad del rótulo del informe; no cambia los valores originales.")
    regla_ld=c2.selectbox("Regla para <LD (solo cálculos iónicos)",["LD/2","0","LD"],key="siams_fq_ld_regla")
    if alternativo: st.warning("Escenario alternativo: se interpretan temporalmente los valores del parámetro nitratos_n como mg/L NO₃⁻. No modifica la base original.")
    resultado=analizar(df,nitratos_en_no3=alternativo,regla_ld=regla_ld)
    m1,m2,m3,m4=st.columns(4)
    m1.metric("Resultados",f"{len(df):,}".replace(",","."))
    m2.metric("Muestras",int(df.id_muestra.nunique()))
    m3.metric("Puntos agrupados",int(df.groupby(["sede","grupo_punto"]).ngroups))
    m4.metric("IRCA calculado",int(resultado.irca.notna().sum()))
    st.caption(
        "**Resultados** = determinaciones individuales (por ejemplo, pH o calcio); "
        "**muestras** = conjuntos de resultados de una toma; **puntos** = lugares "
        "agrupados de monitoreo; **IRCA calculado** = muestras con puntaje disponible "
        "para la evaluación realizada aquí."
    )
    if df.bandera.fillna("").astype(str).str.strip().ne("").any():
        st.warning("La base trae observaciones metodológicas. Revisa fechas, tipo de muestra, identificación de puntos y unidades antes de interpretar conclusiones.")
    tabs=st.tabs(["📊 Panorama", "🧪 Calculadora y muestra", "📐 Diagramas", "📈 Evolución", "📁 Datos y método"])
    with tabs[0]:
        st.subheader("Indicadores por muestra")
        st.markdown(
            "**¿Qué estoy viendo?** Cada barra representa el **IRCA base** calculado "
            "con los parámetros evaluados en una muestra. Cuanto mayor el porcentaje, "
            "mayor es el puntaje de características que no cumplieron los límites "
            "considerados. El **rombo** marca un límite superior posible cuando "
            "hay resultados bajo el límite de detección que no permiten decidir. "
            "No es una medición oficial de potabilidad del agua cruda."
        )
        if resultado.irca.notna().any():
            st.plotly_chart(_irca_figura(resultado),use_container_width=True)
        else: st.info("No hay parámetros suficientes para calcular IRCA.")
        con_irca = resultado.dropna(subset=["irca"])
        if not con_irca.empty:
            menor = con_irca.loc[con_irca["irca"].idxmin()]
            mayor = con_irca.loc[con_irca["irca"].idxmax()]
            st.markdown(
                f"**Lectura de las muestras seleccionadas:** el IRCA base calculado va "
                f"de **{menor['irca']:.1f}%** (informe **{menor['informe']}**) "
                f"a **{mayor['irca']:.1f}%** (informe **{mayor['informe']}**). "
                "Son valores de las muestras disponibles, no de toda la sede ni de "
                "una red de abastecimiento. Si los rombos están lejos de sus barras, "
                "la incertidumbre por resultados no concluyentes es mayor."
            )
        st.dataframe(resultado[["informe","sede","grupo_punto","fecha_uso","irca","irca_max","nivel","error_balance_pct"]],hide_index=True,use_container_width=True)
        ce=resultado.dropna(subset=["CE_medida","CE_estimada"])
        if not ce.empty:
            st.markdown(
                "**¿Qué representa la conductividad?** El eje horizontal es la "
                "conductividad medida en el laboratorio y el vertical es un cálculo "
                "aproximado a partir de los iones. Puntos próximos a la diagonal "
                "indican mayor coincidencia entre ambas aproximaciones; puntos "
                "alejados invitan a revisar unidades, iones faltantes y supuestos."
            )
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=ce.CE_medida,y=ce.CE_estimada,mode="markers+text",
                                     text=ce.informe.astype(str),textposition="top center",marker=dict(size=10,color=VERDE),name="Muestras"))
            vmax=max(float(ce.CE_medida.max()),float(ce.CE_estimada.max()),1)
            fig.add_trace(go.Scatter(x=[0,vmax],y=[0,vmax],mode="lines",line=dict(color=GRIS,dash="dash"),name="Referencia 1:1"))
            _leyenda(fig,"Control exploratorio: conductividad estimada y medida","CE medida (µS/cm)","CE estimada (µS/cm)")
            st.plotly_chart(fig,use_container_width=True)
            st.caption("La CE estimada por conductividades iónicas límite es una comprobación aproximada, no un sustituto de la medición; Na⁺+K⁺ se infieren cuando faltan.")
    with tabs[1]:
        st.markdown(
            "**Vamos muestra por muestra.** Aquí puedes identificar qué "
            "parámetros cumplen los criterios usados, cuáles no y cuáles quedaron "
            "sin conclusión. Después se estiman algunos componentes químicos "
            "y se revisa si el conjunto de iones es coherente."
        )
        ids=resultado.id_muestra.tolist()
        elegido=st.selectbox("Muestra que quieres analizar",ids,format_func=lambda v:v,key="siams_fq_una_muestra")
        muestra=df[df.id_muestra==elegido]
        seleccion=resultado[resultado.id_muestra==elegido].iloc[0]
        st.markdown(f"**Informe:** {seleccion['informe']} · **Punto:** {seleccion['punto']} · **Fecha:** {seleccion['fecha_uso']}")
        tabla,ir=_tabla_irca(muestra,alternativo)
        a,b,c=st.columns(3)
        a.metric("IRCA base",f"{ir['irca']:.1f}%" if math.isfinite(ir['irca']) else "No calculable")
        b.metric("IRCA superior",f"{ir['irca_max']:.1f}%" if math.isfinite(ir['irca_max']) else "No calculable")
        c.metric("Clasificación base",ir["nivel"])
        st.caption("Cálculo: IRCA = 100 × (Σ puntajes de características no conformes) / (Σ puntajes analizados). "
                   "El límite superior añade las características no concluyentes por <LD.")
        if math.isfinite(ir["irca"]):
            st.markdown(
                f"**Interpretación de esta muestra:** el **IRCA base de {ir['irca']:.1f}%** "
                f"se clasifica como **{ir['nivel']}** según los parámetros "
                "evaluados en este ejercicio. "
                + ("El límite superior difiere del base porque existen resultados "
                   "que no permiten decidir completamente su cumplimiento. "
                   if math.isfinite(ir['irca_max']) and ir['irca_max'] > ir['irca'] else "")
                + "La clasificación no reemplaza un análisis completo de potabilidad "
                  "ni puede extenderse sin más a toda la población."
            )
        st.markdown(
            "**Cómo leer la tabla:** 'cumple' = está dentro del límite usado; "
            "'no cumple' = lo supera o queda fuera de él; 'no concluyente' = "
            "el resultado no permite decidir; 'no analizado' = no hay medición "
            "de ese parámetro en el informe."
        )
        st.dataframe(tabla,use_container_width=True,hide_index=True)
        st.markdown("**Alcalinidad y balance iónico**")
        st.markdown(
            "Los **bicarbonatos y carbonatos** influyen en el equilibrio químico "
            "del agua; aquí se estiman usando pH y alcalinidad, no se reportan "
            "como mediciones directas. El **balance iónico** contrasta cargas "
            "positivas y negativas: grandes diferencias pueden indicar iones "
            "faltantes, unidades inconsistentes u otras limitaciones de la muestra."
        )
        if pd.notna(seleccion.hco3_mg):
            st.write(f"Bicarbonato estimado por especiación: **{seleccion.hco3_mg:.2f} mg/L HCO₃⁻**; "
                     f"carbonato: **{seleccion.co3_mg:.4f} mg/L CO₃²⁻**.")
        else: st.info("Para especiación se requiere pH y alcalinidad.")
        if pd.notna(seleccion.error_balance_pct):
            st.write(f"Error de balance iónico, antes de añadir Na⁺+K⁺ estimados: **{seleccion.error_balance_pct:.1f}%**; "
                     f"Na⁺+K⁺ inferidos por diferencia: **{seleccion.nak_inferido_meq:.3f} meq/L**.")
            if abs(seleccion.error_balance_pct)>10:
                st.warning("Desequilibrio iónico elevado; no interpretes Na⁺+K⁺ inferidos como un análisis de laboratorio.")
        else: st.info("El balance requiere pH, alcalinidad, durezas cálcica y magnésica, Cl⁻, SO₄²⁻, nitratos y fluoruros.")
        st.caption("Na⁺ y K⁺ no se midieron en estos informes; el balance con Na⁺+K⁺ inferidos por diferencia no sirve como validación independiente.")
        st.dataframe(muestra[["parametro","valor","signo","unidad","metodo","bandera"]],hide_index=True,use_container_width=True)
    with tabs[2]:
        st.subheader("Diagramas hidrogeoquímicos")
        st.markdown(
            "**¿Para qué sirven estos dibujos?** Son maneras de resumir qué "
            "iones predominan en el agua. Ayudan a reconocer si dos muestras "
            "tienen composiciones parecidas, pero no permiten afirmar por sí "
            "solos que el agua sea potable o que tenga un origen geológico concreto."
        )
        st.caption("Se utilizan equivalentes iónicos. La concentración Na⁺+K⁺* se infiere por diferencia, y Cl incluye NO₃⁻ y F⁻ en el agrupamiento de Piper/Stiff. "
                   "Los diagramas son exploratorios, no sustituyen mediciones completas de iones mayoritarios.")
        todos=resultado.id_muestra.tolist()
        elegidos=st.multiselect("Muestras incluidas",todos,default=todos[:min(len(todos),9)],key="siams_fq_elegir_diagramas")
        iones=_iones(df,elegidos,alternativo,regla_ld)
        if iones.empty:
            st.warning("No hay muestras con el conjunto iónico requerido para generar diagramas.")
        else:
            st.markdown(
                "**Piper · cómo leerlo:** cada muestra aparece como puntos en "
                "triángulos (cationes a la izquierda y aniones a la derecha) "
                "y en un rombo central. Puntos cercanos pueden representar "
                "composiciones iónicas parecidas. **Aquí falta Na⁺/K⁺ medido**, "
                "por lo que la comparación es orientativa."
            )
            st.plotly_chart(_piper(iones),use_container_width=True)
            st.markdown(
                "**Stiff · cómo leerlo:** la mitad izquierda resume los iones "
                "positivos y la derecha los negativos, expresados en meq/L. "
                "Una forma más ancha significa mayor cantidad *equivalente* "
                "del grupo representado. Su contorno ayuda a comparar muestras."
            )
            inf=st.selectbox("Muestra para el diagrama Stiff",iones.id_muestra.tolist(),key="siams_fq_stiff")
            st.plotly_chart(_stiff(iones.loc[iones.id_muestra==inf].iloc[0]),use_container_width=True)
            st.markdown(
                "**Gibbs · cómo leerlo:** compara proporciones de algunos iones "
                "con una estimación de sólidos disueltos. Se usa para explorar "
                "patrones compatibles con distintos controles hidroquímicos, "
                "no para demostrar una causa. En estos datos el contenido "
                "disuelto es aproximado (sólidos totales menos suspendidos)."
            )
            g,cuenta=_gibbs(df,iones,alternativo)
            if cuenta: st.plotly_chart(g,use_container_width=True)
            else: st.info("No hay sólidos totales y suspendidos suficientes para Gibbs.")
    with tabs[3]:
        st.markdown(
            "**¿Ha cambiado el agua con el tiempo?** Selecciona un parámetro "
            "para comparar sus mediciones entre campañas. Cada color es un "
            "punto de monitoreo. Las líneas unen observaciones disponibles, "
            "pero con pocas fechas no representan necesariamente una tendencia "
            "estadística ni un cambio permanente."
        )
        _series(df)
    with tabs[4]:
        st.subheader("Base consolidada y trazabilidad")
        st.markdown(
            "**¿Por qué es importante guardar los datos?** Porque una gráfica "
            "solo muestra el resultado final. Esta tabla permite revisar la "
            "fecha, la unidad, el método de laboratorio y las observaciones "
            "de cada valor, para que el análisis pueda verificarse y repetirse. "
            "También puedes descargar una guía para practicar con nuevos informes."
        )
        a,b=st.columns(2)
        with a: _descarga(df,"SIAMS_fisicoquimica_datos_largos.csv","⬇️ Descargar datos filtrados","siams_fq_descarga_datos")
        with b: _descarga(resultado,"SIAMS_fisicoquimica_resumen.csv","⬇️ Descargar resumen calculado","siams_fq_descarga_resumen")
        st.dataframe(df,use_container_width=True,hide_index=True)
        if (RECURSOS/"Guia_taller_informes_fisicoquimicos_SIAMS.pdf").is_file():
            st.download_button("📘 Descargar guía del taller",data=(RECURSOS/"Guia_taller_informes_fisicoquimicos_SIAMS.pdf").read_bytes(),
                               file_name="Guia_taller_informes_fisicoquimicos_SIAMS.pdf",mime="application/pdf",key="siams_fq_guia_pdf")
        if (RECURSOS/"SIAMS_fisicoquimicos_plantilla.xlsx").is_file():
            st.download_button("📗 Descargar plantilla Excel original",data=(RECURSOS/"SIAMS_fisicoquimicos_plantilla.xlsx").read_bytes(),
                               file_name="SIAMS_fisicoquimicos_plantilla.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",key="siams_fq_plantilla_xlsx")
        st.markdown("**Metodología y alcance**")
        st.markdown("- Cálculos adaptados de `05_construccion/hq.py` de la guía SIAMS de octubre de 2026.\n"
                    "- IRCA: Resolución 2115 de 2007, para los parámetros disponibles.\n"
                    "- Alcalinidad → HCO₃⁻ y CO₃²⁻: especiación por pH (25 °C); inferencia aproximada.\n"
                    "- `<LD`: evaluado como intervalo para IRCA; regla configurable en balance iónico.\n"
                    "- Nitratos: supuesto por defecto mg/L N–NO₃; hay un escenario alternativo visible.\n"
                    "- Tres campañas de Leticia 2026: no bastan para estimar tendencias robustas.\n"
                    "- Los CSV cargados se procesan durante la sesión; no se escriben automáticamente en GitHub.")
        if resultado.banderas.astype(str).str.strip().ne("").any():
            with st.expander("Observaciones de los datos"):
                st.dataframe(resultado[["informe","grupo_punto","banderas"]],hide_index=True,use_container_width=True)
