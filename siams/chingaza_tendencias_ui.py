"""Presentación de resultados estadísticos; no modifica los cálculos."""

import math

import pandas as pd

import streamlit as st





def _fmt(x, cifras=5):

    try:

        x = float(x)

        if not math.isfinite(x):

            return "No disponible"

    except (TypeError, ValueError):

        return "No disponible"

    return f"{x:.{cifras}g}"





def _tabla(result, campos):

    return pd.DataFrame([{"Parámetro": nombre, "Resultado": _fmt(result.get(k))}

                         for k, nombre in campos])





def mostrar_resultados_tendencia(mk, sen, hr, anios, unidad_anual):

    st.subheader("Mann–Kendall original")

    alpha = mk.get("alpha", 0.05)

    confianza = 100 * (1 - alpha)

    st.markdown("**" + mk["tendencia"] + "**")

    st.caption(f"Prueba bilateral · nivel de confianza nominal: {confianza:g} %")

    c1, c2 = st.columns(2)

    c1.metric("Años válidos", str(mk["n"]))

    c2.metric("Valor p", _fmt(mk["p"]))

    c3, c4 = st.columns(2)

    c3.metric("Pendiente de Sen", _fmt(sen.get("pendiente")))

    c3.caption(f"Unidad: ({unidad_anual}) por año")

    c4.metric("Tau de Kendall", _fmt(mk["tau"]))

    if mk["significativa"]:

        direccion = "decreciente" if mk["tau"] < 0 else "creciente"

        st.write(f"Se identifica una tendencia {direccion} estadísticamente significativa con la prueba original (p < {alpha:g}).")

    else:

        st.write(f"La prueba original no encuentra evidencia suficiente de una tendencia significativa con α = {alpha:g}. Esto no demuestra ausencia de cambio.")

    yrs = sorted(set(int(a) for a in anios))

    if yrs:

        faltan = sorted(set(range(yrs[0], yrs[-1] + 1)) - set(yrs))

        st.caption(f"Periodo de años completos: {yrs[0]}–{yrs[-1]} · {len(faltan)} años faltantes dentro del intervalo.")

    else:

        faltan = []

    st.divider()

    st.subheader("Mann–Kendall modificado · Hamed–Rao")

    if hr.get("disponible", False):

        st.markdown("**" + hr["tendencia"] + "**")

        c1, c2 = st.columns(2)

        c1.metric("Valor p corregido", _fmt(hr.get("p")))

        c2.metric("Factor de varianza", _fmt(hr.get("factor_varianza")))

        st.caption("Corrección por autocorrelación de rangos según la implementación de SIAMS.")

    else:

        st.info("No evaluable: " + (hr.get("motivo") or "No se cumplen las condiciones del método."))

        st.caption("La prueba original permanece disponible; no se ha confirmado su resultado mediante Hamed–Rao.")

    with st.expander("Detalles estadísticos"):

        st.table(_tabla(mk, [("S", "Estadístico S"), ("var_S", "Varianza de S"), ("Z", "Estadístico Z"), ("alpha", "Nivel de significancia α")]))

        st.caption("Años faltantes: " + (", ".join(map(str, faltan)) if faltan else "ninguno dentro del periodo evaluado"))

        if hr.get("disponible", False):

            st.table(_tabla(hr, [("Z", "Z corregido"), ("var_S", "Varianza corregida"), ("lag1", "Autocorrelación de rezago 1")]))

            lags = hr.get("lags_significativos", [])

            st.caption("Rezagos significativos: " + (", ".join(map(str, lags)) if len(lags) else "ninguno"))

    st.caption("Interpretación exploratoria. Revisar homogeneidad, cobertura temporal y autocorrelación antes de atribuir causas a una tendencia.")

# SIAMS_CHINGAZA_ANALISIS_CLIMATICO

def _serie_mensual_valida(d):
    import numpy as np
    f = pd.to_datetime(d['fecha'], errors='raise')
    if f.isna().any() or f.duplicated().any() or not f.dt.day.eq(1).all():
        raise ValueError('Se requiere una serie mensual única por fecha.')
    v = pd.to_numeric(d['valor'], errors='coerce')
    return pd.Series(v.where(np.isfinite(v)).to_numpy(), index=pd.DatetimeIndex(f), name='valor').sort_index()


def _intervalo_analisis(s, clave):
    s = s.dropna()
    if s.empty:
        return s
    a, b = int(s.index.year.min()), int(s.index.year.max())
    r = st.slider('Periodo de análisis (años)', a, b, (a,b), key=clave) if a < b else (a,b)
    return s[(s.index.year >= r[0]) & (s.index.year <= r[1])]


def mostrar_tendencias_satelitales():
    from .chingaza_datos import leer_nasa, anual_desde_serie, NASA_COLUMNAS
    from .precipitacion_satelital_datos import cargar
    from .tendencias import mann_kendall, pendiente_sen, mann_kendall_hamed_rao
    st.caption('NASA POWER AG, CHIRPS v3 Final e IMERG Final V07B · estimaciones puntuales de grilla, no promedios de cuenca.')
    sat, avisos = cargar('chingaza')
    opciones = {}
    for col in sat:
        opciones[f'{col} · Precipitación'] = (sat[col].dropna(), 'sum', 'mm/año')
    try:
        nasa = leer_nasa()
        for col, nombre in NASA_COLUMNAS.items():
            if col == 'precipitacion_mm_mes' or nasa.empty:
                continue
            s = _serie_mensual_valida(nasa.rename(columns={col:'valor'}))
            unidad = nombre.rsplit('(',1)[-1].rstrip(')')
            opciones[f'NASA POWER · {nombre}'] = (s.dropna(), 'mean', unidad)
    except (OSError, ValueError, KeyError) as exc:
        st.warning(f'No se pudo leer NASA POWER mensual: {exc}')
    opciones = {k:v for k,v in opciones.items() if not v[0].empty}
    if avisos:
        with st.expander('Disponibilidad de fuentes'):
            for fuente, aviso in avisos.items(): st.caption(f'{fuente}: {aviso}')
    if not opciones:
        st.info('No hay series satelitales mensuales disponibles.'); return
    nombre = st.selectbox('Fuente y variable', list(opciones), key='ch_tend_sat_var')
    s, modo, unidad = opciones[nombre]
    s = _intervalo_analisis(s, 'ch_tend_sat_periodo_'+nombre)
    anual = anual_desde_serie(s, modo)
    if anual.empty:
        st.info('No hay años con doce meses válidos en el periodo.'); return
    st.line_chart(anual.set_index('anio').valor.reindex(range(int(anual.anio.min()),int(anual.anio.max())+1)), y_label=unidad)
    st.caption('Solo años con doce meses válidos. Precipitación: suma anual; otras variables: media ponderada por días del mes. Las máximas y mínimas NASA corresponden a medias de extremos diarios, no extremos absolutos anuales.')
    if len(anual) >= 10:
        x,y = anual.anio.to_numpy(),anual.valor.to_numpy()
        mostrar_resultados_tendencia(mann_kendall(y), pendiente_sen(x,y), mann_kendall_hamed_rao(x,y),x,unidad)
    else:
        st.info('Se requieren al menos 10 años completos para evaluar tendencias.')
    st.download_button('Descargar serie anual analizada',anual.assign(fuente_variable=nombre,unidad=unidad).to_csv(index=False).encode('utf-8-sig'),'chingaza_tendencia_satelital_anual.csv','text/csv',key='ch_tend_sat_desc')


def _snht_mensual(s, referencia=None):
    import numpy as np
    from scripts.a1._siams_a1_base import snht_test
    s = s.dropna().sort_index()
    if referencia is not None:
        p = pd.concat([s.rename('obs'),referencia.rename('ref')],axis=1).dropna()
        p = p[(p.obs >= 0) & (p.ref >= 0)]
        s = np.log((p.obs + 1)/(p.ref + 1))
    md = {k.strftime('%Y-%m'):float(v) for k,v in s.items() if np.isfinite(v)}
    return snht_test(md,kind='Relativo log[(P+1)/(Pref+1)]' if referencia is not None else 'Absoluto',repeat=999)


def mostrar_homogeneidad_chingaza():
    from .chingaza_datos import leer_eaab, BASE
    from .chingaza_ideam import cargar
    st.subheader('Homogeneidad de series observadas · SNHT')
    st.caption('Tamizaje exploratorio de cambios estadísticos. Se reutiliza el método SIAMS A1: anomalías estacionales mensuales y 999 permutaciones de bloques anuales. No corrige ni certifica automáticamente una serie.')
    fuente = st.radio('Fuente observada',['EAAB','IDEAM'],horizontal=True,key='ch_snht_fuente')
    try:
        if fuente == 'EAAB':
            d=leer_eaab(); est=pd.read_csv(BASE/'eaab_estaciones.csv',dtype={'estacion':str})
            nota='EAAB E.S.P. · Sistema de Información Hidrológica, reporte de febrero de 2024.'
        else:
            est,_,d=cargar(); nota='IDEAM · Solicitud 20249050031264 (2024).'
    except (OSError, ValueError, KeyError) as exc:
        st.warning(f'No se pudo cargar la fuente: {exc}'); return
    st.caption(nota+' Solo meses completos; sin imputación.')
    variable=st.selectbox('Variable',list(d.variable.unique()),key='ch_snht_var_'+fuente)
    d=d[d.variable.eq(variable)].copy()
    if 'etiqueta' in d and d.etiqueta.nunique()>1:
        etiqueta=st.selectbox('Código de variable',list(d.etiqueta.unique()),key='ch_snht_etiqueta')
        d=d[d.etiqueta.eq(etiqueta)]
    nombres=est.drop_duplicates('estacion').set_index('estacion').nombre.to_dict()
    codigos=list(d.loc[d.valor.notna(),'estacion'].unique())
    if not codigos:
        st.info('No hay estaciones con meses válidos.');return
    etiqueta=lambda c:f'{nombres.get(c,c)} · {c}'
    cod=st.selectbox('Estación objetivo',codigos,format_func=etiqueta,key='ch_snht_est_'+fuente+variable)
    s=_serie_mensual_valida(d[d.estacion.eq(cod)])
    s=_intervalo_analisis(s,'ch_snht_periodo_'+fuente+variable+cod)
    ref=None
    if variable=='Precipitación' and len(codigos)>1:
        otras=[c for c in codigos if c!=cod]
        modo=st.radio('Tipo de contraste',['SNHT absoluto','SNHT relativo entre estaciones'],key='ch_snht_modo',horizontal=True)
        if modo.startswith('SNHT relativo'):
            rc=st.selectbox('Estación de referencia',otras,format_func=etiqueta,key='ch_snht_ref_'+fuente+cod)
            ref=_serie_mensual_valida(d[d.estacion.eq(rc)]).reindex(s.index)
            st.caption('Contraste log[(P+1)/(P_ref+1)], en meses comunes. La referencia se elige manualmente; debe verificarse su cercanía, homogeneidad y representatividad.')
    if s.empty:
        st.info('No hay meses válidos en este periodo.');return
    res=_snht_mensual(s,ref)
    if res.get('estado')!='calculado':
        st.info(f"No evaluable: {res.get('n',0)} meses utilizables. Se requieren al menos 48 anomalías válidas, cinco años representados y suficientes observaciones a ambos lados del corte.");return
    a,b,c=st.columns(3); a.metric('Meses evaluados',res['n']); b.metric('T máximo SNHT',_fmt(res['T_SNHT'])); c.metric('Valor p por bloques',_fmt(res['p_bloques']))
    st.markdown(f"**Posible punto de cambio:** después de {res['corte']} (último mes observado del primer segmento).")
    st.caption(f"Periodo evaluado: {res['desde']} a {res['hasta']}. Los huecos no se rellenaron.")
    if res['alerta']: st.warning('Se detecta una discontinuidad potencial (p < 0,05). Revisar metadatos, estaciones vecinas y posibles causas climáticas.')
    else: st.info('No se detecta evidencia suficiente de cambio con este contraste al nivel del 5 %. Esto no certifica homogeneidad.')
    import plotly.graph_objects as go
    for campo,titulo,ylabel in [('anomalias','Anomalías mensuales estandarizadas','Anomalía (adimensional)'),('perfil','Perfil del estadístico SNHT','T SNHT')]:
        f=pd.DataFrame(res[campo],columns=['mes','valor']); f['fecha']=pd.to_datetime(f.mes,format='%Y-%m')
        fig=go.Figure(go.Scatter(x=f.fecha,y=f.valor,mode='lines',connectgaps=False)); fig.add_vline(x=pd.Timestamp(res['corte']+'-01').timestamp()*1000,line_dash='dash',line_color='#C87425'); fig.update_layout(title=titulo,yaxis_title=ylabel,height=340); st.plotly_chart(fig,width='stretch')
    st.caption('La prueba supone años intercambiables en las permutaciones. El punto de cambio no implica por sí mismo un cambio instrumental ni debe usarse para corregir los registros automáticamente.')
