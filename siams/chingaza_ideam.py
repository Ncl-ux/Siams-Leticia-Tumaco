"""IDEAM Chingaza: únicamente productos mensuales e inventario de estaciones."""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from .chingaza_datos import BASE, anual_completo

FUENTE='IDEAM · Solicitud 20249050031264 (2024), CNE_IDEAM.xls y archivos hidrometeorológicos entregados al proyecto Chingaza.'

def cargar(base=BASE):
    base=Path(base)
    est=pd.read_csv(base/'ideam_estaciones.csv',dtype={'estacion':str})
    inv=pd.read_csv(base/'ideam_inventario.csv',dtype={'estacion':str})
    d=pd.read_csv(base/'ideam_mensual.csv',dtype={'estacion':str},parse_dates=['fecha'])
    if d.fecha.isna().any() or not d.fecha.dt.day.eq(1).all() or d.duplicated(['estacion','etiqueta','fecha']).any():raise ValueError('Claves mensuales IDEAM inválidas')
    if not d.dias_mes.eq(d.fecha.dt.days_in_month).all() or not d.loc[d.valor.notna(),'dias_validos'].eq(d.loc[d.valor.notna(),'dias_mes']).all():raise ValueError('Completitud mensual IDEAM inválida')
    if not set(d.estacion)<=set(est.estacion):raise ValueError('Estación sin metadatos')
    return est,inv,d

def mostrar_inventario():
    est,inv,d=cargar(); st.caption(FUENTE)
    st.caption('Selección espacial: polígono de zona de influencia del proyecto; coordenadas según el catálogo de la entrega, no verificadas en campo.')
    st.dataframe(est,hide_index=True,width='stretch');st.dataframe(inv,hide_index=True,width='stretch')
    st.download_button('Descargar catálogo seleccionado IDEAM',est.to_csv(index=False).encode('utf-8-sig'),'ideam_chingaza_estaciones.csv','text/csv',key='chingaza_ideam_inventario_descarga')

def agregar_mapa(fig):
    est,_,_=cargar()
    for disponible,g in est.groupby('series_en_entrega'):
        fig.add_trace(go.Scattermap(lat=g.latitud,lon=g.longitud,mode='markers',marker=dict(size=8 if disponible else 5,color='#245da8' if disponible else '#929292'),name='IDEAM · con series' if disponible else 'IDEAM · sin series en entrega',text=g.nombre,hovertemplate='%{text}<extra></extra>'))

def mostrar_ideam():
    est,inv,d=cargar(); st.caption(FUENTE)
    st.caption('Series mensuales preliminares: solo meses completos. Sin imputación. Temperatura seca/húmeda según etiqueta de la entrega; humedad relativa: promedio de tres horarios fijos (07, 13 y 19 h). Se excluye evaporación automática hasta verificar la interpretación de las series.')
    var=st.selectbox('Variable IDEAM',list(d.variable.unique()),key='chingaza_ideam_variable')
    t=d[d.variable.eq(var)]; codigos=t.estacion.unique().tolist(); nombres=est.set_index('estacion').nombre.to_dict()
    cod=st.selectbox('Estación IDEAM',codigos,format_func=lambda x:f'{nombres[x]} · {x}',key='chingaza_ideam_estacion')
    s=t[t.estacion.eq(cod)].sort_values('fecha'); a,b=int(s.fecha.dt.year.min()),int(s.fecha.dt.year.max()); r=st.slider('Periodo IDEAM (años)',a,b,(a,b),key=f'chingaza_ideam_periodo_{cod}_{s.etiqueta.iloc[0]}') if a<b else (a,b)
    s=s[s.fecha.dt.year.between(*r)]; n=s.valor.count(); c1,c2,c3=st.columns(3);c1.metric('Meses válidos',int(n));c2.metric('Meses calendario',len(s));c3.metric('Completitud',f'{100*n/len(s):.1f}%')
    st.caption(f'Ubicación del catálogo: {est.set_index("estacion").loc[cod,"zona"]}. No representa por sí sola la precipitación media de una cuenca.')
    if n:
        fig=go.Figure(go.Scatter(x=s.fecha,y=s.valor,mode='lines+markers' if n<12 else 'lines',connectgaps=False));fig.update_layout(yaxis_title=s.unidad.iloc[0]);st.plotly_chart(fig,width='stretch')
        reg=s.groupby(s.fecha.dt.month).valor.agg(['mean','count']).reindex(range(1,13));st.subheader('Climatología mensual del periodo seleccionado');st.bar_chart(reg['mean'],y_label=s.unidad.iloc[0]);st.dataframe(reg.rename(columns={'mean':'Promedio','count':'Meses válidos'}),width='stretch')
        anual=anual_completo(s,'sum' if s.etiqueta.iloc[0] in ('PTPM_CON','EVTE_CON') else 'mean')
        with st.expander('Tendencias anuales · Mann–Kendall y Sen'):
            if len(anual)>=10:
                from .tendencias import mann_kendall, pendiente_sen, mann_kendall_hamed_rao
                from .chingaza_tendencias_ui import mostrar_resultados_tendencia
                st.line_chart(anual.set_index('anio').valor)
                mk=mann_kendall(anual.valor.to_numpy())
                sen=pendiente_sen(anual.anio.to_numpy(),anual.valor.to_numpy())
                hr=mann_kendall_hamed_rao(anual.anio.to_numpy(),anual.valor.to_numpy())
                unidad_anual='mm/año' if s.etiqueta.iloc[0] in ('PTPM_CON','EVTE_CON') else s.unidad.iloc[0]
                mostrar_resultados_tendencia(mk, sen, hr, anual.anio, unidad_anual)
                st.caption('Exploratorio; homogeneidad de serie pendiente de evaluar.')
            else:st.info('Menos de 10 años completos; no se calcula tendencia.')
    else:st.info('No hay meses completos para esta selección.')
    st.download_button('Descargar serie mensual IDEAM',s.to_csv(index=False,date_format='%Y-%m-%d').encode('utf-8-sig'),f'ideam_{cod}_{s.etiqueta.iloc[0]}_mensual.csv','text/csv',key='chingaza_ideam_descarga')
    if var=='Precipitación' and n:
        with st.expander('Comparación mensual con productos satelitales'):
            from .precipitacion_satelital_datos import cargar as cargar_sat, pares
            sat,avisos=cargar_sat('chingaza'); st.caption('Comparación exploratoria estación–grilla en puntos diferentes; no equivale a validación espacial ni a promedio de cuenca.')
            if sat.empty:st.info('Productos satelitales no disponibles.')
            else:
                p=s.set_index('fecha').valor.rename('IDEAM'); tabla=pd.concat([p,sat],axis=1).loc[s.fecha.min():s.fecha.max()];st.line_chart(tabla);st.dataframe(pares(tabla,'IDEAM'),hide_index=True,width='stretch')
