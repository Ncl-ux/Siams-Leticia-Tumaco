"""Interfaces de contraste y disponibilidad. Solo se llaman para Bogotá."""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from .catalogo import MESES
from .ideam_bogota import NOMBRES
from .ideam_bogota_datos import cargar_mensual
from .ideam_bogota_clima_datos import NASA, VARIABLES, pares_mensuales, regimen_pareado, anuales_ideam, paquetes_ideam


def mostrar_contraste_clima_bogota():
    st.subheader('Contraste de observaciones IDEAM y NASA POWER')
    st.caption('Series independientes. Se comparan únicamente meses completos con datos en ambas fuentes; no se rellenan vacíos ni se unen estaciones.')
    try:
        m = cargar_mensual()
        diario = pd.read_csv(NASA)
        a, b = st.columns([1, 1.5])
        with a:
            variable = st.selectbox('Variable', [v for v in VARIABLES if v in set(m.Variable)], key='bog_clima_ideam_variable')
        codigos = sorted(m.loc[m.Variable.eq(variable), 'CodigoEstacion'].unique())
        with b:
            codigo = st.selectbox('Estación IDEAM', codigos, format_func=lambda c: f'{NOMBRES.get(c,c)} · {c}', key=f'bog_clima_ideam_estacion_{variable}')
        p = pares_mensuales(m, diario, codigo, variable)
    except (OSError, ValueError, KeyError) as e:
        st.warning(f'No se pudo cargar el contraste IDEAM–NASA: {e}')
        return
    if p.empty:
        st.info('No hay meses completos comunes. Consulta el histórico IDEAM en su apartado independiente.')
        return
    inicio, fin = int(p.MesFecha.dt.year.min()), int(p.MesFecha.dt.year.max())
    if inicio < fin:
        desde, hasta = st.slider('Intervalo de comparación', inicio, fin, (inicio, fin), key=f'bog_clima_ideam_periodo_{codigo}_{variable}')
        p = p[p.MesFecha.dt.year.between(desde, hasta)].copy()
    if p.empty:
        st.info('Sin pares mensuales en el intervalo seleccionado.')
        return
    unidad = VARIABLES[variable][1]
    diff = p['NASA POWER'] - p.IDEAM
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Meses comunes', len(p))
    c2.metric('Sesgo medio NASA − IDEAM', f'{diff.mean():+.2f} {unidad}')
    c3.metric('MAE', f'{diff.abs().mean():.2f} {unidad}')
    c4.metric('RMSE', f'{np.sqrt(diff.pow(2).mean()):.2f} {unidad}')
    st.caption(f'Fechas comparadas: {p.MesFecha.min():%Y-%m} a {p.MesFecha.max():%Y-%m}. IDEAM: {int(p.Definitivos.sum())}/{int(p.Dias.sum())} días definitivos; {int(p.Inferidos.sum())} identificaciones de parámetro inferidas. NASA POWER representa una celda de reanálisis y no una medición puntual; las ventanas de observación pueden diferir.')
    if p.Inferidos.sum():
        st.warning('Parte de la identificación de parámetros IDEAM fue reconstruida desde bloques XLSX. Comparación exploratoria, pendiente de verificación documental.')
    if len(p) < 120:
        st.info('Cobertura limitada: este contraste no constituye una validación climática de largo plazo.')
    r = regimen_pareado(p)
    fig = go.Figure()
    for col, nombre, color in [('IDEAM','IDEAM','#0b5147'), ('NASA','NASA POWER','#3789bf')]:
        fig.add_trace(go.Scatter(x=MESES,y=r[col],name=nombre,mode='lines+markers',line=dict(color=color),connectgaps=False,customdata=r.Pares,hovertemplate='%{x}: %{y:.2f} · %{customdata} pares<extra>'+nombre+'</extra>'))
    fig.update_layout(title='Promedios mensuales sobre fechas comunes',yaxis_title=unidad,legend=dict(orientation='h'))
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Cada mes del calendario puede tener un número de años diferente. No sumar estas medias como una normal anual oficial.')
    if variable == 'Precipitación':
        st.caption('Precipitación: acumulados mensuales observados completos. No se comparan acumulados parciales con totales completos.')
    with st.expander('Serie temporal y tabla de pares'):
        completo = p.set_index('MesFecha').reindex(pd.date_range(p.MesFecha.min(),p.MesFecha.max(),freq='MS'))
        fig2 = go.Figure()
        for col, color in [('IDEAM','#0b5147'),('NASA POWER','#3789bf')]:
            fig2.add_trace(go.Scatter(x=completo.index,y=completo[col],name=col,mode='lines+markers',connectgaps=False,line=dict(color=color)))
        fig2.update_layout(yaxis_title=unidad)
        st.plotly_chart(fig2,use_container_width=True)
        st.dataframe(p,hide_index=True,use_container_width=True)
        st.download_button('Descargar meses comparados',p.to_csv(index=False).encode('utf-8-sig'),f'contraste_bogota_{codigo}.csv','text/csv',key='bog_clima_pares_csv')


def agregar_tendencias_ideam_bogota(paquetes):
    """Añade las fuentes a la interfaz existente sin reemplazar paquetes NASA."""
    try:
        m = cargar_mensual()
        a = anuales_ideam(m)
        inventario = m[['CodigoEstacion','Variable']].drop_duplicates()
        conteos = a.groupby(['CodigoEstacion','Variable']).size().rename('Años completos').reset_index()
        inventario = inventario.merge(conteos,how='left',on=['CodigoEstacion','Variable'])
        inventario['Años completos'] = inventario['Años completos'].fillna(0).astype(int)
        inventario['Estación'] = inventario.CodigoEstacion.map(NOMBRES).fillna(inventario.CodigoEstacion)
        inventario['Uso'] = np.select([inventario['Años completos'].ge(25),inventario['Años completos'].ge(5)],['Evaluable; revisar A1','Exploratorio (<25 años)'],default='Insuficiente para MK')
        with st.expander('IDEAM Bogotá · cobertura y criterios de tendencias',expanded=True):
            st.caption('Solo años calendario completos (12 meses completos). No se combinan estaciones. El mínimo computacional de MK existente es 5 años; 25 años es el objetivo de selección científica. Hamed–Rao no se calcula con años discontinuos o menos de 10 años. Consultar A1 antes de interpretar tendencias.')
            st.dataframe(inventario[['Estación','CodigoEstacion','Variable','Años completos','Uso']],use_container_width=True,hide_index=True)
            st.caption('Los resultados IDEAM son exploratorios; las observaciones preliminares no equivalen a validación oficial. NASA POWER conserva su serie y sus criterios existentes.')
        nuevos = paquetes_ideam(m,NOMBRES)
        # Do not overwrite a source even if another package uses the same key.
        return {**paquetes, **{k:v for k,v in nuevos.items() if k not in paquetes}}
    except (OSError, ValueError, KeyError) as e:
        st.warning(f'No se pudieron incorporar tendencias IDEAM Bogotá: {e}')
        return paquetes
